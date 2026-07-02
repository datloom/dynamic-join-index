#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from sybaek.failure_analysis.src.columns import load_column_values, value_set
from sybaek.failure_analysis.src.config import ensure_parent, load_config, parse_args, require_file, resolve_path
from sybaek.failure_analysis.src.csv_utils import read_dicts, write_dicts


OVERLAP_FIELDS = [
    "pair_id",
    "query_column_id",
    "candidate_column_id",
    "query_unique_count",
    "candidate_unique_count",
    "intersection_size",
    "union_size",
    "jaccard",
    "containment_query_in_candidate",
    "containment_candidate_in_query",
    "max_containment",
    "status",
    "error",
]


def main():
    args = parse_args("Compute value overlap for ground-truth joinable pairs.")
    config = load_config(args.config)

    manifest_path = require_file(resolve_path(config, config["inputs"]["column_manifest"]), "column manifest")
    pairs_path = require_file(resolve_path(config, config["inputs"]["ground_truth_pairs"]), "ground-truth pairs")
    output_path = ensure_parent(resolve_path(config, config["outputs"]["pair_overlap_metrics"]))
    options = config.get("options", {})

    manifest = {row["column_id"]: row for row in read_dicts(manifest_path)}
    cache = {}

    rows = []
    for pair in read_dicts(pairs_path):
        row = {
            "pair_id": pair.get("pair_id", ""),
            "query_column_id": pair.get("query_column_id", ""),
            "candidate_column_id": pair.get("candidate_column_id", ""),
        }
        try:
            q_values = get_values(config, options, manifest, cache, row["query_column_id"])
            c_values = get_values(config, options, manifest, cache, row["candidate_column_id"])

            q_set = value_set(q_values)
            c_set = value_set(c_values)
            intersection = q_set & c_set
            union = q_set | c_set

            row.update(
                {
                    "query_unique_count": len(q_set),
                    "candidate_unique_count": len(c_set),
                    "intersection_size": len(intersection),
                    "union_size": len(union),
                    "jaccard": safe_div(len(intersection), len(union)),
                    "containment_query_in_candidate": safe_div(len(intersection), len(q_set)),
                    "containment_candidate_in_query": safe_div(len(intersection), len(c_set)),
                    "max_containment": max(safe_div(len(intersection), len(q_set)), safe_div(len(intersection), len(c_set))),
                    "status": "ok",
                    "error": "",
                }
            )
        except Exception as exc:
            row.update({field: "" for field in OVERLAP_FIELDS if field not in row})
            row["status"] = "error"
            row["error"] = str(exc)
        rows.append(row)

    write_dicts(output_path, rows, OVERLAP_FIELDS)
    print(f"Wrote {len(rows)} pair overlap rows to {output_path}")


def get_values(config, options, manifest, cache, column_id):
    if column_id in cache:
        return cache[column_id]
    if column_id not in manifest:
        raise KeyError(f"Column id not found in manifest: {column_id}")

    item = manifest[column_id]
    table_path = require_file(resolve_path(config, item["table_path"]), f"table for {column_id}")
    _, values = load_column_values(
        table_path,
        column_name=item.get("column_name"),
        column_index=item.get("column_index"),
        max_rows=options.get("max_rows_per_table"),
        encoding=options.get("encoding"),
    )
    cache[column_id] = values
    return values


def safe_div(numerator, denominator):
    return float(numerator) / float(denominator) if denominator else 0.0


if __name__ == "__main__":
    main()

