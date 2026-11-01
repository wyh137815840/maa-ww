#!/usr/bin/env python3
"""Offline prototype: find all 直接挑战/前往 pills + plan scrollbar click (ok-ww).

Calibrated against review/inbox/20261031-205657..708 scroll sequence.
See docs/zh_cn/tacet-scrollbar-calib.json / tacet-select-design.md.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CALIB_PATH = ROOT / "docs/zh_cn/tacet-scrollbar-calib.json"

STRUCTURE = [4, 5, 5, 7]
TOTAL = sum(STRUCTURE)
BAR_X_RATIO = 0.973
BAR_BOTTOM_RATIO = 0.8806
BAR_TOP_FALLBACK = 0.1963
HEADER_H_RATIO = 0.028
VIEWPORT_ROWS = 4


def load_calib() -> dict:
    if CALIB_PATH.exists():
        return json.loads(CALIB_PATH.read_text(encoding="utf-8"))
    return {}


def cross_count(structure: list[int], serial_1based: int) -> int:
    s = 0
    cross = 0
    for n in structure:
        s += n
        if serial_1based > s:
            cross += 1
        else:
            break
    return cross


def scrollbar_y(serial_1based: int, bar_top: float, h: int) -> int:
    """Approximate scrollbar click y (pixels), ok-ww formula."""
    calib_h = BAR_BOTTOM_RATIO - bar_top - (len(STRUCTURE) - 1) * HEADER_H_RATIO
    item_h = calib_h / TOTAL if TOTAL else 0
    cross = cross_count(STRUCTURE, serial_1based)
    y_ratio = min(bar_top + item_h * serial_1based + cross * HEADER_H_RATIO, BAR_BOTTOM_RATIO)
    return int(y_ratio * h)


def find_go_buttons(im: Image.Image) -> list[tuple[int, int]]:
    """Return [(cx,cy), ...] sorted by y — dark pills in right column (直接挑战/前往)."""
    w, h = im.size
    # right column of 直接挑战 pills; skip filter chrome & name-card dark strips
    x0, x1 = int(w * 0.88), int(w * 0.96)  # ~1126..1228 @1280
    dark_ys: list[int] = []
    for y in range(max(220, int(h * 0.30)), int(h * 0.90)):
        cnt = sum(1 for x in range(x0, x1) if sum(im.getpixel((x, y))) < 120)
        if cnt > 55:
            dark_ys.append(y)
    bands: list[tuple[int, int]] = []
    if dark_ys:
        a = p = dark_ys[0]
        for y in dark_ys[1:]:
            if y - p > 3:
                bands.append((a, p))
                a = y
            p = y
        bands.append((a, p))
    # mid-scroll pills often split into 2 thin bands; merge close neighbors
    merged: list[tuple[int, int]] = []
    for ya, yb in bands:
        if merged and ya - merged[-1][1] <= 8:
            merged[-1] = (merged[-1][0], yb)
        else:
            merged.append((ya, yb))
    out: list[tuple[int, int]] = []
    for ya, yb in merged:
        if not (14 <= (yb - ya + 1) <= 60):
            continue
        cy = (ya + yb) // 2
        xs = [x for x in range(x0, x1) if sum(im.getpixel((x, cy))) < 120]
        if not xs:
            continue
        cx = (min(xs) + max(xs)) // 2
        # real pills sit near x≈1146–1174; reject leftish dark noise
        if cx < 1125:
            continue
        out.append((cx, cy))
    out.sort(key=lambda p: p[1])
    return out


def detect_thumb(im: Image.Image) -> tuple[int, int, int] | None:
    """Return (ya, yb, x) of light scrollbar thumb on dark track, or None."""
    best = None  # (score, ya, yb, x)
    for x in range(1240, 1252):
        ys = []
        for y in range(140, 640):
            r, g, b = im.getpixel((x, y))
            v = 0.299 * r + 0.587 * g + 0.114 * b
            left = sum(im.getpixel((max(0, x - 8), y))) / 3
            if v >= 170 and v > left + 12:
                ys.append(y)
        if len(ys) < 20:
            continue
        # longest contiguous band ~ thumb height 80–130
        i = 0
        while i < len(ys):
            a = p = ys[i]
            j = i + 1
            while j < len(ys) and ys[j] - p <= 2:
                p = ys[j]
                j += 1
            band_h = p - a + 1
            if 70 <= band_h <= 140:
                score = band_h
                if best is None or score > best[0]:
                    best = (score, a, p, x)
            i = j
    if best is None:
        return None
    return best[1], best[2], best[3]


def detect_bar_top(im: Image.Image, fallback: float = BAR_TOP_FALLBACK) -> float:
    """Light thumb top on track; ratio of image height."""
    thumb = detect_thumb(im)
    if thumb is None:
        return fallback
    return thumb[0] / im.size[1]


def plan(serial_1based: int, visible: list[tuple[int, int]], bar_top: float = BAR_TOP_FALLBACK) -> dict:
    h = 720
    if serial_1based < 1 or serial_1based > TOTAL:
        return {"ok": False, "error": f"index out of range 1..{TOTAL}"}
    if serial_1based <= VIEWPORT_ROWS and len(visible) >= serial_1based:
        cx, cy = visible[serial_1based - 1]
        return {
            "ok": True,
            "mode": "direct",
            "click": [cx, cy],
            "bar_top": bar_top,
            "note": f"first page: click visible button #{serial_1based}",
        }
    sy = scrollbar_y(serial_1based, bar_top, h)
    item_h = (BAR_BOTTOM_RATIO - bar_top - (len(STRUCTURE) - 1) * HEADER_H_RATIO) / TOTAL
    return {
        "ok": True,
        "mode": "scrollbar_then_bottom_btn",
        "scrollbar_click": [int(BAR_X_RATIO * 1280), sy],
        "scrollbar_click_ratio": [BAR_X_RATIO, round(sy / h, 4)],
        "then": "re-detect buttons; click max(y) (ok-ww style)",
        "underscroll_retry_y": int(min(sy / h + item_h * 0.55, BAR_BOTTOM_RATIO) * h),
        "cross": cross_count(STRUCTURE, serial_1based),
        "bar_top": bar_top,
        "note": "After scroll, runtime re-finds buttons and clicks bottom-most",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("image", type=Path)
    ap.add_argument("--index", type=int, default=1)
    args = ap.parse_args()
    calib = load_calib()
    global BAR_X_RATIO, BAR_BOTTOM_RATIO, BAR_TOP_FALLBACK, STRUCTURE, TOTAL
    if calib:
        BAR_X_RATIO = float(calib.get("bar_x_ratio", BAR_X_RATIO))
        BAR_BOTTOM_RATIO = float(calib.get("bar_bottom_ratio", BAR_BOTTOM_RATIO))
        BAR_TOP_FALLBACK = float(calib.get("bar_top_fallback_ratio", BAR_TOP_FALLBACK))
        STRUCTURE = list(calib.get("structure", STRUCTURE))
        TOTAL = int(calib.get("total", sum(STRUCTURE)))
    im = Image.open(args.image).convert("RGB")
    btns = find_go_buttons(im)
    bar_top = detect_bar_top(im, BAR_TOP_FALLBACK)
    print("calib", CALIB_PATH.name if calib else "builtin")
    print("bar_top", round(bar_top, 4), "fallback", BAR_TOP_FALLBACK)
    print("visible_go_buttons", btns)
    print("plan", plan(args.index, btns, bar_top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
