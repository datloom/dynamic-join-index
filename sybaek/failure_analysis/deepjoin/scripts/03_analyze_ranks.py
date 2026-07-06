#!/usr/bin/env python3
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from sybaek.failure_analysis.deepjoin.src.config import ensure_parent, load_config, parse_args, require_file, resolve_path
from sybaek.failure_analysis.deepjoin.src.csv_utils import read_dicts, write_dicts
from sybaek.failure_analysis.deepjoin.src.rank_utils import load_ann_results, load_embeddings


RANK_FIELDS = [
    "pair_id",
    "query_column_id",
    "candidate_column_id",
    "exact_rank",
    "exact_similarity",
    "found_in_ann",
    "ann_rank",
    "ann_score",
    "rank_gap",
    "status",
    "error",
]


def main():
    args = parse_args("Compare exact embedding rank with optional ANN retrieval rank.")
    config = load_config(args.config)

    pairs_path = require_file(resolve_path(config, config["inputs"]["ground_truth_pairs"]), "ground-truth pairs")
    embeddings_path = require_file(resolve_path(config, config["inputs"]["embeddings_npz"]), "embedding npz")
    ann_path = resolve_path(config, config["inputs"].get("ann_results", ""))
    output_path = ensure_parent(resolve_path(config, config["outputs"]["rank_comparison"]))

    ids, vectors = load_embeddings(embeddings_path)
    id_to_idx = {column_id: idx for idx, column_id in enumerate(ids)}
    ann_available = ann_path.exists()
    ann_results = load_ann_results(ann_path)

    pairs = read_dicts(pairs_path)
    pairs_by_query = defaultdict(list)
    rows = []
    for idx, pair in enumerate(pairs):
        row = {
            "pair_id": pair.get("pair_id", ""),
            "query_column_id": pair.get("query_column_id", ""),
            "candidate_column_id": pair.get("candidate_column_id", ""),
        }
        rows.append(row)
        pairs_by_query[row["query_column_id"]].append(idx)

    query_ids = list(pairs_by_query)
    batch_size = int(config.get("options", {}).get("rank_batch_size", 256))
    for start in range(0, len(query_ids), batch_size):
        batch_query_ids = query_ids[start : start + batch_size]
        valid_query_ids = [qid for qid in batch_query_ids if qid in id_to_idx]
        if not valid_query_ids:
            mark_missing_queries(rows, pairs_by_query, batch_query_ids)
            continue

        q_idx = np.array([id_to_idx[qid] for qid in valid_query_ids], dtype=np.int64)
        sims = vectors[q_idx] @ vectors.T

        for local_idx, query_id in enumerate(valid_query_ids):
            sim_row = sims[local_idx]
            self_idx = id_to_idx[query_id]
            for row_idx in pairs_by_query[query_id]:
                row = rows[row_idx]
                try:
                    candidate_id = row["candidate_column_id"]
                    if candidate_id not in id_to_idx:
                        raise KeyError("candidate column id not found in embeddings")
                    candidate_idx = id_to_idx[candidate_id]
                    target_sim = float(sim_row[candidate_idx])
                    exact_rank_value = int(np.sum(sim_row > target_sim))
                    if sim_row[self_idx] > target_sim:
                        exact_rank_value -= 1
                    exact_rank_value += 1

                    ann = ann_results.get(query_id, {}).get(candidate_id)
                    ann_rank = ann["rank"] if ann else ""
                    row.update(
                        {
                            "exact_rank": exact_rank_value,
                            "exact_similarity": target_sim,
                            "found_in_ann": "true" if ann else ("false" if ann_available else ""),
                            "ann_rank": ann_rank,
                            "ann_score": ann["score"] if ann else "",
                            "rank_gap": int(ann_rank) - int(exact_rank_value) if ann_rank != "" else "",
                            "status": "ok",
                            "error": "",
                        }
                    )
                except Exception as exc:
                    mark_error(row, exc)

        missing_query_ids = set(batch_query_ids) - set(valid_query_ids)
        mark_missing_queries(rows, pairs_by_query, missing_query_ids)
        print(f"ranked queries {min(start + batch_size, len(query_ids))}/{len(query_ids)}")

    write_dicts(output_path, rows, RANK_FIELDS)
    print(f"Wrote {len(rows)} rank comparison rows to {output_path}")


def mark_missing_queries(rows, pairs_by_query, query_ids):
    for query_id in query_ids:
        for row_idx in pairs_by_query[query_id]:
            mark_error(rows[row_idx], KeyError("query column id not found in embeddings"))


def mark_error(row, exc):
    row.update({field: "" for field in RANK_FIELDS if field not in row})
    row["status"] = "error"
    row["error"] = str(exc)


if __name__ == "__main__":
    main()
