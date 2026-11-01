#!/usr/bin/env python3
"""Tap a UI node by text/desc using uiautomator dump (device raw → 720 coords)."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
from capture import capture_png, ensure_device
from common import load_config
from device_geom import raw_screen_size, tap720

OUT = ROOT / "review/inbox"


def dump_nodes(adb: str, serial: str) -> list[dict]:
    subprocess.run(
        [adb, "-s", serial, "shell", "uiautomator", "dump", "/sdcard/uidump.xml"],
        capture_output=True,
    )
    p = OUT / "_uidump.xml"
    subprocess.run([adb, "-s", serial, "pull", "/sdcard/uidump.xml", str(p)], capture_output=True)
    text = p.read_text(encoding="utf-8", errors="ignore")
    nodes = []
    for m in re.finditer(r"<node\b([^>]*)/>", text):
        attrs = m.group(1)
        text_m = re.search(r'\btext="([^"]*)"', attrs)
        desc_m = re.search(r'\bcontent-desc="([^"]*)"', attrs)
        bound_m = re.search(r'\bbounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', attrs)
        if not bound_m:
            continue
        t = text_m.group(1) if text_m else ""
        d = desc_m.group(1) if desc_m else ""
        x1, y1, x2, y2 = map(int, bound_m.groups())
        nodes.append({"text": t, "desc": d, "bounds": (x1, y1, x2, y2)})
    return nodes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True, help="Exact text or content-desc to tap")
    ap.add_argument("--label", default="tap")
    ap.add_argument("--wait", type=float, default=1.2)
    ap.add_argument("--contains", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    dw, dh = raw_screen_size(cfg["adb_path"], cfg["serial"])
    nodes = dump_nodes(cfg["adb_path"], cfg["serial"])
    hit = None
    for n in nodes:
        vals = (n["text"], n["desc"])
        if args.contains:
            if any(args.text in v for v in vals if v):
                hit = n
                break
        else:
            if args.text in vals:
                hit = n
                break
    if not hit:
        print("NOT_FOUND", args.text)
        for n in nodes:
            if n["text"] or n["desc"]:
                print(n)
        return 2
    x1, y1, x2, y2 = hit["bounds"]
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    x720 = int(cx * 1280 / dw)
    y720 = int(cy * 720 / dh)
    print("hit", hit, "→720", (x720, y720))
    print(tap720(cfg["adb_path"], cfg["serial"], x720, y720, dw, dh))
    time.sleep(args.wait)
    p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-n-{args.label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
