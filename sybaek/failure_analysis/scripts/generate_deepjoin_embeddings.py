#!/usr/bin/env python3
import csv
import sys
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from sybaek.failure_analysis.src.columns import load_column_values
from sybaek.failure_analysis.src.config import ensure_parent, load_config, parse_args, require_file, resolve_path
from sybaek.failure_analysis.src.csv_utils import read_dicts


DEFAULT_MODEL = "datasets/LakeBench/join/Deepjoin/output/deepjoin_webtable_training-all-mpnet-base-v2-2023-10-18_19-54-27"


def main():
    args = parse_args("Generate DeepJoin-style column embeddings from column_manifest.csv.")
    config = load_config(args.config)
    manifest_path = require_file(resolve_path(config, config["inputs"]["column_manifest"]), "column manifest")
    output_path = ensure_parent(resolve_path(config, config["inputs"]["embeddings_npz"]))
    model_path = resolve_path(config, config.get("deepjoin_model", DEFAULT_MODEL))
    options = config.get("options", {})

    rows = read_dicts(manifest_path)
    ids = []
    texts = []
    for i, row in enumerate(rows, 1):
        table_path = require_file(resolve_path(config, row["table_path"]), f"table for {row['column_id']}")
        _, values = load_column_values(
            table_path,
            column_name=row.get("column_name"),
            column_index=row.get("column_index"),
            max_rows=options.get("max_rows_per_table"),
            encoding=options.get("encoding"),
        )
        ids.append(row["column_id"])
        texts.append(column_to_text(row.get("column_name", ""), values))
        if i % 1000 == 0:
            print(f"prepared {i}/{len(rows)} columns")

    print(f"loading model: {model_path}")
    model = SentenceTransformer(str(model_path))
    vectors = model.encode(
        texts,
        batch_size=int(options.get("embedding_batch_size", 64)),
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype(np.float32)

    np.savez_compressed(output_path, ids=np.array(ids), vectors=vectors)
    print(f"wrote embeddings: {output_path} shape={vectors.shape}")


def column_to_text(column_name, values):
    cleaned = []
    seen = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
        if len(cleaned) >= 128:
            break
    return " ".join([str(column_name).strip(), *cleaned])


if __name__ == "__main__":
    main()

