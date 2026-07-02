#!/usr/bin/env python3
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from sybaek.failure_analysis.src.config import load_config, parse_args, require_file, resolve_path


GROUP_ORDER = ["rank_1_10", "rank_11_100", "rank_101_1000", "rank_gt_1000"]
GROUP_LABELS = ["1-10", "11-100", "101-1000", ">1000"]


def main():
    args = parse_args("Plot failure-analysis figures.")
    config = load_config(args.config)
    failure_path = require_file(resolve_path(config, config["outputs"]["failure_table"]), "failure table")
    plots_dir = resolve_path(config, config["outputs"]["plots_dir"])
    plots_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(failure_path)
    plot_rank_distribution(df, plots_dir / "rank_distribution.png")
    plot_group_counts(df, plots_dir / "failure_group_counts.png")
    plot_overlap_by_group(df, plots_dir / "overlap_by_rank_group.png")
    plot_rank_vs_overlap(df, plots_dir / "rank_vs_overlap_scatter.png")
    plot_feature_medians(df, plots_dir / "column_feature_medians_by_group.png")
    plot_correlation(df, plots_dir / "feature_correlation_heatmap.png")
    print(f"Wrote plots to {plots_dir}")


def plot_rank_distribution(df, path):
    plt.figure(figsize=(8, 5))
    ranks = df["exact_rank"].clip(lower=1)
    bins = np.logspace(0, np.log10(ranks.max()), 50)
    plt.hist(ranks, bins=bins, color="#3b82f6", edgecolor="white")
    plt.xscale("log")
    plt.xlabel("Exact embedding rank")
    plt.ylabel("GT pair count")
    plt.title("Distribution of exact ranks for GT joinable pairs")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_group_counts(df, path):
    counts = df["rank_group"].value_counts().reindex(GROUP_ORDER, fill_value=0)
    plt.figure(figsize=(7, 5))
    plt.bar(GROUP_LABELS, counts.values, color=["#16a34a", "#65a30d", "#f59e0b", "#dc2626"])
    plt.xlabel("Exact rank group")
    plt.ylabel("GT pair count")
    plt.title("GT pairs by retrieval difficulty")
    for i, value in enumerate(counts.values):
        plt.text(i, value, f"{value:,}", ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_overlap_by_group(df, path):
    data = [df.loc[df["rank_group"] == group, "max_containment"].dropna() for group in GROUP_ORDER]
    plt.figure(figsize=(8, 5))
    plt.boxplot(data, tick_labels=GROUP_LABELS, showfliers=False)
    plt.xlabel("Exact rank group")
    plt.ylabel("Max containment")
    plt.title("Value overlap by retrieval difficulty")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_rank_vs_overlap(df, path):
    sample = df.sample(n=min(10000, len(df)), random_state=7)
    colors = np.where(sample["is_embedding_failure"], "#dc2626", "#2563eb")
    plt.figure(figsize=(8, 5))
    plt.scatter(sample["max_containment"], sample["exact_rank"], s=8, alpha=0.35, c=colors)
    plt.yscale("log")
    plt.xlabel("Max containment")
    plt.ylabel("Exact embedding rank")
    plt.title("Overlap vs exact rank")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_feature_medians(df, path):
    features = [
        "jaccard",
        "max_containment",
        "query_cardinality_ratio",
        "candidate_cardinality_ratio",
        "query_numeric_ratio",
        "candidate_numeric_ratio",
        "query_date_like_ratio",
        "candidate_date_like_ratio",
    ]
    grouped = df.groupby("rank_group")[features].median().reindex(GROUP_ORDER)
    plt.figure(figsize=(10, 5.5))
    x = np.arange(len(features))
    width = 0.18
    for idx, group in enumerate(GROUP_ORDER):
        offset = (idx - 1.5) * width
        plt.bar(x + offset, grouped.loc[group].values, width=width, label=GROUP_LABELS[idx])
    plt.xticks(x, [shorten(f) for f in features], rotation=35, ha="right")
    plt.ylabel("Median value")
    plt.title("Median features by exact rank group")
    plt.legend(title="Rank")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def plot_correlation(df, path):
    features = [
        "exact_rank",
        "exact_similarity",
        "jaccard",
        "max_containment",
        "query_cardinality_ratio",
        "candidate_cardinality_ratio",
        "query_numeric_ratio",
        "candidate_numeric_ratio",
        "query_entropy",
        "candidate_entropy",
    ]
    corr = df[features].corr(numeric_only=True)
    plt.figure(figsize=(8, 7))
    im = plt.imshow(corr, vmin=-1, vmax=1, cmap="coolwarm")
    plt.colorbar(im, fraction=0.046, pad=0.04)
    plt.xticks(range(len(features)), [shorten(f) for f in features], rotation=45, ha="right")
    plt.yticks(range(len(features)), [shorten(f) for f in features])
    plt.title("Feature correlation")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def shorten(name):
    return (
        name.replace("query_", "q_")
        .replace("candidate_", "c_")
        .replace("_ratio", "")
        .replace("containment", "contain")
        .replace("cardinality", "card")
        .replace("similarity", "sim")
    )


if __name__ == "__main__":
    main()
