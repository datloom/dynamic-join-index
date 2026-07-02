# Initial Failure Analysis

Dataset: LakeBench WebTable join.

Method analyzed: DeepJoin-style column embeddings with exact nearest-neighbor rank.

## Pipeline Summary

```text
GT rows: 54,823
Kept GT pairs: 54,219
Skipped GT pairs: 604
Extracted tables: 4,280
Analyzed columns: 15,518
Embedding shape: 15,518 x 768
```

## Rank Groups

```text
rank 1-10: 18,293 pairs
rank 11-100: 16,860 pairs
rank 101-1000: 16,585 pairs
rank >1000: 2,481 pairs
```

Interpretation:

- `rank 1-10`: DeepJoin retrieves the GT joinable column well.
- `rank 11-100`: close candidate, but may be missed under small top-k.
- `rank 101-1000`: embedding-level miss candidate.
- `rank >1000`: hard embedding failure.

## Key Observations

1. Easy pairs are strongly associated with high value overlap.
   The `rank 1-10` group has median Jaccard and max-containment near `1.0`.

2. Many missed pairs have weak value overlap.
   The `rank 101-1000` group has much lower median overlap, and the `rank >1000` group has near-zero median overlap.

3. Some high-overlap pairs are still missed.
   These are useful failure cases because value overlap suggests joinability, but the embedding does not rank the pair highly.

```text
high_overlap_missed: 2,999
high_jaccard_missed: 1,501
numeric_or_date_missed: 11,794
high_cardinality_missed: 6,067
hard_failure: 2,481
```

## Figures

- `results/plots/failure_group_counts.png`: number of GT pairs by rank group.
- `results/plots/rank_distribution.png`: exact-rank distribution.
- `results/plots/overlap_by_rank_group.png`: overlap distribution by rank group.
- `results/plots/rank_vs_overlap_scatter.png`: pair-level overlap vs exact rank.
- `results/plots/column_feature_medians_by_group.png`: median features by rank group.
- `results/plots/feature_correlation_heatmap.png`: feature correlation matrix.

## Representative Samples

- `results/samples/high_overlap_missed_cases.csv`
- `results/samples/high_jaccard_missed_cases.csv`
- `results/samples/low_overlap_missed_cases.csv`
- `results/samples/numeric_or_date_missed_cases.csv`
- `results/samples/high_cardinality_missed_cases.csv`
- `results/samples/hard_failure_cases.csv`

## Next Step

Build inspection tables that include sample values and table headers, then manually label 50-100 representative failures.
