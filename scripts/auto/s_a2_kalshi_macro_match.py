"""Stage A2 — Match every Kalshi series to authoritative macro events.

Rule-based: regex with word boundaries on title + sub_title + (optional)
rules_primary. Aliases come from docs/macro_matching_rules.md.

Output: outputs/auto/macro_kalshi.csv
  series_ticker, title, category, matched_events (comma-sep), n_matches
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "auto"
OUT.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────
# Alias dictionary — VERBATIM from docs/macro_matching_rules.md.
# Adding/removing any entry requires re-running this whole stage.
# ─────────────────────────────────────────────────────────────────
ALIASES: dict[str, list[str]] = {
    "nonfarm payrolls": [
        r"\bnonfarm payroll\b", r"\bnfp\b", r"\bpayroll report\b",
        r"\bjobs report\b", r"\bpayrolls?\b", r"\bemployment situation\b",
    ],
    "unemployment rate": [
        r"\bunemployment rate\b", r"\bu-?3\b", r"\bjobless rate\b",
    ],
    "initial jobless": [
        r"\binitial jobless\b", r"\binitial claims\b", r"\bweekly jobless\b",
    ],
    "continuing jobless": [
        r"\bcontinuing jobless\b", r"\bcontinued claims\b",
    ],
    "jolts": [
        r"\bjolts\b", r"\bjob openings\b", r"\blabor turnover\b",
    ],
    "adp employment": [
        r"\badp\b.{0,20}employ", r"\badp national employment\b",
    ],
    "nonfarm productivity": [
        r"\bnonfarm productivity\b", r"\bproductivity and costs\b",
    ],
    "participation rate": [
        r"\bparticipation rate\b", r"\blabor force participation\b",
    ],
    "average hourly earnings": [
        r"\baverage hourly earnings\b", r"\bahe\b", r"\bwage growth\b",
    ],
    "cpi": [
        r"\bcpi\b", r"\bconsumer price index\b", r"\binflation rate\b",
    ],
    "core cpi": [
        r"\bcore cpi\b", r"\bcpi ex food and energy\b", r"\bcore inflation\b",
    ],
    "ppi": [
        r"\bppi\b", r"\bproducer price index\b", r"\bproducer inflation\b",
    ],
    "pce": [
        r"\bpce\b", r"\bpersonal consumption expenditure\b",
        r"\bpce price index\b",
    ],
    "core pce": [
        r"\bcore pce\b", r"\bpce ex food and energy\b",
    ],
    "retail sales": [
        r"\bretail sales\b", r"\badvance retail sales\b",
    ],
    "industrial production": [
        r"\bindustrial production\b", r"\bindpro\b",
    ],
    "durable goods": [
        r"\bdurable goods\b", r"\bdurable goods orders\b",
    ],
    "factory orders": [
        r"\bfactory orders\b", r"\bnew manufacturers' orders\b",
    ],
    "construction spending": [
        r"\bconstruction spending\b",
        r"\bvalue of construction put in place\b",
    ],
    "housing starts": [
        r"\bhousing starts\b", r"\bnew residential construction\b",
    ],
    "building permits": [
        r"\bbuilding permits\b",
    ],
    "new home sales": [
        r"\bnew home sales\b", r"\bnew residential sales\b",
    ],
    "existing home sales": [
        r"\bexisting home sales\b",
    ],
    "case-shiller": [
        r"\bcase[- ]shiller\b", r"\bs&p corelogic\b",
    ],
    "consumer sentiment": [
        r"\bconsumer sentiment\b", r"\bmichigan sentiment\b", r"\bumich\b",
    ],
    "michigan consumer": [
        r"\bmichigan sentiment\b", r"\bmichigan consumer\b", r"\bumich\b",
    ],
    "consumer confidence": [
        r"\bconsumer confidence\b", r"\bcci\b", r"\bconference board confidence\b",
    ],
    "import price": [
        r"\bimport price\b",
    ],
    "personal income": [
        r"\bpersonal income\b",
    ],
    "personal spending": [
        r"\bpersonal spending\b", r"\bpersonal expenditure\b",
    ],
    "trade balance": [
        r"\btrade balance\b", r"\binternational trade in goods\b",
    ],
    "ism manufacturing": [
        r"\bism manufacturing\b", r"\bism mfg\b", r"\bpmi manufacturing\b",
    ],
    "ism non-manufacturing": [
        r"\bism non-?manufacturing\b",
    ],
    "ism services": [
        r"\bism services\b",
    ],
    "manufacturing pmi": [
        r"\bmanufacturing pmi\b", r"\bs&p global manufacturing pmi\b",
    ],
    "services pmi": [
        r"\bservices pmi\b", r"\bs&p global services pmi\b",
    ],
    "gdp": [
        r"\bgdp\b", r"\bgross domestic product\b",
    ],
    "fomc": [
        r"\bfomc\b", r"\bfederal open market committee\b",
    ],
    "fed interest rate": [
        r"\bfed interest rate\b", r"\bfederal funds rate\b",
        r"\bfed funds rate\b", r"\bfed rate decision\b",
    ],
    "fed chair": [
        r"\bfed chair\b", r"\bfederal reserve chair\b",
    ],
}

# Also match raw FRED series IDs and indicator names appearing in Kalshi text.
FRED_NAME_PATTERNS = {
    # FRED catalog (subset matching active macro releases above)
    "FRED:PAYEMS": [r"\bpayems\b"],
    "FRED:UNRATE": [r"\bunrate\b"],
    "FRED:CPIAUCSL": [r"\bcpiaucsl\b"],
    "FRED:PCEPI": [r"\bpcepi\b"],
    "FRED:GDPC1": [r"\bgdpc1\b"],
    "FRED:RSAFS": [r"\brsafs\b"],
    "FRED:HOUST": [r"\bhoust\b"],
    "FRED:UMCSENT": [r"\bumcsent\b"],
    "FRED:PPIACO": [r"\bppiaco\b"],
    "FRED:DFF": [r"\bdff\b"],
    "FRED:FEDFUNDS": [r"\bfedfunds\b"],
}


def compile_rules(rules: dict[str, list[str]]) -> dict[str, list[re.Pattern]]:
    return {k: [re.compile(p, re.IGNORECASE) for p in v] for k, v in rules.items()}


def match_text(text: str, compiled: dict[str, list[re.Pattern]]) -> list[str]:
    matched: list[str] = []
    for event_name, patterns in compiled.items():
        if any(p.search(text) for p in patterns):
            matched.append(event_name)
    return matched


def main() -> None:
    kalshi = pd.read_csv(ROOT / "outputs" / "kalshi_series_all.csv")
    kalshi["title"] = kalshi["title"].fillna("")
    # Some series have a sub-title-like field — concatenate what we have
    text_col = kalshi["title"].astype(str)

    compiled_alias = compile_rules(ALIASES)
    compiled_fred = compile_rules(FRED_NAME_PATTERNS)

    rows = []
    for _, r in kalshi.iterrows():
        text = str(r.get("title", "")).strip()
        matches = match_text(text, compiled_alias) + match_text(text, compiled_fred)
        if matches:
            rows.append({
                "series_ticker": r.get("series_ticker"),
                "title": r.get("title"),
                "category": r.get("category"),
                "matched_events": ",".join(sorted(set(matches))),
                "n_matches": len(set(matches)),
            })

    out_df = pd.DataFrame(rows)
    out_csv = OUT / "macro_kalshi.csv"
    out_df.to_csv(out_csv, index=False)
    print(f"wrote {out_csv} — {len(out_df)} macro Kalshi series")
    print(f"  out of {len(kalshi)} total kalshi series ({100*len(out_df)/len(kalshi):.1f}%)")

    # Category breakdown
    print("\n매크로 시리즈 카테고리 분포:")
    print(out_df["category"].value_counts().head(10).to_string())

    # Top 10 most common event matches
    print("\n매칭 빈도 (상위 10 events):")
    all_matches: list[str] = []
    for s in out_df["matched_events"]:
        all_matches.extend(s.split(","))
    print(pd.Series(all_matches).value_counts().head(10).to_string())

    # ─ Negative control verification (must not match)
    print("\n── Negative control check ─────────────")
    negs = [
        "Will the Beatles have 3.5B streams in 2026?",
        "MrBeast Million Dollar Puzzle completion",
        "Will Elon Musk visit Mars in his lifetime?",
        "Oscar for Best Picture",
        "Will Joyce Beatty be the Democratic nominee for OH-03?",
    ]
    for n in negs:
        m = match_text(n.lower(), compiled_alias) + match_text(n.lower(), compiled_fred)
        sign = "❌ FAIL — false positive" if m else "✅"
        print(f"  {sign} {n[:60]:62s} → {m}")


if __name__ == "__main__":
    main()
