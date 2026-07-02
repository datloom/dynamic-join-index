import math
import re
from collections import Counter

from .csv_utils import read_csv_rows


DATE_LIKE = re.compile(
    r"^\s*(\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})\s*$"
)
NUMERIC = re.compile(r"^\s*[-+]?\d{1,3}(,\d{3})*(\.\d+)?\s*$|^\s*[-+]?\d+(\.\d+)?\s*$")
ALPHA = re.compile(r"[A-Za-z]")


def normalize_value(value):
    return str(value).strip()


def load_column_values(table_path, column_name=None, column_index=None, max_rows=None, encoding=None):
    rows = read_csv_rows(table_path, encoding=encoding)
    if not rows:
        return "", []

    header = rows[0]
    index = _resolve_column_index(header, column_name, column_index)
    values = []

    for row in rows[1:]:
        if max_rows is not None and len(values) >= max_rows:
            break
        values.append(row[index] if index < len(row) else "")

    resolved_name = header[index] if index < len(header) else str(column_name or column_index)
    return resolved_name, values


def profile_values(values):
    cleaned = [normalize_value(value) for value in values]
    row_count = len(cleaned)
    non_null = [value for value in cleaned if value != ""]
    null_count = row_count - len(non_null)
    counts = Counter(non_null)
    unique_count = len(counts)

    if row_count == 0:
        return _empty_profile()

    top_counts = sorted(counts.values(), reverse=True)
    duplicate_count = max(0, len(non_null) - unique_count)
    lengths = [len(value) for value in non_null]

    return {
        "row_count": row_count,
        "non_null_count": len(non_null),
        "null_count": null_count,
        "unique_count": unique_count,
        "duplicate_ratio": _safe_div(duplicate_count, len(non_null)),
        "null_ratio": _safe_div(null_count, row_count),
        "cardinality_ratio": _safe_div(unique_count, len(non_null)),
        "avg_length": _safe_div(sum(lengths), len(lengths)),
        "numeric_ratio": _safe_div(sum(1 for value in non_null if NUMERIC.match(value)), len(non_null)),
        "date_like_ratio": _safe_div(sum(1 for value in non_null if DATE_LIKE.match(value)), len(non_null)),
        "alpha_ratio": _safe_div(sum(1 for value in non_null if ALPHA.search(value)), len(non_null)),
        "entropy": _entropy(counts, len(non_null)),
        "top1_frequency": _safe_div(top_counts[0], len(non_null)) if top_counts else 0.0,
        "top5_frequency": _safe_div(sum(top_counts[:5]), len(non_null)) if top_counts else 0.0,
    }


def value_set(values):
    return {normalize_value(value).lower() for value in values if normalize_value(value) != ""}


def _resolve_column_index(header, column_name, column_index):
    if column_index not in (None, ""):
        return int(column_index)
    if column_name not in (None, ""):
        for index, name in enumerate(header):
            if name == column_name:
                return index
        for index, name in enumerate(header):
            if name.strip().lower() == str(column_name).strip().lower():
                return index
        raise ValueError(f"Column name not found: {column_name}")
    raise ValueError("Either column_name or column_index is required.")


def _empty_profile():
    return {
        "row_count": 0,
        "non_null_count": 0,
        "null_count": 0,
        "unique_count": 0,
        "duplicate_ratio": 0.0,
        "null_ratio": 0.0,
        "cardinality_ratio": 0.0,
        "avg_length": 0.0,
        "numeric_ratio": 0.0,
        "date_like_ratio": 0.0,
        "alpha_ratio": 0.0,
        "entropy": 0.0,
        "top1_frequency": 0.0,
        "top5_frequency": 0.0,
    }


def _safe_div(numerator, denominator):
    return float(numerator) / float(denominator) if denominator else 0.0


def _entropy(counts, total):
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in counts.values():
        prob = count / total
        entropy -= prob * math.log2(prob)
    return entropy

