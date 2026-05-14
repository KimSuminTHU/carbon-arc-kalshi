"""Phase 1.0 — Fetch actual sample rows for the top-candidate datasets.

For each (dataset_id, entity_topic_id) we call get_data_sample and
save the resulting 100-row dataframe to outputs/samples/<id>__<topic>.csv.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pandas as pd
from carbonarc import CarbonArcClient
from dotenv import load_dotenv

load_dotenv()

OUT = Path(__file__).resolve().parents[1] / "outputs" / "samples"
OUT.mkdir(parents=True, exist_ok=True)

# Datasets we want full per-topic samples for (Phase 1 EDA targets).
TARGETS = [
    "CA0049",  # medical/pharmacy claims (8 topics, drug-level)
    "CA0056",  # card spend (7 topics, payment/cohort)
    "CA0028",  # card detailed historic
    "CA0030",  # clickstream (7 topics, overlap/audience)
    "CA0060",  # foot traffic
    "CA0077",  # commodity prices
    "CA0058",  # health card
    "CA0040",  # trade claims
    "CA0054",  # app intelligence
    "CA0013",  # mobile app
    "CA0035",  # financial news (27 topics)
    "CA009",   # digital advertising
    "CA0053",  # job movements
]


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:60]


def _extract_payload(sample) -> dict | None:
    """The API returns roughly:
        DataFrame[dataset_id, samples] OR
        {dataset_id, samples: {entity_topic_id, columns, data: [{...}, ...]}} OR
        {dataset_id, samples: [{entity_topic_id, ..., data: [...]}, ...]}
    Normalize to a list of payload dicts {entity_topic_id, label, data}.
    """
    if isinstance(sample, pd.DataFrame):
        if "samples" in sample.columns:
            payloads = []
            for v in sample["samples"]:
                if isinstance(v, dict):
                    payloads.append(v)
            return payloads
    if isinstance(sample, dict):
        s = sample.get("samples", sample)
        if isinstance(s, list):
            return s
        if isinstance(s, dict):
            return [s]
    return None


def fetch_dataset(c: CarbonArcClient, dsid: str) -> list[dict]:
    out = []
    try:
        sample = c.data.get_data_sample(dsid)
    except Exception as e:
        return [{"dataset_id": dsid, "topic_id": None, "topic_label": None,
                 "ok": False, "err": f"sample: {e}"}]

    payloads = _extract_payload(sample) or []
    for p in payloads:
        if not isinstance(p, dict):
            continue
        tid = p.get("entity_topic_id")
        tlabel = p.get("entity_topic_label") or p.get("topic_label") or p.get("label")
        data = p.get("data")
        if not isinstance(data, list) or not data:
            out.append({"dataset_id": dsid, "topic_id": tid, "topic_label": tlabel,
                        "ok": False, "err": "no_data_field"})
            continue
        df = pd.DataFrame(data)
        fname = f"{dsid}__t{tid}__{slug(tlabel or 'topic')}.csv"
        df.to_csv(OUT / fname, index=False)
        out.append({"dataset_id": dsid, "topic_id": tid, "topic_label": tlabel,
                    "ok": True, "n_rows": len(df), "n_cols": len(df.columns),
                    "file": fname})
    return out


def main() -> None:
    token = os.environ["CARBONARC_API_KEY"]
    c = CarbonArcClient(token=token)

    all_meta = []
    for dsid in TARGETS:
        print(f"--- {dsid} ---")
        meta = fetch_dataset(c, dsid)
        for m in meta:
            print(f"  topic_id={m.get('topic_id')} ok={m.get('ok')} "
                  f"label={m.get('topic_label')!r} rows={m.get('n_rows')} "
                  f"err={m.get('err','')}")
        all_meta.extend(meta)

    pd.DataFrame(all_meta).to_csv(OUT / "_index.csv", index=False)
    print(f"\nwrote {OUT / '_index.csv'}")


if __name__ == "__main__":
    main()
