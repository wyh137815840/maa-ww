#!/usr/bin/env python3
"""Odin: calibrate 大世界 → 索拉指南 → 左侧第2栏 → 无音清剿 (720p coords, scaled taps)."""
from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture import capture_png, ensure_device  # noqa: E402
from common import load_config  # noqa: E402
from device_geom import raw_screen_size, tap720  # noqa: E402
from tacet_select_proto import find_go_buttons  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "review/inbox"
CALIB = ROOT / "docs/zh_cn/odin-nav-calib.json"


def snap(cfg, label: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = OUT / f"{stamp}-{label}.png"
    tag = capture_png(cfg["adb_path"], cfg["serial"], dest, cfg)
    print(f"  snap {dest.name} ({tag})")
    return dest


def annotate_top(path: Path, marks: list[tuple[int, int, str]]) -> None:
    im = Image.open(path).convert("RGB")
    dr = ImageDraw.Draw(im)
    for x, y, name in marks:
        dr.ellipse((x - 8, y - 8, x + 8, y + 8), outline=(255, 40, 40), width=2)
        dr.text((x - 20, y + 12), name, fill=(255, 60, 60))
    crop = im.crop((900, 0, 1280, 120))
    out = ROOT / "tools/touch-review/_scrollbar_calib" / f"hud_{path.stem}.png"
    crop.resize((crop.width * 2, crop.height * 2)).save(out)
    print("  wrote", out.name)


def has_gold_claim(im: Image.Image) -> bool:
    n = 0
    for y in range(180, 360):
        for x in range(1000, 1220):
            r, g, b = im.getpixel((x, y))
            if r > 160 and g > 120 and b < 120 and (r - b) > 60:
                n += 1
                if n > 40:
                    return True
    return False


def looks_guidebook_sidebar(im: Image.Image) -> bool:
    """Left rail of 索拉指南: dark panel with icons."""
    dark = 0
    for y in range(120, 600, 8):
        for x in range(80, 160, 4):
            if sum(im.getpixel((x, y))) < 90:
                dark += 1
    return dark > 80


def looks_tacet(im: Image.Image) -> bool:
    if has_gold_claim(im):
        return False
    btns = find_go_buttons(im)
    if len(btns) < 3:
        return False
    # 合鸣 filter / list: dark pills
    dark = sum(1 for cx, cy in btns if sum(im.getpixel((cx, cy))) < 200)
    return dark >= 3


def main() -> int:
    import argparse
    import json

    ap = argparse.ArgumentParser()
    ap.add_argument("--step", choices=["hud", "open", "rail2", "tacet", "all"], default="all")
    args = ap.parse_args()

    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    dw, dh = raw_screen_size(cfg["adb_path"], cfg["serial"])
    print(f"device={cfg['serial']} raw={dw}x{dh} (taps scaled from 1280x720)")

    result = {"device_raw": [dw, dh], "serial": cfg["serial"], "coords_720p": {}}

    def tap(x, y, wait=1.2):
        dx, dy = tap720(cfg["adb_path"], cfg["serial"], x, y, dw, dh)
        print(f"  tap720 ({x},{y}) -> device ({dx},{dy})")
        time.sleep(wait)

    path = snap(cfg, "odin-nav-start")
    im = Image.open(path).convert("RGB")
    # Candidate top-right HUD icons @720p (guess grid)
    candidates = [
        (1050, 40, "a"),
        (1100, 40, "b"),
        (1150, 40, "c"),
        (1198, 38, "oldOpenGB"),
        (1240, 40, "menu"),
    ]
    annotate_top(path, [(x, y, n) for x, y, n in candidates])

    if args.step in ("hud",):
        print("HUD only; inspect hud_*.png then rerun --step open")
        return 0

    if args.step in ("open", "all"):
        # Prefer ESC/Terminal then 索拉指南 (stable on mobile)
        print("open Terminal/menu (1240,40)")
        tap(1240, 40, wait=1.3)
        path = snap(cfg, "odin-after-menu")
        im = Image.open(path).convert("RGB")
        # Terminal grid 索拉指南 ~ (700,505) @720p from earlier LD calib; try nearby
        for xy in [(700, 505), (720, 520), (680, 500), (760, 500)]:
            print("try 索拉指南", xy)
            tap(xy[0], xy[1], wait=1.4)
            path = snap(cfg, f"odin-gb-{xy[0]}-{xy[1]}")
            im = Image.open(path).convert("RGB")
            ok = looks_guidebook_sidebar(im)
            print("  guidebook_sidebar", ok, "gold", has_gold_claim(im), "btns", find_go_buttons(im))
            if ok or has_gold_claim(im) or looks_tacet(im):
                result["coords_720p"]["open_guidebook"] = {"via": "terminal", "tap": list(xy)}
                break
        else:
            print("WARN: guidebook open uncertain")

    if args.step in ("rail2", "all"):
        path = snap(cfg, "odin-before-rail2")
        im = Image.open(path).convert("RGB")
        # 2nd left-rail icon ~ y=266 @720p (from LD peak); x~155
        for xy in [(155, 266), (180, 266), (155, 250), (155, 280)]:
            print("try rail#2", xy)
            tap(xy[0], xy[1], wait=1.4)
            path = snap(cfg, f"odin-rail2-{xy[0]}-{xy[1]}")
            im = Image.open(path).convert("RGB")
            print("  gold", has_gold_claim(im), "tacet", looks_tacet(im), "btns", find_go_buttons(im))
            if looks_tacet(im) or (not has_gold_claim(im) and len(find_go_buttons(im)) >= 1):
                result["coords_720p"]["rail2"] = list(xy)
                # if popup, dismiss
                if looks_guidebook_sidebar(im) and not looks_tacet(im):
                    tap(640, 360, wait=0.8)
                break

    if args.step in ("tacet", "all"):
        if not looks_tacet(Image.open(path).convert("RGB")):
            for xy in [(183, 531), (180, 500), (180, 560), (200, 480)]:
                print("try TacetTab", xy)
                tap(xy[0], xy[1], wait=1.3)
                path = snap(cfg, f"odin-tacet-{xy[0]}-{xy[1]}")
                im = Image.open(path).convert("RGB")
                print("  tacet", looks_tacet(im), "btns", find_go_buttons(im))
                if looks_tacet(im):
                    result["coords_720p"]["tacet_tab"] = list(xy)
                    break

    im = Image.open(path).convert("RGB")
    result["final"] = {
        "file": path.name,
        "tacet_list": looks_tacet(im),
        "buttons": find_go_buttons(im),
        "gold_claim": has_gold_claim(im),
    }
    CALIB.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", CALIB)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["final"]["tacet_list"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
