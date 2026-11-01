#!/usr/bin/env python3
"""From current guidebook page, find & click 无音清剿 via template or sidebar sweep."""
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
TAB = ROOT / "assets/resource_adb/image/Guidebook/TacetTab.png"
GO = ROOT / "assets/resource_adb/image/Guidebook/TacetGoButton.png"


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


def has_yellow_claim(im: Image.Image) -> bool:
    n = 0
    for y in range(180, 360):
        for x in range(1000, 1220):
            r, g, b = im.getpixel((x, y))
            if r > 160 and g > 120 and b < 120 and (r - b) > 60:
                n += 1
                if n > 40:
                    return True
    return False


def match_template(screen: Image.Image, tmpl: Image.Image, roi, thresh=0.72):
    """Naive RGB SAD normalized match; return (score, cx, cy) best or None."""
    sx, sy, sw, sh = roi
    tw, th = tmpl.size
    best = None
    # downsample for speed
    step = 2
    tpx = list(tmpl.getdata())
    for y in range(sy, sy + sh - th, step):
        for x in range(sx, sx + sw - tw, step):
            sad = 0
            n = 0
            for j in range(0, th, 2):
                for i in range(0, tw, 2):
                    a = screen.getpixel((x + i, y + j))
                    b = tpx[j * tw + i]
                    sad += abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])
                    n += 1
            # score 1 = perfect
            score = 1.0 - (sad / (n * 255 * 3))
            if best is None or score > best[0]:
                best = (score, x + tw // 2, y + th // 2)
    if best and best[0] >= thresh:
        return best
    return best  # return even if low, caller decides


def looks_tacet(im: Image.Image) -> bool:
    if has_yellow_claim(im):
        return False
    btns = find_go_buttons(im)
    if len(btns) < 3:
        return False
    # template of 直接挑战 if present
    if GO.exists():
        go = Image.open(GO).convert("RGB")
        m = match_template(im, go, (1040, 160, 220, 500), thresh=0.55)
        print("  TacetGoButton match", m)
        if m and m[0] >= 0.62:
            return True
    # dark pills
    dark = sum(1 for cx, cy in btns if sum(im.getpixel((cx, cy))) < 200)
    return dark >= 3 and not has_yellow_claim(im)


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=int, default=6)
    ap.add_argument("--click", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])

    path = snap(cfg, "goto-start")
    im = Image.open(path).convert("RGB")
    print("start yellow_claim", has_yellow_claim(im), "btns", find_go_buttons(im), "tacet", looks_tacet(im))

    if not looks_tacet(im):
        # try template TacetTab
        if TAB.exists():
            tab = Image.open(TAB).convert("RGB")
            m = match_template(im, tab, (60, 80, 280, 600), thresh=0.5)
            print("TacetTab best", m)
            if m and m[0] >= 0.55:
                tap(cfg, m[1], m[2])
                path = snap(cfg, "after-tab-tmpl")
                im = Image.open(path).convert("RGB")
                print("after tmpl tacet", looks_tacet(im), "btns", find_go_buttons(im))

        if not looks_tacet(im):
            # sweep left sidebar icons (guidebook rail)
            for y in range(140, 640, 70):
                tap(cfg, 180, y, wait=0.9)
                path = snap(cfg, f"side-y{y}")
                im = Image.open(path).convert("RGB")
                ok = looks_tacet(im)
                print(f"  side y={y} tacet={ok} yellow={has_yellow_claim(im)} btns={find_go_buttons(im)}")
                if ok:
                    break

    if not looks_tacet(im):
        raise SystemExit(f"cannot reach tacet list; last={path}")

    btns = find_go_buttons(im)
    bar_top = detect_bar_top(im)
    p = plan(args.index, btns, bar_top)
    print("ON TACET plan", p)

    if p["mode"] == "direct":
        if not args.click:
            print("scroll-only direct would click", p["click"])
            return 0
        tap(cfg, *p["click"])
        snap(cfg, f"clicked-{args.index}")
        return 0

    sx, sy = p["scrollbar_click"]
    before = btns
    tap(cfg, sx, sy, wait=1.4)
    path2 = snap(cfg, f"scrolled-{args.index}")
    im2 = Image.open(path2).convert("RGB")
    after = find_go_buttons(im2)
    print("after scroll", after, "changed", after != before)

    if after and max(b[1] for b in after) / 720 < 0.73:
        ry = int(p["underscroll_retry_y"])
        tap(cfg, sx, ry, wait=1.2)
        path2 = snap(cfg, f"nudged-{args.index}")
        im2 = Image.open(path2).convert("RGB")
        after = find_go_buttons(im2)
        print("after nudge", after)

    if not args.click:
        print("SCROLL-ONLY done changed=", after != before)
        return 0 if after != before else 2

    if not after:
        raise SystemExit("no buttons")
    cx, cy = max(after, key=lambda b: b[1])
    tap(cfg, cx, cy, wait=1.5)
    snap(cfg, f"clicked-{args.index}")
    print("CLICKED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
