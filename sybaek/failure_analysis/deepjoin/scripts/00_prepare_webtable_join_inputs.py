#!/usr/bin/env python3
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from sybaek.failure_analysis.deepjoin.src.config import ensure_parent, load_config, parse_args, resolve_path


RAW_ROOT = "sybaek/datasets/lakebench/webtable_join"
QUERY_FILE = f"{RAW_ROOT}/query/webtable_join_query.csv"
GROUND_TRUTH_FILE = f"{RAW_ROOT}/ground_truth/webtable_join_ground_truth.csv"
EXTRACTED_ROOT = f"{RAW_ROOT}/tables"
SUMMARY_FILE = "sybaek/failure_analysis/deepjoin/results/webtable_join_prepare_summary.csv"


def main():
    args = parse_args("Prepare WebTable join inputs from LakeBench raw files.")
    config = load_config(args.config)

    query_path = resolve_path(config, QUERY_FILE)
    gt_path = resolve_path(config, GROUND_TRUTH_FILE)
    extracted_root = resolve_path(config, EXTRACTED_ROOT)
    manifest_path = ensure_parent(resolve_path(config, config["inputs"]["column_manifest"]))
    pairs_path = ensure_parent(resolve_path(config, config["inputs"]["ground_truth_pairs"]))
    summary_path = ensure_parent(resolve_path(config, SUMMARY_FILE))

    table_paths = build_table_path_index(extracted_root, config)
    header_cache = {}

    rows = []
    skipped = []
    needed_columns = {}

    with gt_path.open("r", encoding="utf-8-sig", newline="") as f:
        for idx, row in enumerate(csv.DictReader(f), 1):
            query_table = row["query_table"]
            candidate_table = row["candidate_table"]
            query_column = row["query_column"]
            candidate_column = row["candidate_column"]

            q_path = table_paths.get(query_table)
            c_path = table_paths.get(candidate_table)
            if not q_path or not c_path:
                skipped.append((idx, "missing_table", query_table, candidate_table, query_column, candidate_column))
                continue

            if not column_exists(q_path, query_column, header_cache):
                skipped.append((idx, "missing_query_column", query_table, candidate_table, query_column, candidate_column))
                continue
            if not column_exists(c_path, candidate_column, header_cache):
                skipped.append((idx, "missing_candidate_column", query_table, candidate_table, query_column, candidate_column))
                continue

            q_id = make_column_id(query_table, query_column)
            c_id = make_column_id(candidate_table, candidate_column)
            needed_columns[q_id] = {
                "column_id": q_id,
                "table_path": q_path,
                "column_name": query_column,
                "column_index": "",
            }
            needed_columns[c_id] = {
                "column_id": c_id,
                "table_path": c_path,
                "column_name": candidate_column,
                "column_index": "",
            }
            rows.append(
                {
                    "pair_id": f"webtable_join_{idx}",
                    "query_column_id": q_id,
                    "candidate_column_id": c_id,
                }
            )

    write_csv(
        manifest_path,
        ["column_id", "table_path", "column_name", "column_index"],
        sorted(needed_columns.values(), key=lambda x: x["column_id"]),
    )
    write_csv(
        pairs_path,
        ["pair_id", "query_column_id", "candidate_column_id"],
        rows,
    )
    write_csv(
        summary_path,
        ["metric", "value"],
        [
            {"metric": "tables_extracted", "value": len(table_paths)},
            {"metric": "ground_truth_rows", "value": len(rows) + len(skipped)},
            {"metric": "ground_truth_pairs_kept", "value": len(rows)},
            {"metric": "ground_truth_pairs_skipped", "value": len(skipped)},
            {"metric": "manifest_columns", "value": len(needed_columns)},
        ],
    )

    skipped_path = summary_path.with_name("webtable_join_prepare_skipped.csv")
    write_csv(
        skipped_path,
        ["source_row", "reason", "query_table", "candidate_table", "query_column", "candidate_column"],
        [
            {
                "source_row": item[0],
                "reason": item[1],
                "query_table": item[2],
                "candidate_table": item[3],
                "query_column": item[4],
                "candidate_column": item[5],
            }
            for item in skipped
        ],
    )

    print(f"Wrote manifest: {manifest_path}")
    print(f"Wrote pairs: {pairs_path}")
    print(f"Wrote summary: {summary_path}")
    print(f"Kept {len(rows)} pairs, skipped {len(skipped)} pairs")


def build_table_path_index(root, config):
    table_paths = {}
    for path in root.rglob("*.csv"):
        rel = path.relative_to(Path(config["repo_root"]))
        table_paths[path.name] = str(rel)
    return table_paths


def column_exists(table_path, column_name, header_cache):
    if table_path not in header_cache:
        header_cache[table_path] = read_header(table_path)
    target = column_name.strip().lower()
    return any(name == column_name or name.strip().lower() == target for name in header_cache[table_path])


def read_header(table_path):
    with Path(table_path).open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        try:
            return next(csv.reader(f))
        except StopIteration:
            return []


def make_column_id(table, column):
    return f"{table}::{column}"


def write_csv(path, fieldnames, rows):
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
