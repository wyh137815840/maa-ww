"""Machine-local secrets for tools (device lock PIN, serial, internal hosts).

Source of truth: tools/touch-review/config.json (git-ignored; copy from config.example.json).
Environment overrides: ODIN_PIN, ANDROID_SERIAL, REF_GIT_BASE.
Never hard-code these values in scripts, docs, tests or pipelines.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

_CFG = Path(__file__).resolve().parent / "touch-review" / "config.json"


def _load() -> dict:
    try:
        return json.loads(_CFG.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def pin() -> str:
    """Device lock-screen PIN. Empty string = do not type a PIN."""
    return os.environ.get("ODIN_PIN") or str(_load().get("pin", ""))


def serial() -> str:
    return os.environ.get("ANDROID_SERIAL") or str(_load().get("serial", ""))


def ref_git_base() -> str:
    return os.environ.get("REF_GIT_BASE") or str(_load().get("ref_git_base", ""))
