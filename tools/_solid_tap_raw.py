#!/usr/bin/env python3
"""Tap using uiautomator raw bounds center (ignore 720 remap)."""
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

OUT = ROOT / "review/inbox"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--contains", action="store_true")
    ap.add_argument("--label", default="raw")
    ap.add_argument("--wait", type=float, default=1.5)
    ap.add_argument("--button-parent", action="store_true", help="If text hit, tap empty Button near same Y")
    args = ap.parse_args()

    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    adb, s = cfg["adb_path"], cfg["serial"]

    # diagnose size
    for cmd in (
        ["shell", "wm", "size"],
        ["shell", "wm", "density"],
        ["shell", "dumpsys", "window", "displays"],
    ):
        r = subprocess.run([adb, "-s", s, *cmd], capture_output=True, text=True, encoding="utf-8", errors="ignore")
        out = (r.stdout or "")[:500]
        print("CMD", " ".join(cmd), "→", out.replace("\n", " | ")[:400])

    subprocess.run([adb, "-s", s, "shell", "uiautomator", "dump", "/sdcard/uidump.xml"], capture_output=True)
    p = OUT / "_uidump.xml"
    subprocess.run([adb, "-s", s, "pull", "/sdcard/uidump.xml", str(p)], capture_output=True)
    text = p.read_text(encoding="utf-8", errors="ignore")
    nodes = []
    for m in re.finditer(r"<node\b([^>]*)/>", text):
        attrs = m.group(1)
        text_m = re.search(r'\btext="([^"]*)"', attrs)
        desc_m = re.search(r'\bcontent-desc="([^"]*)"', attrs)
        bound_m = re.search(r'\bbounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', attrs)
        class_m = re.search(r'\bclass="([^"]*)"', attrs)
        if not bound_m:
            continue
        nodes.append(
            {
                "text": text_m.group(1) if text_m else "",
                "desc": desc_m.group(1) if desc_m else "",
                "bounds": tuple(map(int, bound_m.groups())),
                "class": (class_m.group(1) if class_m else "").split(".")[-1],
            }
        )

    hit = None
    for n in nodes:
        vals = (n["text"], n["desc"])
        ok = any(args.text in v for v in vals if v) if args.contains else args.text in vals
        if ok:
            hit = n
            break
    if not hit:
        print("NOT_FOUND", args.text)
        return 2

    x1, y1, x2, y2 = hit["bounds"]
    if args.button_parent:
        cy = (y1 + y2) // 2
        for n in nodes:
            if n["class"] == "Button":
                bx1, by1, bx2, by2 = n["bounds"]
                if by1 <= cy <= by2 and (bx2 - bx1) > 400:
                    x1, y1, x2, y2 = n["bounds"]
                    hit = n
                    break

    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    print("tap raw", hit, "→", (cx, cy))
    subprocess.run([adb, "-s", s, "shell", "input", "tap", str(cx), str(cy)], capture_output=True)
    time.sleep(args.wait)
    out = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-n-{args.label}.png"
    print(capture_png(adb, s, out, cfg), out.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
