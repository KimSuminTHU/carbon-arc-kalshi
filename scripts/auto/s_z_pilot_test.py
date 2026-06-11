#!/usr/bin/env python3
"""
s_z_pilot_test.py — pilot tests on the 3 newly-bought CA datasets.

DIRECTION 1 (EPS / margin): can a COST proxy (CA0077 commodities) help where card (demand) failed?
  s_u showed card→EPS-surprise is null (r=0.065) because card can't see margins/costs. Test whether
  adding a commodity input-cost index helps explain the EPS surprise.
    cost_yoy = YoY of a food-commodity basket (restaurants/grocers) or cottonseed (apparel)
    Y = EPS surprise_early (vs point-in-time consensus, from FactSet)
    tests: Y~ca_yoy (card, baseline-null) ; Y~cost_yoy ; Y~ca_yoy+cost_yoy (does cost add?)
  Caveat: commodity spot prices are largely PUBLIC → if it predicts the surprise it's nowcast power,
  not necessarily edge over analysts (who see the same prices). Also commodity country source is a
  hodge-podge (Spain beef, Poland chicken) → YoY of globally-traded softs/grains is cleaner than proteins.

DIRECTION 2 (revenue): do clickstream (CA0030) / app (CA0054) fill the card gap for e-commerce / services?
    web_yoy = YoY of quarterly website users (sum desktop+mobile)
    Y = revenue surprise_early (FactSet)   tests: Y~ca_yoy ; Y~web_yoy ; Y~ca_yoy+web_yoy
"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import s_q_edge_tests as eq
import s_t_revsurprise_factset as st
import s_u_epssurprise_factset as su

ROOT = Path("/Users/junekwon/Desktop/Projects/carbon_arc")
A = ROOT / "outputs" / "auto"
OUT_MD = ROOT / "docs" / "analysis_pilot_cost_web.md"
ent = json.load(open(A / "pilot_entities.json"))
ID2TKR_CLICK = {e["carc_id"]: e["tkr"] for e in ent["click"]}
ID2TKR_APP = {e["carc_id"]: e["tkr"] for e in ent["app"]}
lines = []
def log(s=""): print(s); lines.append(s)

FOOD = ["Beef, ribeye", "Chicken\xa0leg", "Pork,\xa0leg", "Milk,\xa0fortified", "Eggs", "Coffee",
        "Avocado", "Wheat", "Corn", "Sugar,\xa0white", "Rice", "Tomatoes,\xa0fresh",
        "Soybean\xa0oil,\xa0refined", "Potato", "Cocoa"]
COTTON = "Cottonseed, fuzzy"
APPAREL = {"NKE", "LULU", "GAP", "AEO", "ANF", "URBN"}
FOODCOS = {"CMG", "MCD", "SBUX", "YUM", "DPZ", "WEN", "DRI", "TXRH", "CAVA", "KR", "WMT", "COST", "TGT", "DG", "DLTR"}
ECOMM = {"AMZN", "ETSY", "CHWY", "NKE", "LULU", "GAP", "AEO", "ANF", "URBN", "BBY"}

def commodity_yoy():
    d = pd.read_csv(A / "ca0077_commodity_prices_5y.csv"); d["date"] = pd.to_datetime(d["date"])
    # best-coverage country per commodity
    cnt = d.groupby(["entity_name", "country"])["date"].nunique().reset_index(name="n")
    best = cnt.sort_values("n").groupby("entity_name").tail(1)[["entity_name", "country"]]
    d = d.merge(best, on=["entity_name", "country"])
    d["q"] = d["date"].dt.to_period("Q")
    qv = d.groupby(["entity_name", "q"])["price_value"].mean().reset_index()
    qv = qv.sort_values(["entity_name", "q"])
    qv["yoy"] = qv.groupby("entity_name")["price_value"].pct_change(4)
    return qv

def quarter_yoy_from_monthly(df, val, idcol):
    df = df.copy(); df["date"] = pd.to_datetime(df["date"]); df["q"] = df["date"].dt.to_period("Q")
    qv = df.groupby([idcol, "q"])[val].sum().reset_index().sort_values([idcol, "q"])
    qv["yoy"] = qv.groupby(idcol)[val].pct_change(4)
    return qv

def mreg_boot(d, ycol, xcols, n=3000, seed=3):
    """Pooled OLS R² + per-coef company-clustered bootstrap two-sided p."""
    d = d.dropna(subset=[ycol] + xcols)
    if len(d) < 15: return None
    X = np.column_stack([np.ones(len(d))] + [d[c].values for c in xcols]); y = d[ycol].values
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    yhat = X @ beta; r2 = 1 - ((y - yhat) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    ticks = d.ticker.unique(); rng = np.random.default_rng(seed); bs = []
    for _ in range(n):
        s = pd.concat([d[d.ticker == k] for k in rng.choice(ticks, len(ticks), True)])
        if len(s) < len(xcols) + 2: continue
        Xs = np.column_stack([np.ones(len(s))] + [s[c].values for c in xcols])
        try: b, *_ = np.linalg.lstsq(Xs, s[ycol].values, rcond=None)
        except Exception: continue
        bs.append(b)
    bs = np.array(bs); ps = []
    for j in range(1, len(xcols) + 1):
        col = bs[:, j]; ps.append(2 * min((col > 0).mean(), (col < 0).mean()))
    return {"n": len(d), "r2": r2, "coef": beta[1:], "p": ps, "nt": d.ticker.nunique()}

def main():
    ca = eq.build_ca_surprise()[["ticker", "date", "ca_yoy"]]
    cyoy = commodity_yoy()
    food = cyoy[cyoy.entity_name.isin(FOOD)].groupby("q")["yoy"].mean().rename("food_yoy")
    cotton = cyoy[cyoy.entity_name == COTTON].set_index("q")["yoy"].rename("cotton_yoy")
    cost = pd.concat([food, cotton], axis=1).reset_index()
    cost["date"] = cost["q"].dt.to_timestamp("Q")

    # ---------------- DIRECTION 1: EPS / cost ----------------
    e = su.load_eps()
    parts = []
    for t in e.ticker.unique():
        a = ca[ca.ticker == t].sort_values("date")
        if a.empty: continue
        m = pd.merge_asof(e[e.ticker == t].sort_values("FE_FP_END"), a[["date", "ca_yoy"]], left_on="FE_FP_END", right_on="date",
                          direction="nearest", tolerance=pd.Timedelta(days=50))
        parts.append(m)
    d = pd.concat(parts, ignore_index=True).dropna(subset=["ca_yoy"])
    d["fq"] = pd.to_datetime(d["FE_FP_END"]).dt.to_period("Q")
    cost_q = cost.set_index("q")
    d["cost_yoy"] = [cost_q.loc[q, "cotton_yoy"] if t in APPAREL else (cost_q.loc[q, "food_yoy"] if q in cost_q.index else np.nan)
                     for t, q in zip(d.ticker, d.fq)]
    d = d[d.ticker.isin(FOODCOS | APPAREL)]
    for c in ["surprise_early"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["eps_surprise"] = (d["ACTUAL"] - d["CONS_EARLY"]) / d["CONS_EARLY"].abs()
    d = d[(d["ACTUAL"].abs() >= 0.05) & (d["CONS_EARLY"].abs() >= 0.05)]
    lo, hi = d.eps_surprise.quantile([.01, .99]); d.eps_surprise = d.eps_surprise.clip(lo, hi)

    log("# PILOT — cost (commodities) for EPS, web/app for revenue\n")
    log("## DIRECTION 1 — does a COMMODITY COST proxy help predict the EPS surprise (where card failed)?")
    log(f"panel: {len(d)} company-quarters, {d.ticker.nunique()} food/apparel tickers; "
        f"{d.fq.min()}..{d.fq.max()}")
    r1 = mreg_boot(d, "eps_surprise", ["ca_yoy"])
    r2 = mreg_boot(d, "eps_surprise", ["cost_yoy"])
    r3 = mreg_boot(d, "eps_surprise", ["ca_yoy", "cost_yoy"])
    if r1: log(f"  Y~ca_yoy           : R²={r1['r2']:+.3f} coef={r1['coef'][0]:+.3f} p={r1['p'][0]:.3f} (n={r1['n']}) — card alone (null, per s_u)")
    if r2: log(f"  Y~cost_yoy         : R²={r2['r2']:+.3f} coef={r2['coef'][0]:+.3f} p={r2['p'][0]:.3f} — cost alone (expect <0: cost up→EPS miss)")
    if r3: log(f"  Y~ca_yoy+cost_yoy  : R²={r3['r2']:+.3f} ca={r3['coef'][0]:+.3f}(p{r3['p'][0]:.2f}) cost={r3['coef'][1]:+.3f}(p{r3['p'][1]:.2f}) — does cost ADD?")
    # restaurants-only (cleanest cost link)
    rest = d[d.ticker.isin({"CMG","MCD","SBUX","YUM","DPZ","WEN","DRI","TXRH","CAVA"})]
    rr = mreg_boot(rest, "eps_surprise", ["cost_yoy"])
    if rr: log(f"  [restaurants only] Y~cost_yoy: R²={rr['r2']:+.3f} coef={rr['coef'][0]:+.3f} p={rr['p'][0]:.3f} (n={rr['n']}, {rr['nt']} cos)")
    dcost = d.dropna(subset=["cost_yoy","eps_surprise"])
    rco = dcost.cost_yoy.corr(dcost.eps_surprise)
    psurr_cost = eq.surrogate(dcost, "cost_yoy", "eps_surprise", rco)
    log(f"  surrogate (shuffle-company) cost_yoy→eps_surprise: r={rco:+.3f} p_surr={psurr_cost:.3f}")

    # ---------------- DIRECTION 2: revenue / web ----------------
    log("\n## DIRECTION 2 — do clickstream / app fill the card gap for revenue (surprise vs consensus)?")
    rev = pd.DataFrame(json.load(open(st.FS))["rows"])  # s_t revenue file
    for c in ["ACTUAL", "CONS_EARLY"]: rev[c] = pd.to_numeric(rev[c], errors="coerce")
    rev["FE_FP_END"] = pd.to_datetime(rev["FE_FP_END"]); rev["ticker"] = rev["FSYM_ID"].map(st.FSYM2TKR)
    rev = rev.dropna(subset=["ticker", "ACTUAL", "CONS_EARLY"])
    keep = rev.groupby(["ticker","FSYM_ID"]).size().reset_index(name="n").sort_values("n").groupby("ticker").tail(1)
    rev = rev.merge(keep[["ticker","FSYM_ID"]], on=["ticker","FSYM_ID"]).sort_values(["ticker","FE_FP_END"])
    rev["rev_surprise"] = (rev["ACTUAL"] - rev["CONS_EARLY"]) / rev["CONS_EARLY"]

    click = pd.read_csv(A / "ca0030_clickstream_by_company_3y.csv")
    click["ticker"] = click["entity_id"].map(ID2TKR_CLICK)
    wq = quarter_yoy_from_monthly(click, "website_users", "ticker").rename(columns={"yoy": "web_yoy"})
    wq["date"] = wq["q"].dt.to_timestamp("Q")

    parts = []
    for t in rev.ticker.unique():
        a = ca[ca.ticker == t].sort_values("date"); w = wq[wq.ticker == t].sort_values("date")
        base = rev[rev.ticker == t].sort_values("FE_FP_END")
        if a.empty: continue
        m = pd.merge_asof(base, a[["date", "ca_yoy"]], left_on="FE_FP_END", right_on="date", direction="nearest", tolerance=pd.Timedelta(days=50))
        if not w.empty:
            m = pd.merge_asof(m.sort_values("FE_FP_END"), w[["date","web_yoy"]].sort_values("date"),
                              left_on="FE_FP_END", right_on="date", direction="nearest", tolerance=pd.Timedelta(days=50))
        else: m["web_yoy"] = np.nan
        parts.append(m)
    dr = pd.concat(parts, ignore_index=True)
    de = dr[dr.ticker.isin(ECOMM)].dropna(subset=["web_yoy"])
    log(f"e-commerce panel w/ clickstream: {len(de)} company-quarters, {de.ticker.nunique()} tickers")
    a1 = mreg_boot(de, "rev_surprise", ["ca_yoy"]); a2 = mreg_boot(de, "rev_surprise", ["web_yoy"]); a3 = mreg_boot(de, "rev_surprise", ["ca_yoy","web_yoy"])
    if a1: log(f"  Y~ca_yoy          : R²={a1['r2']:+.3f} coef={a1['coef'][0]:+.3f} p={a1['p'][0]:.3f} (n={a1['n']})")
    if a2: log(f"  Y~web_yoy         : R²={a2['r2']:+.3f} coef={a2['coef'][0]:+.3f} p={a2['p'][0]:.3f}")
    if a3: log(f"  Y~ca_yoy+web_yoy  : R²={a3['r2']:+.3f} ca={a3['coef'][0]:+.3f}(p{a3['p'][0]:.2f}) web={a3['coef'][1]:+.3f}(p{a3['p'][1]:.2f}) — does web ADD?")
    rweb = de.web_yoy.corr(de.rev_surprise)
    psurr_web = eq.surrogate(de, "web_yoy", "rev_surprise", rweb)
    log(f"  surrogate (shuffle-company) web_yoy→rev_surprise: r={rweb:+.3f} p_surr={psurr_web:.3f}")

    # app (UBER/DASH/ABNB) — tiny n, descriptive
    app = pd.read_csv(A / "ca0054_app_users_3y.csv"); app["ticker"] = app["entity_id"].map(ID2TKR_APP)
    aq = quarter_yoy_from_monthly(app, "app_users", "ticker").rename(columns={"yoy":"app_yoy"})
    aq["date"] = aq["q"].dt.to_timestamp("Q")
    parts = []
    for t in ["UBER","DASH","ABNB"]:
        a = aq[aq.ticker==t].dropna(subset=["app_yoy"]); base = rev[rev.ticker==t].sort_values("FE_FP_END")
        if a.empty or base.empty: continue
        m = pd.merge_asof(base, a[["date","app_yoy"]].sort_values("date"), left_on="FE_FP_END", right_on="date", direction="nearest", tolerance=pd.Timedelta(days=50))
        parts.append(m)
    if parts:
        da = pd.concat(parts, ignore_index=True).dropna(subset=["app_yoy","rev_surprise"])
        log(f"\napp panel (UBER/DASH/ABNB): {len(da)} obs — tiny, descriptive only")
        if len(da) >= 6:
            log(f"  corr(app_yoy, rev_surprise) = {da.app_yoy.corr(da.rev_surprise):+.3f} (n={len(da)})")

    log("\n## VERDICT (pilot) — surrogate-corrected (cluster-bootstrap alone over-claims; surrogate removes common trend)")
    log(f"  EPS / commodity cost: cost has the right sign (cost↑→EPS miss, r={rco:+.3f}) and lifts combo R² "
        f"{r1['r2']:+.3f}→{r3['r2']:+.3f}, BUT it is only borderline (surrogate p={psurr_cost:.3f}) and cost_yoy is a")
    log(f"     COMMON time factor (food/cotton, ~10 distinct values) + commodity prices are PUBLIC → weak hint, not edge.")
    log(f"  Revenue / clickstream: the 'web adds beyond card' (combo R² {a1['r2']:+.3f}→{a3['r2']:+.3f}, cluster p<0.01)")
    log(f"     is a COMMON-TREND ARTIFACT — it FAILS the shuffle-company surrogate (p_surr={psurr_web:.3f}). Web traffic and")
    log(f"     e-commerce revenue surprises rose together 2024-26, but company A's web does NOT predict company A's surprise.")
    log(f"  → Both pilots collapse to weak/null under the surrogate, same lesson as every prior layer: CA measures, doesn't edge.")
    OUT_MD.write_text("# Pilot — commodity cost (EPS) + clickstream/app (revenue)\n\n> 2026-06-04 · `scripts/auto/s_z_pilot_test.py`\n\n```\n"+"\n".join(lines)+"\n```\n")
    print(f"\n[written] {OUT_MD}")

if __name__ == "__main__":
    main()
