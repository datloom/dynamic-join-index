# DeepJoin Failure Analysis

Failure analysis workspace for DeepJoin-style column embeddings on LakeBench.

The goal is to characterize ground-truth joinable column pairs that are missed
by column-level embedding retrieval, then inspect whether cell-level coverage
and column-profile signals can recover those candidates.

## Layout

- `configs/`: input, output, and threshold settings.
- `scripts/`: reproducible analysis steps.
- `src/`: shared helpers for column loading, CSV IO, ranking, and config paths.
- `artifacts/`: local raw files, embeddings, and optional ANN outputs.
- `results/`: generated CSV summaries, samples, and plots.
- `cache/`, `logs/`, `notebooks/`: local experiment workspace.

Large generated files under `artifacts/`, `cache/`, `logs/`, and `results/`
should remain uncommitted.

## Run

```bash
cd /home/syback/AIST/dynamic-join-index
bash sybaek/failure_analysis/deepjoin/scripts/run_all.sh
```

Default config:

```text
sybaek/failure_analysis/deepjoin/configs/deepjoin_failure_analysis.json
```

For WebTable join experiments, place LakeBench raw files under:

```text
sybaek/datasets/webtable_join/
```

## Initial Figures

`07_plot_failure_analysis.py` generates the first four report figures:

- `gt_pair_rank_distribution.png`: binned distribution of GT candidate ranks.
- `pair_level_hit_at_k_curve.png`: cumulative pair-level Hit@k curve.
- `rank_vs_query_containment_scatter.png`: DeepJoin rank vs query-side cell coverage.
- `feature_boxplots_by_rank_group.png`: key overlap/profile features by rank group.
