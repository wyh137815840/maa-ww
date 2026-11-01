#!/usr/bin/env python3
"""From Terminal (or reopen): tap 索拉指南 (634,500) → rail#2 → try reach 无音清剿."""
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
from tacet_select_proto import find_go_buttons

ROOT = Path(__file__).resolve().parents[2]
CALIB = ROOT / "docs/zh_cn/odin-nav-calib.json"
OUT = ROOT / "review/inbox"


def snap(cfg, label):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = OUT / f"{stamp}-{label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], dest, cfg), dest.name)
    return dest


def main():
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    dw, dh = raw_screen_size(cfg["adb_path"], cfg["serial"])

    def tap(x, y, wait=1.3):
        print(" tap", (x, y), "->", tap720(cfg["adb_path"], cfg["serial"], x, y, dw, dh))
        time.sleep(wait)

    path = snap(cfg, "odin-pre-sola")
    # ensure terminal
    im = Image.open(path).convert("RGB")
    dark_attack = sum(1 for y in range(560, 680, 4) for x in range(1080, 1200, 4) if sum(im.getpixel((x, y))) < 80)
    if dark_attack > 40:
        print("reopen terminal")
        tap(1198, 38, wait=1.4)
        path = snap(cfg, "odin-term2")

    tap(634, 500, wait=1.6)
    path = snap(cfg, "odin-sola-634-500")
    im = Image.open(path).convert("RGB")
    print("after sola btns", find_go_buttons(im))

    # dismiss tip popup
    tap(900, 200, wait=0.5)
    path = snap(cfg, "odin-sola-ready")

    # rail #2
    for xy in [(155, 266), (180, 266), (155, 240)]:
        tap(*xy)
        path = snap(cfg, f"odin-rail-{xy[0]}-{xy[1]}")
        im = Image.open(path).convert("RGB")
        btns = find_go_buttons(im)
        print(" rail", xy, "btns", btns)
        if len(btns) >= 3:
            break

    # if 素材获取 style left tabs, click 无音清剿
    for xy in [(183, 531), (180, 500), (180, 560), (200, 480), (180, 450)]:
        im = Image.open(path).convert("RGB")
        if len(find_go_buttons(im)) >= 3:
            break
        tap(*xy)
        path = snap(cfg, f"odin-tacettab-{xy[0]}-{xy[1]}")
        print(" tacet try", xy, find_go_buttons(Image.open(path).convert("RGB")))

    im = Image.open(path).convert("RGB")
    btns = find_go_buttons(im)
    out = {
        "device_raw": [dw, dh],
        "serial": cfg["serial"],
        "coords_720p": {
            "terminal_menu": [1198, 38],
            "sola_guidebook_tile": [634, 500],
            "rail2_candidates": [[155, 266], [180, 266]],
            "wrong_980_40": "唤取",
        },
        "final": {"file": path.name, "buttons": btns, "ok": len(btns) >= 3},
        "scale_note": "tap720 maps to device; MaaFramework SetScreenshotTargetLongSide(1280) for runtime",
    }
    CALIB.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["final"]["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
