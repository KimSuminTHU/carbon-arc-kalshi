"""Stage E — Price every CA dataset that appears in verification_pairs_macro.csv.

For each unique CA dataset (35 of them):
  1. Pick a "core" topic + its primary insight
  2. Find the US national entity for that insight
  3. Call check_framework_price at three standardized windows (1y / 3y / 5y, monthly)

Then attach prices to all 754 pair rows.

Outputs:
  outputs/auto/framework_prices.csv   ← per-dataset prices
  outputs/auto/pair_prices.csv        ← per-pair (754 rows) with CA cost
  docs/framework_prices.md            ← human-readable summary + 754-pair table

Note: check_framework_price does NOT charge the promo balance. buy_frameworks does.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "auto"
DOCS = ROOT / "docs"

API_KEY = os.environ.get("CARBONARC_API_KEY")
if not API_KEY:
    print("ERROR: CARBONARC_API_KEY not set", file=sys.stderr)
    sys.exit(1)

HEADERS = {"Authorization": f"Bearer {API_KEY}"}
ORDER_URL = "https://api.carbonarc.co/v2/framework/order"


def check_price(framework: dict) -> dict:
    """Return {valid, price, used_rows_count, table_max_date, message} dict."""
    try:
        r = requests.post(ORDER_URL, json={"framework": framework},
                          headers=HEADERS, timeout=20)
        if r.status_code != 200:
            return {"valid": False, "price": None,
                    "message": f"HTTP {r.status_code}"}
        b = r.json()
        return {
            "valid": b.get("valid"),
            "price": b.get("price"),
            "used_rows_count": b.get("used_rows_count"),
            "table_max_date": b.get("table_max_date"),
            "message": b.get("message", "")[:120],
        }
    except Exception as e:
        return {"valid": False, "price": None,
                "message": f"{type(e).__name__}: {str(e)[:100]}"}


def get_dataset_meta(client, ds_id: str) -> tuple[int | None, str | None, int | None]:
    """Return (insight_id, insight_label, us_carc_id) for the primary topic of ds_id."""
    try:
        dd = client.data.get_data_dictionary(ds_id)
    except Exception as e:
        print(f"  {ds_id}: dictionary error: {e}")
        return None, None, None

    # Prefer a topic with "Core Panel" / "Prices" in label, else first valid topic
    topics = [t for t in dd if t.get("entity_topic_id")]
    if not topics:
        return None, None, None

    primary = next(
        (t for t in topics
         if any(kw in (t.get("label") or "").lower()
                for kw in ["core panel", "prices", "core ", "claims"])),
        topics[0],
    )

    try:
        ins_resp = client.ontology.get_insights_for_topic(primary["entity_topic_id"])
        insights = ins_resp.get("insights", []) if isinstance(ins_resp, dict) else []
    except Exception as e:
        print(f"  {ds_id}: insights error: {e}")
        return None, None, None

    if not insights:
        return None, None, None

    # Pick first "metric" insight (Worker Count, Card Spend, Price Value, ...)
    inf = insights[0]
    iid = inf.get("insight_id") or inf.get("carc_id")
    iname = inf.get("insight_label") or inf.get("insight_name")

    # Find US country entity
    try:
        ents = client.ontology.get_entities(
            insight_id=iid, search="United States", size=2
        ).get("entities", [])
    except Exception:
        ents = []
    us_carc = ents[0]["carc_id"] if ents else None
    us_rep = ents[0]["representation"] if ents else "country"
    return iid, iname, us_carc if us_carc else None


def build_fw(carc: int, rep: str, insight: int, years: int,
             aggregate: str = "mean") -> dict:
    return {
        "entities": [{"carc_id": carc, "representation": rep}],
        "insight": {"insight_id": insight},
        "filters": {
            "date_resolution": "month",
            "location_resolution": "us",
            "date_range": {
                "start_date": f"{2026 - years}-01-01",
                "end_date": "2026-04-30",
            },
        },
        "aggregate": aggregate,
    }


def main() -> None:
    from carbonarc import CarbonArcClient
    client = CarbonArcClient(token=API_KEY)

    pairs = pd.read_csv(OUT / "verification_pairs_macro.csv")
    unique_ca = pairs["ca_dataset_id"].unique()
    print(f"Pricing {len(unique_ca)} unique CA datasets "
          f"covering {len(pairs)} pairs...")

    rows: list[dict] = []
    t0 = time.time()
    for i, ds in enumerate(unique_ca):
        ca_name = pairs[pairs["ca_dataset_id"] == ds]["ca_name"].iloc[0]
        print(f"\n[{i+1}/{len(unique_ca)}] {ds} {ca_name}")
        iid, iname, us_carc = get_dataset_meta(client, ds)
        if not (iid and us_carc):
            print(f"  ⚠ no insight or US entity")
            rows.append({"ca_dataset_id": ds, "ca_name": ca_name,
                         "insight_id": iid, "insight_label": iname,
                         "us_carc_id": us_carc,
                         **{f"price_{y}y": None for y in [1, 3, 5]},
                         **{f"rows_{y}y": None for y in [1, 3, 5]},
                         "table_max_date": None, "note": "no insight/us entity"})
            continue
        print(f"  insight {iid} '{iname}', US carc_id={us_carc}")

        result_row = {"ca_dataset_id": ds, "ca_name": ca_name,
                      "insight_id": iid, "insight_label": iname,
                      "us_carc_id": us_carc,
                      "table_max_date": None, "note": ""}

        for years in [1, 3, 5]:
            for agg in ["mean", "sum"]:
                fw = build_fw(us_carc, "country", iid, years, agg)
                res = check_price(fw)
                if res.get("valid"):
                    break
            result_row[f"price_{years}y"] = res.get("price")
            result_row[f"rows_{years}y"] = res.get("used_rows_count")
            if res.get("table_max_date"):
                result_row["table_max_date"] = res["table_max_date"]
            if not res.get("valid") and not result_row["note"]:
                result_row["note"] = res.get("message", "")[:100]
            print(f"    {years}y: ${res.get('price','?')} "
                  f"({res.get('used_rows_count','?')} rows) — "
                  f"valid={res.get('valid')}")
        rows.append(result_row)

    prices = pd.DataFrame(rows)
    prices.to_csv(OUT / "framework_prices.csv", index=False)
    print(f"\nwrote {OUT / 'framework_prices.csv'}")
    print(f"elapsed {time.time()-t0:.1f}s")

    # Join prices to pairs
    pair_prices = pairs.merge(
        prices[["ca_dataset_id", "insight_id", "insight_label",
                "price_1y", "price_3y", "price_5y",
                "rows_1y", "rows_3y", "rows_5y",
                "table_max_date", "note"]],
        on="ca_dataset_id", how="left",
    )
    pair_prices.to_csv(OUT / "pair_prices.csv", index=False)
    print(f"wrote {OUT / 'pair_prices.csv'} ({len(pair_prices)} rows)")

    # Build markdown
    build_markdown(prices, pair_prices)


def build_markdown(prices: pd.DataFrame, pairs: pd.DataFrame) -> None:
    md: list[str] = [
        "# Framework Prices — 754 검증쌍 × CarbonArc cost",
        "",
        "> Stage E 산출물. `outputs/auto/verification_pairs_macro.csv` 의 754 페어가 "
        "쓰는 35개 CA 데이터셋에 대해 `check_framework_price` 호출 (promo 차감 없음).",
        "",
        "## 가격 모델 메모",
        "",
        "- CarbonArc 가격 = **framework 단위** (= 데이터셋 슬라이스 + entity + 기간 + aggregate).",
        "- 동일 dataset 의 day/week/month resolution 은 같은 row 수 → 같은 가격. resolution 으로 절약 불가.",
        "- 검증 가능한 최소 단위: monthly US national rollup, 1-5y 윈도우.",
        "- 모든 price 는 `check_framework_price` 호출 결과 (promo 사용 X).",
        "- Promo balance: **$50.00 (사용 0)**",
        "",
        "## 35 CA 데이터셋 가격표 (monthly US, 표준화 윈도우)",
        "",
        "| CA | Name | Insight | 1y | 3y | 5y | rows@3y | table updated | note |",
        "|---|---|---|---:|---:|---:|---:|---|---|",
    ]
    pair_counts = pairs.groupby("ca_dataset_id").size().to_dict()
    prices_sorted = prices.copy()
    prices_sorted["pairs"] = prices_sorted["ca_dataset_id"].map(pair_counts)
    prices_sorted = prices_sorted.sort_values("pairs", ascending=False)

    def fmt_price(v):
        if pd.isna(v) or v is None:
            return "—"
        if v == 0:
            return "$0.00 ⚠"
        return f"${v:.2f}"

    for _, r in prices_sorted.iterrows():
        md.append(f"| `{r['ca_dataset_id']}` | {r['ca_name']} | "
                  f"`{r['insight_id']}` {r['insight_label'] or '—'} | "
                  f"{fmt_price(r['price_1y'])} | {fmt_price(r['price_3y'])} | "
                  f"{fmt_price(r['price_5y'])} | "
                  f"{int(r['rows_3y']) if pd.notna(r['rows_3y']) else '—'} | "
                  f"{str(r['table_max_date'])[:10] if r['table_max_date'] else '—'} | "
                  f"{r['note'] or ''} |")

    # Summary: how many pairs fit at each budget
    md += [
        "",
        "## $50 promo 로 살 수 있는 페어 수",
        "",
        "각 행 = 한 데이터셋을 1번 사면 그 데이터셋이 들어있는 *모든* 페어 검증에 재사용 가능. "
        "여러 데이터셋을 사면 합산 비용.",
        "",
        "| 윈도우 | 단독 $50 이내 데이터셋 수 | 해당 페어 수 |",
        "|---|---:|---:|",
    ]
    for col in ["price_1y", "price_3y", "price_5y"]:
        within = prices[prices[col].fillna(99999) <= 50]
        n_ds = len(within)
        n_pairs = pairs[pairs["ca_dataset_id"].isin(within["ca_dataset_id"])].shape[0]
        years = col.split("_")[1]
        md.append(f"| monthly {years} | {n_ds} | {n_pairs} |")

    # All 754 pairs table — annotated
    md += [
        "",
        "## 전체 754 페어 (lead window 큰 순)",
        "",
        "| # | CA | CA name | Kalshi | Kalshi title | matched macro | lead | CA cost 3y | rows@3y |",
        "|---:|---|---|---|---|---|---:|---:|---:|",
    ]
    sorted_pairs = pairs.sort_values("lead_window_days", ascending=False).reset_index(drop=True)
    for i, r in sorted_pairs.iterrows():
        title = str(r["kalshi_title"])[:55]
        match = str(r["matched_events"])[:35]
        md.append(f"| {i+1} | `{r['ca_dataset_id']}` | {r['ca_name'][:35]} | "
                  f"`{r['kalshi_series_ticker']}` | {title} | {match} | "
                  f"{int(r['lead_window_days'])}d | {fmt_price(r['price_3y'])} | "
                  f"{int(r['rows_3y']) if pd.notna(r['rows_3y']) else '—'} |")

    out = DOCS / "framework_prices.md"
    out.write_text("\n".join(md))
    print(f"wrote {out} ({len(md)} lines)")


if __name__ == "__main__":
    main()
