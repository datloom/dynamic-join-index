import csv
from pathlib import Path


def read_dicts(path):
    with Path(path).open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_dicts(path, rows, fieldnames):
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def read_csv_rows(path, encoding=None):
    encodings = [encoding] if encoding else ["utf-8-sig", "utf-8", "ISO-8859-1"]
    last_error = None
    for enc in encodings:
        try:
            with Path(path).open("r", encoding=enc, newline="") as f:
                return list(csv.reader(f))
        except UnicodeDecodeError as exc:
            last_error = exc
    raise last_error

