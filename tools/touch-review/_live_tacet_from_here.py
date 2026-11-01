#!/usr/bin/env python3
"""Assume already in 索拉指南 (any tab). Click 无音清剿 then test SelectTacetRow."""
from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture import capture_png, ensure_device  # noqa: E402
from common import load_config  # noqa: E402
from tacet_select_proto import detect_bar_top, find_go_buttons, plan  # noqa: E402

try:
    from _calib_scrollbar3 import detect_thumb
except Exception:
    detect_thumb = None

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "review/inbox"


def adb(cfg, *args, check=True):
    return subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *args],
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )


def tap(cfg, x, y, wait=1.1):
    print(f"  tap ({x},{y})")
    adb(cfg, "shell", "input", "tap", str(x), str(y), check=False)
    time.sleep(wait)


def snap(cfg, label):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = OUT / f"{stamp}-{label}.png"
    tag = capture_png(cfg["adb_path"], cfg["serial"], dest, cfg)
    print(f"  snap {dest.name} ({tag})")
    return dest


def is_tacet_list(im: Image.Image) -> bool:
    """True only for 无音清剿 list — reject 活跃行迹 (yellow 领取) etc."""
    btns = find_go_buttons(im)
    if len(btns) < 3:
        return False
    ys = [b[1] for b in btns]
    if len(ys) >= 2:
        gaps = [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
        med = sorted(gaps)[len(gaps) // 2]
        if not (80 <= med <= 120):
            return False
    # reject 活跃度 / claim gold buttons
    yellow = 0
    for y in range(180, 360):
        for x in range(1000, 1220):
            r, g, b = im.getpixel((x, y))
            if r > 160 and g > 120 and b < 120 and (r - b) > 60:
                yellow += 1
    if yellow > 40:
        return False
    # 无音清剿 title area often has "合鸣" filter near top-right of list
    # require dark pills (直接挑战) not too bright mean
    darkish = 0
    for cx, cy in btns[:4]:
        r, g, b = im.getpixel((cx, cy))
        if r + g + b < 180:
            darkish += 1
    return darkish >= 2


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=int, default=6)
    ap.add_argument("--scroll-only", action="store_true", default=True)
    ap.add_argument("--click", action="store_true", help="also click 直接挑战 after scroll")
    args = ap.parse_args()
    scroll_only = not args.click

    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])

    path = snap(cfg, "tacet-here-start")
    im = Image.open(path).convert("RGB")
    print("start is_tacet", is_tacet_list(im), "btns", find_go_buttons(im))

    if not is_tacet_list(im):
        # Guidebook left sidebar 无音清剿 — pipeline (183,531); also try nearby
        for xy in [(183, 531), (180, 500), (180, 560), (200, 530), (160, 530)]:
            print("try TacetTab", xy)
            tap(cfg, xy[0], xy[1], wait=1.2)
            path = snap(cfg, f"tacet-tab-{xy[0]}-{xy[1]}")
            im = Image.open(path).convert("RGB")
            print("  is_tacet", is_tacet_list(im), "btns", find_go_buttons(im))
            if is_tacet_list(im):
                break

    if not is_tacet_list(im):
        raise SystemExit(f"not on tacet list; see {path}")

    btns = find_go_buttons(im)
    bar_top = detect_bar_top(im)
    thumb = detect_thumb(im) if detect_thumb else None
    print("ON LIST", "bar_top", bar_top, "thumb", thumb, "btns", btns)

    p = plan(args.index, btns, bar_top)
    print("plan", p)
    if not p.get("ok"):
        raise SystemExit(p)

    if p["mode"] == "direct":
        print("direct mode")
        if scroll_only:
            print("scroll-only skip click", p["click"])
            return 0
        cx, cy = p["click"]
        tap(cfg, cx, cy, wait=1.5)
        snap(cfg, f"clicked-idx{args.index}")
        return 0

    sx, sy = p["scrollbar_click"]
    print(f"scrollbar ({sx},{sy})")
    tap(cfg, sx, sy, wait=1.4)
    path2 = snap(cfg, f"scrolled-idx{args.index}")
    im2 = Image.open(path2).convert("RGB")
    btns2 = find_go_buttons(im2)
    thumb2 = detect_thumb(im2) if detect_thumb else None
    print("after scroll btns", btns2, "thumb", thumb2)

    changed = btns2 != btns
    print("list_changed", changed)

    if btns2 and max(b[1] for b in btns2) / 720 < 0.73 and "underscroll_retry_y" in p:
        ry = int(p["underscroll_retry_y"])
        print("nudge", ry)
        tap(cfg, sx, ry, wait=1.2)
        path2 = snap(cfg, f"nudged-idx{args.index}")
        im2 = Image.open(path2).convert("RGB")
        btns2 = find_go_buttons(im2)
        thumb2 = detect_thumb(im2) if detect_thumb else None
        print("after nudge btns", btns2, "thumb", thumb2)

    if scroll_only:
        print("SCROLL-ONLY RESULT changed=", changed)
        return 0 if changed else 2

    if not btns2:
        raise SystemExit("no buttons")
    cx, cy = max(btns2, key=lambda b: b[1])
    tap(cfg, cx, cy, wait=1.5)
    snap(cfg, f"clicked-idx{args.index}")
    print("CLICKED DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
