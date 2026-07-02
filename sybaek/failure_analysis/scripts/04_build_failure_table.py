#!/usr/bin/env python3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from sybaek.failure_analysis.src.config import ensure_parent, load_config, parse_args, require_file, resolve_path


PROFILE_COLUMNS = [
    "column_id",
    "row_count",
    "non_null_count",
    "unique_count",
    "duplicate_ratio",
    "null_ratio",
    "cardinality_ratio",
    "avg_length",
    "numeric_ratio",
    "date_like_ratio",
    "alpha_ratio",
    "entropy",
    "top1_frequency",
    "top5_frequency",
]


def main():
    args = parse_args("Build joined pair-level failure table.")
    config = load_config(args.config)
    outputs = config["outputs"]
    options = config.get("options", {})

    rank_path = require_file(resolve_path(config, outputs["rank_comparison"]), "rank comparison")
    overlap_path = require_file(resolve_path(config, outputs["pair_overlap_metrics"]), "pair overlap metrics")
    profile_path = require_file(resolve_path(config, outputs["column_profiles"]), "column profiles")
    output_path = ensure_parent(resolve_path(config, outputs["failure_table"]))

    rank = pd.read_csv(rank_path)
    overlap = pd.read_csv(overlap_path)
    profiles = pd.read_csv(profile_path)

    rank = rank[rank["status"] == "ok"].copy()
    overlap = overlap[overlap["status"] == "ok"].copy()
    profiles = profiles[profiles["status"] == "ok"][PROFILE_COLUMNS].copy()

    overlap = overlap.rename(
        columns={
            "query_unique_count": "query_overlap_unique_count",
            "candidate_unique_count": "candidate_overlap_unique_count",
        }
    )
    df = rank.merge(
        overlap.drop(columns=["status", "error"]),
        on=["pair_id", "query_column_id", "candidate_column_id"],
        how="left",
    )

    query_profiles = profiles.add_prefix("query_").rename(columns={"query_column_id": "query_column_id"})
    candidate_profiles = profiles.add_prefix("candidate_").rename(columns={"candidate_column_id": "candidate_column_id"})
    df = df.merge(query_profiles, on="query_column_id", how="left")
    df = df.merge(candidate_profiles, on="candidate_column_id", how="left")

    success_t = int(options.get("success_rank_threshold", 10))
    failure_t = int(options.get("failure_rank_threshold", 100))
    hard_t = int(options.get("hard_failure_rank_threshold", 1000))
    high_overlap_t = float(options.get("high_overlap_threshold", 0.8))
    high_jaccard_t = float(options.get("high_jaccard_threshold", 0.5))
    low_overlap_t = float(options.get("low_overlap_threshold", 0.2))

    df["rank_group"] = df["exact_rank"].apply(lambda rank: rank_group(rank, success_t, failure_t, hard_t))
    df["is_success_topk"] = df["exact_rank"] <= success_t
    df["is_embedding_failure"] = df["exact_rank"] > failure_t
    df["is_hard_failure"] = df["exact_rank"] > hard_t
    df["is_high_overlap_missed"] = (df["max_containment"] >= high_overlap_t) & df["is_embedding_failure"]
    df["is_high_jaccard_missed"] = (df["jaccard"] >= high_jaccard_t) & df["is_embedding_failure"]
    df["is_low_overlap_missed"] = (df["max_containment"] < low_overlap_t) & df["is_embedding_failure"]
    df["is_numeric_or_date_missed"] = (
        df[[
            "query_numeric_ratio",
            "candidate_numeric_ratio",
            "query_date_like_ratio",
            "candidate_date_like_ratio",
        ]].max(axis=1)
        >= 0.8
    ) & df["is_embedding_failure"]
    df["is_high_cardinality_missed"] = (
        df[["query_cardinality_ratio", "candidate_cardinality_ratio"]].min(axis=1) >= 0.8
    ) & df["is_embedding_failure"]

    df.to_csv(output_path, index=False)
    print(f"Wrote {len(df)} rows to {output_path}")


def rank_group(rank, success_t, failure_t, hard_t):
    if rank <= success_t:
        return f"rank_1_{success_t}"
    if rank <= failure_t:
        return f"rank_{success_t + 1}_{failure_t}"
    if rank <= hard_t:
        return f"rank_{failure_t + 1}_{hard_t}"
    return f"rank_gt_{hard_t}"


if __name__ == "__main__":
    main()
