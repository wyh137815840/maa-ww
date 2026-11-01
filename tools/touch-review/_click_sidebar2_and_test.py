#!/usr/bin/env python3
"""Click guidebook left-rail 2nd icon (user-confirmed), then SelectTacetRow scroll test."""
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


def tap(cfg, x, y, wait=1.2):
    print(f"  tap ({x},{y})")
    adb(cfg, "shell", "input", "tap", str(x), str(y), check=False)
    time.sleep(wait)


def snap(cfg, label):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = OUT / f"{stamp}-{label}.png"
    tag = capture_png(cfg["adb_path"], cfg["serial"], dest, cfg)
    print(f"  snap {dest.name} ({tag})")
    return dest


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=int, default=6)
    ap.add_argument("--click", action="store_true")
    # Left rail ~x=180; 6 icons from ~y140..580 → 2nd ≈ y=220
    ap.add_argument("--x", type=int, default=180)
    ap.add_argument("--y", type=int, default=220)
    args = ap.parse_args()

    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])

    path = snap(cfg, "before-side2")
    im = Image.open(path).convert("RGB")
    print("before btns", find_go_buttons(im))

    print("click left-rail 2nd icon")
    tap(cfg, args.x, args.y, wait=1.4)
    path = snap(cfg, "after-side2")
    im = Image.open(path).convert("RGB")
    btns = find_go_buttons(im)
    print("after side2 btns", btns)

    # If still activity-like (gold claim), try nearby Y for 2nd icon
    def has_gold(im0):
        n = 0
        for y in range(180, 360):
            for x in range(1000, 1220):
                r, g, b = im0.getpixel((x, y))
                if r > 160 and g > 120 and b < 120 and (r - b) > 60:
                    n += 1
                    if n > 40:
                        return True
        return False

    if has_gold(im) or len(btns) < 3:
        for y in (190, 200, 210, 230, 240, 250, 260):
            print(f"retry 2nd icon y={y}")
            tap(cfg, args.x, y, wait=1.2)
            path = snap(cfg, f"side2-y{y}")
            im = Image.open(path).convert("RGB")
            btns = find_go_buttons(im)
            gold = has_gold(im)
            print(f"  btns={btns} gold={gold}")
            if not gold and len(btns) >= 3:
                break

    if has_gold(im):
        raise SystemExit(f"still on activity-like page; see {path}")

    if len(btns) < 3:
        # maybe landed on 素材获取 hub — need 无音清剿 sub-tab
        print("few buttons; try GuidebookTacetTab (183,531)")
        tap(cfg, 183, 531, wait=1.3)
        path = snap(cfg, "after-tacet-subtab")
        im = Image.open(path).convert("RGB")
        btns = find_go_buttons(im)
        print("subtab btns", btns)

    if len(btns) < 3:
        raise SystemExit(f"not enough go buttons; see {path}")

    bar_top = detect_bar_top(im)
    p = plan(args.index, btns, bar_top)
    print("plan", p)
    if not p.get("ok"):
        raise SystemExit(p)

    if p["mode"] == "direct":
        if not args.click:
            print("scroll-only would click", p["click"])
            return 0
        tap(cfg, *p["click"], wait=1.5)
        snap(cfg, f"clicked-{args.index}")
        return 0

    sx, sy = p["scrollbar_click"]
    before = btns
    print(f"scrollbar ({sx},{sy})")
    tap(cfg, sx, sy, wait=1.4)
    path2 = snap(cfg, f"scrolled-{args.index}")
    im2 = Image.open(path2).convert("RGB")
    after = find_go_buttons(im2)
    print("after scroll", after, "changed", after != before)

    if after and max(b[1] for b in after) / 720 < 0.73 and "underscroll_retry_y" in p:
        ry = int(p["underscroll_retry_y"])
        print("nudge", ry)
        tap(cfg, sx, ry, wait=1.2)
        path2 = snap(cfg, f"nudged-{args.index}")
        im2 = Image.open(path2).convert("RGB")
        after = find_go_buttons(im2)
        print("after nudge", after)

    if not args.click:
        print("SCROLL-ONLY changed=", after != before)
        return 0 if after != before else 2

    if not after:
        raise SystemExit("no buttons after scroll")
    cx, cy = max(after, key=lambda b: b[1])
    tap(cfg, cx, cy, wait=1.5)
    snap(cfg, f"clicked-{args.index}")
    print("CLICKED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
