#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from sybaek.failure_analysis.src.columns import load_column_values, profile_values
from sybaek.failure_analysis.src.config import ensure_parent, load_config, parse_args, require_file, resolve_path
from sybaek.failure_analysis.src.csv_utils import read_dicts, write_dicts


PROFILE_FIELDS = [
    "column_id",
    "table_path",
    "column_name",
    "column_index",
    "resolved_column_name",
    "row_count",
    "non_null_count",
    "null_count",
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
    "status",
    "error",
]


def main():
    args = parse_args("Profile columns listed in column_manifest.csv.")
    config = load_config(args.config)

    manifest_path = require_file(
        resolve_path(config, config["inputs"]["column_manifest"]),
        "column manifest",
    )
    output_path = ensure_parent(resolve_path(config, config["outputs"]["column_profiles"]))
    options = config.get("options", {})

    rows = []
    for item in read_dicts(manifest_path):
        row = {
            "column_id": item.get("column_id", ""),
            "table_path": item.get("table_path", ""),
            "column_name": item.get("column_name", ""),
            "column_index": item.get("column_index", ""),
        }
        try:
            table_path = require_file(resolve_path(config, row["table_path"]), f"table for {row['column_id']}")
            resolved_name, values = load_column_values(
                table_path,
                column_name=row["column_name"],
                column_index=row["column_index"],
                max_rows=options.get("max_rows_per_table"),
                encoding=options.get("encoding"),
            )
            row.update(profile_values(values))
            row["resolved_column_name"] = resolved_name
            row["status"] = "ok"
            row["error"] = ""
        except Exception as exc:
            row["resolved_column_name"] = ""
            row.update({field: "" for field in PROFILE_FIELDS if field not in row})
            row["status"] = "error"
            row["error"] = str(exc)
        rows.append(row)

    write_dicts(output_path, rows, PROFILE_FIELDS)
    print(f"Wrote {len(rows)} column profiles to {output_path}")


if __name__ == "__main__":
    main()

