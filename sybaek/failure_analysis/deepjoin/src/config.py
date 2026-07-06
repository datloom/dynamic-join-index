import argparse
import json
from pathlib import Path


DEFAULT_CONFIG = "sybaek/failure_analysis/deepjoin/configs/deepjoin_failure_analysis.json"


def parse_args(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Path to JSON config.")
    return parser.parse_args()


def load_config(path):
    config_path = Path(path).resolve()
    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)

    repo_root = Path(config.get("repo_root", "."))
    if not repo_root.is_absolute():
        repo_root = _find_repo_root(config_path.parent) / repo_root
        repo_root = repo_root.resolve()

    config["repo_root"] = str(repo_root)
    return config


def resolve_path(config, value):
    path = Path(value)
    if path.is_absolute():
        return path
    return Path(config["repo_root"]) / path


def require_file(path, label):
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {label}: {path}\n"
            "Create the input file or update the config before running this step."
        )
    return path


def ensure_parent(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _find_repo_root(start):
    current = Path(start).resolve()
    for path in [current, *current.parents]:
        if (path / ".git").exists():
            return path
    return Path.cwd().resolve()
