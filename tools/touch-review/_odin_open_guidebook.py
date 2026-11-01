#!/usr/bin/env python3
"""Odin: tap top-bar book icon (索拉指南) then left-rail #2; save calib."""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture import capture_png, ensure_device
from common import load_config
from device_geom import raw_screen_size, tap720
from tacet_select_proto import find_go_buttons

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "review/inbox"
CALIB = ROOT / "docs/zh_cn/odin-nav-calib.json"


def snap(cfg, label):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = OUT / f"{stamp}-{label}.png"
    print(" ", capture_png(cfg["adb_path"], cfg["serial"], dest, cfg), dest.name)
    return dest


def main():
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    dw, dh = raw_screen_size(cfg["adb_path"], cfg["serial"])
    print(f"raw={dw}x{dh}")

    def tap(x, y, wait=1.3):
        dx, dy = tap720(cfg["adb_path"], cfg["serial"], x, y, dw, dh)
        print(f"  tap720 ({x},{y}) -> ({dx},{dy})")
        time.sleep(wait)

    path = snap(cfg, "odin-gb-start")
    # Book icon left of top-right cluster (~980–1020, 40) from HUD crop
    book_tries = [(980, 40), (1000, 38), (1020, 40), (960, 40), (1040, 40)]
    opened = None
    for xy in book_tries:
        tap(*xy)
        path = snap(cfg, f"odin-book-{xy[0]}-{xy[1]}")
        im = Image.open(path).convert("RGB")
        # Guidebook: left dark rail OR activity title area change (not overworld attack button)
        # Heuristic: overworld has big dark attack pill bottom-right; guidebook usually doesn't
        attack_zone = sum(im.getpixel((1140, 620))) < 100
        left_dark = sum(1 for y in range(150, 500, 10) for x in range(90, 150, 5) if sum(im.getpixel((x, y))) < 100)
        print(f"  attack_darkish={attack_zone} left_dark_n={left_dark} btns={find_go_buttons(im)}")
        if left_dark > 40 or (not attack_zone and left_dark > 20):
            opened = xy
            print("  OPENED guidebook-like UI")
            break

    if not opened:
        # Fallback: Terminal star then 索拉指南 tile
        print("fallback Terminal")
        tap(1198, 38)
        path = snap(cfg, "odin-term")
        for xy in [(700, 505), (640, 500), (760, 520)]:
            tap(*xy)
            path = snap(cfg, f"odin-term-gb-{xy[0]}")
            im = Image.open(path).convert("RGB")
            left_dark = sum(1 for y in range(150, 500, 10) for x in range(90, 150, 5) if sum(im.getpixel((x, y))) < 100)
            print("  left_dark", left_dark)
            if left_dark > 40:
                opened = ("terminal", xy)
                break

    if not opened:
        print("FAILED open guidebook")
        return 2

    # dismiss popup if any
    tap(640, 360, wait=0.6)
    path = snap(cfg, "odin-gb-ready")

    # rail #2
    rail = None
    for xy in [(155, 266), (180, 266), (155, 240), (155, 290), (140, 266)]:
        tap(*xy)
        path = snap(cfg, f"odin-r2-{xy[0]}-{xy[1]}")
        im = Image.open(path).convert("RGB")
        btns = find_go_buttons(im)
        print(f"  rail {xy} btns={btns}")
        if len(btns) >= 3:
            rail = xy
            break

    # tacet subtab if needed
    tacet = None
    im = Image.open(path).convert("RGB")
    if len(find_go_buttons(im)) < 3:
        for xy in [(183, 531), (180, 500), (200, 520)]:
            tap(*xy)
            path = snap(cfg, f"odin-tt-{xy[0]}-{xy[1]}")
            im = Image.open(path).convert("RGB")
            btns = find_go_buttons(im)
            print(f"  tacet {xy} btns={btns}")
            if len(btns) >= 3:
                tacet = xy
                break

    im = Image.open(path).convert("RGB")
    btns = find_go_buttons(im)
    # annotate final
    vis = im.copy()
    dr = ImageDraw.Draw(vis)
    for cx, cy in btns:
        dr.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), outline=(0, 255, 80), width=2)
    vis.save(ROOT / "tools/touch-review/_scrollbar_calib/odin_final_list.png")

    out = {
        "device_raw": [dw, dh],
        "serial": cfg["serial"],
        "coords_720p": {
            "guidebook_book_icon": list(opened) if isinstance(opened, tuple) and not isinstance(opened[0], str) else opened,
            "rail2": list(rail) if rail else None,
            "tacet_tab": list(tacet) if tacet else None,
        },
        "final": {"file": path.name, "buttons": btns, "ok": len(btns) >= 3},
        "note": "720p coords; tap via device_geom.tap720. Book icon is leftmost top-right HUD cluster.",
    }
    CALIB.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print("wrote", CALIB)
    return 0 if out["final"]["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
