#!/usr/bin/env python3
"""One-step App UI navigator for solid verify (no game taps)."""
from __future__ import annotations

import argparse
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

PKG = "com.aliothmoon.maafw.maaww"
OUT = ROOT / "review/inbox"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tap", nargs=2, type=int, metavar=("X", "Y"))
    ap.add_argument("--label", default="step")
    ap.add_argument("--launch", action="store_true")
    ap.add_argument("--wait", type=float, default=1.0)
    args = ap.parse_args()

    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    dw, dh = raw_screen_size(cfg["adb_path"], cfg["serial"])
    if args.launch:
        subprocess.run(
            [
                cfg["adb_path"],
                "-s",
                cfg["serial"],
                "shell",
                "monkey",
                "-p",
                PKG,
                "-c",
                "android.intent.category.LAUNCHER",
                "1",
            ],
            capture_output=True,
        )
        time.sleep(1.5)
    if args.tap:
        print(
            "tap",
            args.tap,
            tap720(cfg["adb_path"], cfg["serial"], args.tap[0], args.tap[1], dw, dh),
        )
        time.sleep(args.wait)
    p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-n-{args.label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
