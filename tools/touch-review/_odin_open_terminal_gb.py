#!/usr/bin/env python3
"""Close mis-opened UI → open Terminal → tap 索拉指南; record 720p coords."""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture import capture_png, ensure_device
from common import load_config
from device_geom import adb_run, raw_screen_size, tap720

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "review/inbox"
CALIB = ROOT / "docs/zh_cn/odin-nav-calib.json"


def snap(cfg, label):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = OUT / f"{stamp}-{label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], dest, cfg), dest.name)
    return dest


def main():
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    dw, dh = raw_screen_size(cfg["adb_path"], cfg["serial"])

    def tap(x, y, wait=1.2):
        print(" tap720", (x, y), "->", tap720(cfg["adb_path"], cfg["serial"], x, y, dw, dh))
        time.sleep(wait)

    # Back out of 唤取 if open
    for _ in range(3):
        adb_run(cfg["adb_path"], cfg["serial"], "shell", "input", "keyevent", "4", check=False)
        time.sleep(0.6)
    path = snap(cfg, "odin-after-back")

    # Terminal / 更多 star (rightmost HUD)
    term = None
    for xy in [(1198, 38), (1220, 42), (1170, 40), (1240, 45)]:
        tap(*xy, wait=1.4)
        path = snap(cfg, f"odin-menu-{xy[0]}-{xy[1]}")
        im = Image.open(path).convert("RGB")
        # Terminal has profile left + icon grid; sample center-right brightness variance
        # Simple: not overworld if attack button area is bright/missing dark sword
        dark_attack = sum(1 for y in range(560, 680, 4) for x in range(1080, 1200, 4) if sum(im.getpixel((x, y))) < 80)
        print("  dark_attack_n", dark_attack)
        if dark_attack < 30:
            term = xy
            print("  MENU likely open")
            break

    if not term:
        print("Terminal not opened; leave calib partial")
        CALIB.write_text(
            json.dumps(
                {
                    "device_raw": [dw, dh],
                    "serial": cfg["serial"],
                    "status": "partial",
                    "findings": {
                        "980_40": "opens 唤取 NOT 索拉指南",
                        "need": "Terminal → 索拉指南 tile, or correct top-bar icon for 索拉指南",
                    },
                    "final_file": path.name,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return 2

    # 索拉指南 on terminal grid (bottom-left of 3x4)
    gb = None
    for xy in [(700, 505), (680, 510), (720, 500), (640, 500), (760, 520)]:
        tap(*xy, wait=1.5)
        path = snap(cfg, f"odin-sola-{xy[0]}-{xy[1]}")
        im = Image.open(path).convert("RGB")
        left_dark = sum(1 for y in range(120, 560, 8) for x in range(70, 160, 4) if sum(im.getpixel((x, y))) < 90)
        print("  left_dark", left_dark, "file", path.name)
        if left_dark > 50:
            gb = xy
            print("  索拉指南 open")
            break

    out = {
        "device_raw": [dw, dh],
        "serial": cfg["serial"],
        "coords_720p": {
            "terminal_menu": list(term) if term else None,
            "sola_guidebook_tile": list(gb) if gb else None,
            "wrong_980_40": "唤取",
        },
        "final_file": path.name,
        "ok": bool(gb),
    }
    CALIB.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if gb else 2


if __name__ == "__main__":
    raise SystemExit(main())
