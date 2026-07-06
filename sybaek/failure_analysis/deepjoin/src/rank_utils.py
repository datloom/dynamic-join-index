import csv
from collections import defaultdict
from pathlib import Path

import numpy as np


def load_embeddings(path):
    data = np.load(path, allow_pickle=False)
    ids = [str(value) for value in data["ids"]]
    vectors = np.asarray(data["vectors"], dtype=np.float32)
    if vectors.ndim != 2:
        raise ValueError("embeddings_npz['vectors'] must be a 2D array.")
    if len(ids) != vectors.shape[0]:
        raise ValueError("embeddings_npz ids length does not match vectors row count.")
    return ids, _l2_normalize(vectors)


def exact_rank(query_id, candidate_id, ids, vectors, id_to_idx):
    if query_id not in id_to_idx or candidate_id not in id_to_idx:
        return None, None

    q_idx = id_to_idx[query_id]
    c_idx = id_to_idx[candidate_id]
    sims = vectors @ vectors[q_idx]
    target_sim = float(sims[c_idx])

    exclude = {q_idx}
    better = 0
    for idx, sim in enumerate(sims):
        if idx in exclude:
            continue
        if sim > target_sim:
            better += 1
    return better + 1, target_sim


def load_ann_results(path):
    if path is None or not Path(path).exists():
        return {}

    by_query = defaultdict(dict)
    order = defaultdict(int)
    with Path(path).open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"query_column_id", "candidate_column_id"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"ANN result file missing columns: {sorted(missing)}")

        for row in reader:
            query_id = row["query_column_id"]
            candidate_id = row["candidate_column_id"]
            order[query_id] += 1
            rank = row.get("rank") or order[query_id]
            score = row.get("score", "")
            by_query[query_id][candidate_id] = {"rank": int(rank), "score": score}
    return by_query


def _l2_normalize(vectors):
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms

