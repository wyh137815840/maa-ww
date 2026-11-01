#!/usr/bin/env python3
"""Dump current App UI nodes (for MaaWW config setup)."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
from common import load_config
from device_geom import raw_screen_size

OUT = ROOT / "review/inbox/_uidump.xml"


def main() -> int:
    cfg = load_config()
    adb, s = cfg["adb_path"], cfg["serial"]
    subprocess.run(
        [adb, "-s", s, "shell", "uiautomator", "dump", "/sdcard/uidump.xml"],
        capture_output=True,
    )
    subprocess.run(
        [adb, "-s", s, "pull", "/sdcard/uidump.xml", str(OUT)],
        capture_output=True,
    )
    text = OUT.read_text(encoding="utf-8", errors="ignore")
    print("len", len(text), "raw", raw_screen_size(adb, s))
    # node attrs can be in any order
    for m in re.finditer(r"<node\b([^>]*)/>", text):
        attrs = m.group(1)
        text_m = re.search(r'\btext="([^"]*)"', attrs)
        desc_m = re.search(r'\bcontent-desc="([^"]*)"', attrs)
        bound_m = re.search(r'\bbounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', attrs)
        click_m = re.search(r'\bclickable="([^"]*)"', attrs)
        if not bound_m:
            continue
        t = text_m.group(1) if text_m else ""
        d = desc_m.group(1) if desc_m else ""
        click = click_m.group(1) if click_m else "?"
        if not t and not d:
            continue
        x1, y1, x2, y2 = map(int, bound_m.groups())
        print(f"click={click} text={t!r} desc={d!r} [{x1},{y1}][{x2},{y2}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
