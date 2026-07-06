#!/usr/bin/env python3
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from sybaek.failure_analysis.deepjoin.src.config import load_config, parse_args, require_file, resolve_path


GROUP_ORDER = ["rank_1_10", "rank_11_100", "rank_101_1000", "rank_gt_1000"]
GROUP_LABELS = ["1-10", "11-100", "101-1000", ">1000"]
RANK_BINS = [1, 2, 6, 11, 21, 51, 101, 1001, np.inf]
RANK_BIN_LABELS = ["1", "2-5", "6-10", "11-20", "21-50", "51-100", "101-1000", ">1000"]
HIT_K_VALUES = [1, 5, 10, 20, 50, 100, 500, 1000, 5000, 10000]


def main():
    args = parse_args("Plot DeepJoin GT-pair rank and failure-analysis figures.")
    config = load_config(args.config)
    failure_path = require_file(resolve_path(config, config["outputs"]["failure_table"]), "failure table")
    plots_dir = resolve_path(config, config["outputs"]["plots_dir"])
    plots_dir.mkdir(parents=True, exist_ok=True)

    df = add_derived_features(pd.read_csv(failure_path))

    plot_gt_pair_rank_distribution(df, plots_dir / "gt_pair_rank_distribution.png")
    plot_pair_level_hit_curve(df, plots_dir / "pair_level_hit_at_k_curve.png")
    plot_rank_vs_query_containment(df, plots_dir / "rank_vs_query_containment_scatter.png")
    plot_feature_boxplots_by_rank_group(df, plots_dir / "feature_boxplots_by_rank_group.png")

    print(f"Wrote DeepJoin failure-analysis plots to {plots_dir}")


def add_derived_features(df):
    if "query_containment" not in df.columns and "containment_query_in_candidate" in df.columns:
        df["query_containment"] = df["containment_query_in_candidate"]
    if "candidate_containment" not in df.columns and "containment_candidate_in_query" in df.columns:
        df["candidate_containment"] = df["containment_candidate_in_query"]
    if "pair_cardinality_proportion" not in df.columns:
        df["pair_cardinality_proportion"] = [
            safe_min_max_ratio(query_count, candidate_count)
            for query_count, candidate_count in zip(df["query_unique_count"], df["candidate_unique_count"])
        ]
    if "entropy_abs_diff" not in df.columns:
        df["entropy_abs_diff"] = (df["query_entropy"] - df["candidate_entropy"]).abs()
    if "avg_length_abs_diff" not in df.columns:
        df["avg_length_abs_diff"] = (df["query_avg_length"] - df["candidate_avg_length"]).abs()
    if "max_numeric_or_date_ratio" not in df.columns:
        df["max_numeric_or_date_ratio"] = df[
            [
                "query_numeric_ratio",
                "candidate_numeric_ratio",
                "query_date_like_ratio",
                "candidate_date_like_ratio",
            ]
        ].max(axis=1)
    return df


def plot_gt_pair_rank_distribution(df, path):
    ranks = df["exact_rank"].clip(lower=1)
    bins = pd.cut(ranks, bins=RANK_BINS, labels=RANK_BIN_LABELS, right=False)
    counts = bins.value_counts(sort=False)
    shares = counts / len(df)

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(RANK_BIN_LABELS, counts.values, color="#4c78a8", edgecolor="white", linewidth=0.8)
    ax.set_xlabel("DeepJoin exact rank of GT candidate")
    ax.set_ylabel("GT pair count")
    ax.set_title("GT Pair Rank Distribution")
    ax.grid(axis="y", color="#d9d9d9", linewidth=0.8, alpha=0.7)
    ax.set_axisbelow(True)

    max_count = counts.max() if len(counts) else 0
    for bar, count, share in zip(bars, counts.values, shares.values):
        if count == 0:
            continue
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            count + max_count * 0.015,
            f"{count:,}\n({share:.1%})",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_pair_level_hit_curve(df, path):
    ranks = df["exact_rank"].clip(lower=1)
    max_rank = int(ranks.max())
    k_values = [k for k in HIT_K_VALUES if k <= max_rank]
    if max_rank not in k_values:
        k_values.append(max_rank)
    hit_rates = [(ranks <= k).mean() for k in k_values]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(k_values, hit_rates, marker="o", color="#4c78a8", linewidth=2)
    ax.set_xscale("log")
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Retrieval depth k")
    ax.set_ylabel("GT pair coverage, fraction with rank <= k")
    ax.set_title("Pair-level Hit@k Curve")
    ax.grid(True, which="both", color="#d9d9d9", linewidth=0.8, alpha=0.7)

    for k, hit_rate in zip(k_values, hit_rates):
        if k in {1, 10, 100, 1000, max_rank}:
            ax.annotate(f"{hit_rate:.1%}", (k, hit_rate), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8)

    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_rank_vs_query_containment(df, path):
    sample = df.sample(n=min(20000, len(df)), random_state=7)

    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.scatter(
        sample["exact_rank"].clip(lower=1),
        sample["query_containment"],
        s=10,
        alpha=0.28,
        color="#4c78a8",
        edgecolors="none",
    )
    for cutoff in [10, 100, 1000]:
        ax.axvline(cutoff, color="#9a9a9a", linestyle="--", linewidth=1)
        ax.text(cutoff, 1.02, f"k={cutoff}", ha="center", va="bottom", fontsize=8, color="#555555")
    ax.set_xscale("log")
    ax.set_ylim(-0.03, 1.08)
    ax.set_xlabel("DeepJoin exact rank of GT candidate")
    ax.set_ylabel("Query containment |Q ∩ C| / |Q|")
    ax.set_title("Rank vs Query-side Cell Coverage")
    ax.grid(True, which="both", color="#d9d9d9", linewidth=0.8, alpha=0.7)

    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_feature_boxplots_by_rank_group(df, path):
    features = [
        ("query_containment", "Query containment"),
        ("candidate_containment", "Candidate containment"),
        ("jaccard", "Jaccard"),
        ("pair_cardinality_proportion", "Cardinality proportion"),
        ("entropy_abs_diff", "Entropy absolute difference"),
        ("avg_length_abs_diff", "Average length absolute difference"),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(13, 7), sharex=True)
    for ax, (column, label) in zip(axes.ravel(), features):
        data = [df.loc[df["rank_group"] == group, column].dropna() for group in GROUP_ORDER]
        ax.boxplot(
            data,
            tick_labels=GROUP_LABELS,
            showfliers=False,
            patch_artist=True,
            medianprops={"color": "#1f1f1f", "linewidth": 1.2},
            boxprops={"facecolor": "#d8e6f3", "edgecolor": "#4c78a8"},
            whiskerprops={"color": "#4c78a8"},
            capprops={"color": "#4c78a8"},
        )
        ax.set_title(label)
        ax.grid(axis="y", color="#d9d9d9", linewidth=0.8, alpha=0.7)
        ax.set_axisbelow(True)
        ax.tick_params(axis="x", rotation=20)

    fig.suptitle("Feature Boxplots by DeepJoin Rank Group", y=1.02, fontsize=13)
    fig.supxlabel("DeepJoin exact rank group")
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def safe_min_max_ratio(left, right):
    denominator = max(float(left), float(right))
    return min(float(left), float(right)) / denominator if denominator else 0.0


if __name__ == "__main__":
    main()
