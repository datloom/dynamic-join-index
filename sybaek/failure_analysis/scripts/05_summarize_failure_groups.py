#!/usr/bin/env python3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from sybaek.failure_analysis.src.config import ensure_parent, load_config, parse_args, require_file, resolve_path


METRICS = [
    "exact_rank",
    "exact_similarity",
    "jaccard",
    "max_containment",
    "query_unique_count",
    "candidate_unique_count",
    "query_cardinality_ratio",
    "candidate_cardinality_ratio",
    "query_numeric_ratio",
    "candidate_numeric_ratio",
    "query_date_like_ratio",
    "candidate_date_like_ratio",
    "query_avg_length",
    "candidate_avg_length",
    "query_entropy",
    "candidate_entropy",
]


def main():
    args = parse_args("Summarize success/failure groups.")
    config = load_config(args.config)
    failure_path = require_file(resolve_path(config, config["outputs"]["failure_table"]), "failure table")
    output_path = ensure_parent(resolve_path(config, config["outputs"]["failure_group_summary"]))

    df = pd.read_csv(failure_path)
    rows = []
    for group, group_df in df.groupby("rank_group", sort=False):
        row = {"rank_group": group, "count": len(group_df), "share": len(group_df) / len(df)}
        for metric in METRICS:
            row[f"{metric}_mean"] = group_df[metric].mean()
            row[f"{metric}_median"] = group_df[metric].median()
        row["high_overlap_missed_count"] = int(group_df["is_high_overlap_missed"].sum())
        row["high_jaccard_missed_count"] = int(group_df["is_high_jaccard_missed"].sum())
        row["low_overlap_missed_count"] = int(group_df["is_low_overlap_missed"].sum())
        row["numeric_or_date_missed_count"] = int(group_df["is_numeric_or_date_missed"].sum())
        row["high_cardinality_missed_count"] = int(group_df["is_high_cardinality_missed"].sum())
        rows.append(row)

    pd.DataFrame(rows).to_csv(output_path, index=False)
    print(f"Wrote group summary to {output_path}")


if __name__ == "__main__":
    main()

