"""Stage C — Mechanism verification via Anthropic LLM.

Reads outputs/auto/timing_pass.csv (~5,664 pairs from Stage B), runs each
through an Anthropic LLM with a STRUCTURED prompt asking for:
  {connected: bool, channel: str, caveat: str}

Only pairs where connected=true are kept as verification pairs.

Default model: Haiku 4.5 (cheaper, fine for binary classification + 1-2 sentence rationale).
Override with --model claude-sonnet-4-6 if needed.

Requires ANTHROPIC_API_KEY in environment or .env.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "auto"
OUT.mkdir(parents=True, exist_ok=True)


SYSTEM_PROMPT = """You are an economic-mechanism verifier for an alt-data research project.

A pair = (CarbonArc dataset, Kalshi prediction market). The Kalshi market settles on an official macro release (BLS / BEA / Census / Fed / etc).

Decide whether the CA dataset's measured quantity is *causally connected* to the macro release that the Kalshi market settles on.

CONNECTED requires a real economic channel: changes in the CA quantity should plausibly precede or determine changes in the macro release value (or at least be a meaningful subset of it).

Output STRICT JSON only:
{"connected": true|false, "channel": "1-2 sentence economic mechanism", "caveat": "if any limitation, otherwise empty string"}

No prose outside the JSON.
"""

USER_TEMPLATE = """CarbonArc dataset {ca_id} — {ca_name}
  Subjects: {ca_subjects}
  Frequency: {ca_frequency}
  Publication lag: {ca_lag_days} days

Kalshi series {kalshi_ticker}: "{kalshi_title}"
  Category: {kalshi_category}
  Settles on macro event(s): {matched_events}
"""


def build_user(row: pd.Series) -> str:
    return USER_TEMPLATE.format(
        ca_id=row["ca_dataset_id"],
        ca_name=row["ca_name"],
        ca_subjects=row.get("ca_subjects", "") or "",
        ca_frequency=row.get("ca_frequency", "") or "",
        ca_lag_days=int(row.get("ca_lag_days", 0)),
        kalshi_ticker=row["kalshi_series_ticker"],
        kalshi_title=row["kalshi_title"],
        kalshi_category=row.get("kalshi_category", "") or "",
        matched_events=row["matched_events"],
    )


def call_llm(client: Anthropic, model: str, user_msg: str,
             max_retries: int = 3) -> dict:
    for attempt in range(max_retries):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=300,
                temperature=0,
                system=[{"type": "text", "text": SYSTEM_PROMPT,
                         "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": user_msg}],
            )
            text = "".join(b.text for b in resp.content if hasattr(b, "text"))
            # Find JSON in the response
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1:
                raise ValueError(f"no JSON in response: {text[:200]}")
            return json.loads(text[start:end + 1])
        except Exception as e:
            if attempt == max_retries - 1:
                return {"connected": None, "channel": "",
                        "caveat": f"ERROR: {type(e).__name__}: {str(e)[:200]}"}
            time.sleep(2 ** attempt)
    return {"connected": None, "channel": "", "caveat": "max retries"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="claude-haiku-4-5",
                        help="Anthropic model name (claude-haiku-4-5 or claude-sonnet-4-6)")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max pairs to evaluate (0 = all)")
    parser.add_argument("--workers", type=int, default=8,
                        help="Concurrent worker threads")
    parser.add_argument("--resume", action="store_true",
                        help="Skip pairs already in output")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set in env or .env", file=sys.stderr)
        sys.exit(1)

    client = Anthropic(api_key=api_key)

    df = pd.read_csv(OUT / "timing_pass.csv")
    if args.limit > 0:
        df = df.head(args.limit)
    print(f"Verifying {len(df)} timing-pass pairs with {args.model} "
          f"× {args.workers} workers")

    out_path = OUT / "mechanism_verified.csv"
    done_keys: set[tuple] = set()
    if args.resume and out_path.exists():
        prev = pd.read_csv(out_path)
        done_keys = {(r["ca_dataset_id"], r["kalshi_series_ticker"])
                     for _, r in prev.iterrows()}
        print(f"resume: {len(done_keys)} already done")

    todo = df[~df.apply(
        lambda r: (r["ca_dataset_id"], r["kalshi_series_ticker"]) in done_keys,
        axis=1)] if done_keys else df

    rows: list[dict] = []
    completed = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as exe:
        future_to_idx = {
            exe.submit(call_llm, client, args.model, build_user(r)): idx
            for idx, r in todo.iterrows()
        }
        for fut in as_completed(future_to_idx):
            idx = future_to_idx[fut]
            verdict = fut.result()
            r = todo.loc[idx]
            rows.append({
                "ca_dataset_id": r["ca_dataset_id"],
                "ca_name": r["ca_name"],
                "kalshi_series_ticker": r["kalshi_series_ticker"],
                "kalshi_title": r["kalshi_title"],
                "matched_events": r["matched_events"],
                "lead_window_days": r["lead_window_days"],
                "connected": verdict.get("connected"),
                "channel": verdict.get("channel", ""),
                "caveat": verdict.get("caveat", ""),
            })
            completed += 1
            if completed % 50 == 0:
                elapsed = time.time() - t0
                rate = completed / elapsed
                print(f"  {completed}/{len(todo)} done "
                      f"({rate:.1f}/s, ~{(len(todo) - completed) / rate:.0f}s left)")

    new_df = pd.DataFrame(rows)
    if args.resume and out_path.exists():
        combined = pd.concat([prev, new_df], ignore_index=True)
    else:
        combined = new_df
    combined.to_csv(out_path, index=False)
    print(f"\nwrote {out_path} ({len(combined)} total rows)")

    # Summary
    cdf = combined[combined["connected"] == True]
    print(f"connected=true: {len(cdf)}")
    print(f"connected=false: {(combined['connected'] == False).sum()}")
    print(f"errors: {combined['connected'].isna().sum()}")

    # Save accepted
    final = (cdf.sort_values("lead_window_days", ascending=False)
                .reset_index(drop=True))
    final.to_csv(OUT / "verification_pairs_macro.csv", index=False)
    print(f"\nwrote outputs/auto/verification_pairs_macro.csv ({len(final)} accepted)")


if __name__ == "__main__":
    main()
