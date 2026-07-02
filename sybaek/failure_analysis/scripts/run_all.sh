#!/usr/bin/env bash
set -euo pipefail

CONFIG="${1:-sybaek/failure_analysis/configs/deepjoin_failure_analysis.json}"

python sybaek/failure_analysis/scripts/00_prepare_webtable_join_inputs.py --config "$CONFIG"
python sybaek/failure_analysis/scripts/01_profile_columns.py --config "$CONFIG"
python sybaek/failure_analysis/scripts/02_compute_overlap.py --config "$CONFIG"

if [[ ! -f sybaek/failure_analysis/artifacts/deepjoin_column_embeddings.npz ]]; then
  python sybaek/failure_analysis/scripts/generate_deepjoin_embeddings.py --config "$CONFIG"
fi

python sybaek/failure_analysis/scripts/03_analyze_ranks.py --config "$CONFIG"
python sybaek/failure_analysis/scripts/04_build_failure_table.py --config "$CONFIG"
python sybaek/failure_analysis/scripts/05_summarize_failure_groups.py --config "$CONFIG"
python sybaek/failure_analysis/scripts/06_sample_failure_cases.py --config "$CONFIG"
python sybaek/failure_analysis/scripts/07_plot_failure_analysis.py --config "$CONFIG"
