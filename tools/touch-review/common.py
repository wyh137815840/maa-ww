from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
EXAMPLE_PATH = CONFIG_PATH.with_name("config.example.json")


def load_config() -> dict:
    # config.json is machine-local and git-ignored (PIN / serial); fall back to the example.
    path = CONFIG_PATH if CONFIG_PATH.exists() else EXAMPLE_PATH
    cfg = json.loads(path.read_text(encoding="utf-8"))
    cfg["inbox_dir"] = (ROOT / cfg["inbox_dir"]).resolve()
    cfg["cards_dir"] = (ROOT / cfg["cards_dir"]).resolve()
    cfg["inbox_dir"].mkdir(parents=True, exist_ok=True)
    cfg["cards_dir"].mkdir(parents=True, exist_ok=True)
    return cfg
