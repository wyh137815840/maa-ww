from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = Path(__file__).resolve().parent / "config.json"


def load_config() -> dict:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    cfg["inbox_dir"] = (ROOT / cfg["inbox_dir"]).resolve()
    cfg["cards_dir"] = (ROOT / cfg["cards_dir"]).resolve()
    cfg["inbox_dir"].mkdir(parents=True, exist_ok=True)
    cfg["cards_dir"].mkdir(parents=True, exist_ok=True)
    return cfg
