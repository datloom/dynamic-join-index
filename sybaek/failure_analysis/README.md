# Failure Analysis

Failure analysis of joinability discovery methods on LakeBench.

The first pipeline focuses on three questions:

1. Which ground-truth joinable column pairs are missed by ANN retrieval?
2. Do missed pairs have high value overlap?
3. What column-level characteristics distinguish found and missed pairs?

## Pipeline

Run the scripts in numeric order:

```bash
cd /home/syback/AIST/dynamic-join-index
bash sybaek/failure_analysis/scripts/run_all.sh
```

The default config is:

```text
sybaek/failure_analysis/configs/deepjoin_failure_analysis.json
```

## Required Inputs

Place large/generated input files under `sybaek/failure_analysis/artifacts/`.
This directory is ignored by Git.

For the current WebTable join experiment, `00_prepare_webtable_join_inputs.py`
expects LakeBench raw files under:

```text
sybaek/failure_analysis/artifacts/raw/webtable_join/
```

Those raw files are not committed. They can be re-downloaded from LakeBench.

### `column_manifest.csv`

One row per column to analyze.

```csv
column_id,table_path,column_name,column_index
q1_city,datasets/LakeBench/example/query.csv,city,
t1_city,datasets/LakeBench/example/table.csv,city,
```

Use either `column_name` or `column_index`. `column_index` is zero-based.

### `ground_truth_pairs.csv`

One row per joinable pair from the benchmark ground truth.

```csv
pair_id,query_column_id,candidate_column_id
p1,q1_city,t1_city
```

### `deepjoin_column_embeddings.npz`

NumPy archive with:

- `ids`: string array of `column_id`
- `vectors`: 2D float array with shape `(num_columns, dim)`

### `deepjoin_ann_results.csv` Optional

ANN retrieval output.

```csv
query_column_id,candidate_column_id,rank,score
q1_city,t1_city,1,0.91
```

If `rank` is missing, row order per query is used.

## Outputs

- `results/failure_group_summary.csv`: committed compact summary by rank group.
- `results/samples/*.csv`: committed representative failure cases.
- `results/plots/*.png`: committed figures for quick inspection.

Large reproducible CSV outputs are ignored by Git:

- `results/column_profiles.csv`: per-column statistics.
- `results/pair_overlap_metrics.csv`: value overlap for ground-truth pairs.
- `results/rank_comparison.csv`: exact embedding rank and optional ANN rank.
- `results/failure_table.csv`: joined pair-level analysis table.

## Current Analysis

See [reports/initial_failure_analysis.md](reports/initial_failure_analysis.md).
