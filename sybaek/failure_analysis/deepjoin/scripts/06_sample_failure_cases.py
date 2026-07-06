#!/usr/bin/env python3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from sybaek.failure_analysis.deepjoin.src.config import load_config, parse_args, require_file, resolve_path


KEEP_COLUMNS = [
    "pair_id",
    "query_column_id",
    "candidate_column_id",
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
    "rank_group",
]


def main():
    args = parse_args("Sample representative failure cases.")
    config = load_config(args.config)
    failure_path = require_file(resolve_path(config, config["outputs"]["failure_table"]), "failure table")
    output_dir = resolve_path(config, config["outputs"]["failure_samples_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(failure_path)
    write_sample(df[df["is_high_overlap_missed"]], output_dir / "high_overlap_missed_cases.csv", ["exact_rank", "max_containment"])
    write_sample(df[df["is_high_jaccard_missed"]], output_dir / "high_jaccard_missed_cases.csv", ["exact_rank", "jaccard"])
    write_sample(df[df["is_low_overlap_missed"]], output_dir / "low_overlap_missed_cases.csv", ["exact_rank"])
    write_sample(df[df["is_numeric_or_date_missed"]], output_dir / "numeric_or_date_missed_cases.csv", ["exact_rank"])
    write_sample(df[df["is_high_cardinality_missed"]], output_dir / "high_cardinality_missed_cases.csv", ["exact_rank"])
    write_sample(df[df["is_hard_failure"]], output_dir / "hard_failure_cases.csv", ["exact_rank"])
    print(f"Wrote failure samples to {output_dir}")


def write_sample(df, path, sort_cols, n=200):
    if df.empty:
        pd.DataFrame(columns=KEEP_COLUMNS).to_csv(path, index=False)
        return
    sample = df.sort_values(sort_cols, ascending=[False] * len(sort_cols)).head(n)
    sample[KEEP_COLUMNS].to_csv(path, index=False)


if __name__ == "__main__":
    main()

