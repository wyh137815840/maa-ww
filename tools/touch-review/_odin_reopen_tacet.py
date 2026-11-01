#!/usr/bin/env python3
"""Close guidebook if open, reopen Terminal→索拉指南→无音清剿, land on top of list."""
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
from device_geom import raw_screen_size, swipe720, tap720
from tacet_select_proto import detect_thumb, find_go_buttons

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "review/inbox"
CALIB = ROOT / "docs/zh_cn/odin-nav-calib.json"


def snap(cfg, label):
    dest = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], dest, cfg), dest.name)
    return dest


def tap(cfg, x, y, dw, dh, wait=1.0):
    print(" tap", (x, y), "->", tap720(cfg["adb_path"], cfg["serial"], x, y, dw, dh))
    time.sleep(wait)


def main() -> int:
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    dw, dh = raw_screen_size(cfg["adb_path"], cfg["serial"])
    nav = json.loads(CALIB.read_text(encoding="utf-8"))["coords_720p"]

    path = snap(cfg, "reopen-start")
    im = Image.open(path).convert("RGB")
    # close overlays / guidebook
    for _ in range(3):
        if len(find_go_buttons(im)) >= 2:
            # already in material list — close and reopen for clean top
            tap(cfg, 1235, 35, dw, dh, wait=0.8)
            path = snap(cfg, "reopen-closed")
            im = Image.open(path).convert("RGB")
            break
        tap(cfg, 1235, 35, dw, dh, wait=0.7)
        path = snap(cfg, "reopen-close")
        im = Image.open(path).convert("RGB")

    t = nav["terminal_menu"]
    tap(cfg, t[0], t[1], dw, dh, wait=1.3)
    path = snap(cfg, "reopen-terminal")
    # save sola tile region for pipeline template later
    im = Image.open(path).convert("RGB")
    im.crop((480, 380, 780, 620)).save(OUT / "odin-sola-tile-crop.png")
    print("wrote odin-sola-tile-crop.png")

    s = nav["sola_guidebook_tile"]
    tap(cfg, s[0], s[1], dw, dh, wait=1.4)
    path = snap(cfg, "reopen-sola")
    tab = nav["tacet_tab_in_material"]
    tap(cfg, tab[0], tab[1], dw, dh, wait=1.2)
    path = snap(cfg, "reopen-tacet")
    im = Image.open(path).convert("RGB")
    btns = find_go_buttons(im)
    thumb = detect_thumb(im)
    print("btns", btns, "thumb", thumb)
    for i, (_cx, cy) in enumerate(btns[:4]):
        im.crop((280, cy - 40, 720, cy + 25)).save(OUT / f"reopen-name-{i+1}.png")
        print(" name crop", i + 1)
    return 0 if len(btns) >= 3 else 2


if __name__ == "__main__":
    raise SystemExit(main())
