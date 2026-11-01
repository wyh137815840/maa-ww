#!/usr/bin/env python3
"""Calibrate scrollbar thumb from scroll-sequence snaps."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SHOTS = [
    ROOT / "review/inbox/20261031-205657-snap.png",
    ROOT / "review/inbox/20261031-205700-snap.png",
    ROOT / "review/inbox/20261031-205704-snap.png",
    ROOT / "review/inbox/20261031-205708-snap.png",
    ROOT / "review/inbox/20261031-205201-snap.png",
    ROOT / "review/inbox/20261031-205216-snap.png",
]

STRUCTURE = [4, 5, 5, 7]
TOTAL = sum(STRUCTURE)
BAR_X_RATIO = 0.973
BAR_BOTTOM_RATIO = 0.8806
HEADER_H_RATIO = 0.028


def is_thumb(rgb: tuple[int, int, int]) -> bool:
    r, g, b = rgb
    mx, mn = max(r, g, b), min(r, g, b)
    if mx - mn > 28:
        return False
    return 55 <= mx <= 165


def is_trackish(rgb: tuple[int, int, int]) -> bool:
    r, g, b = rgb
    mx, mn = max(r, g, b), min(r, g, b)
    if mx - mn > 35:
        return False
    return 140 <= mx <= 230


def find_go(im: Image.Image) -> list[tuple[int, int, int]]:
    w, h = im.size
    x0, x1 = int(w * 0.81), int(w * 0.96)
    dark_ys: list[int] = []
    for y in range(int(h * 0.18), int(h * 0.90)):
        cnt = sum(1 for x in range(x0, x1) if sum(im.getpixel((x, y))) < 120)
        if cnt > 80:
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
    out: list[tuple[int, int, int]] = []
    for ya, yb in bands:
        if not (18 <= (yb - ya + 1) <= 60):
            continue
        cy = (ya + yb) // 2
        xs = [x for x in range(x0, x1) if sum(im.getpixel((x, cy))) < 120]
        if xs:
            out.append(((min(xs) + max(xs)) // 2, cy, yb - ya + 1))
    return out


def thumb_bands_at_x(im: Image.Image, x: int) -> list[tuple[int, int]]:
    ys = [y for y in range(100, 700) if is_thumb(im.getpixel((x, y)))]
    if not ys:
        return []
    bands: list[tuple[int, int]] = []
    a = p = ys[0]
    for y in ys[1:]:
        if y - p > 2:
            bands.append((a, p))
            a = y
        p = y
    bands.append((a, p))
    return [b for b in bands if b[1] - b[0] + 1 >= 8]


def detect_scrollbar(im: Image.Image) -> dict | None:
    w, h = im.size
    cands: list[tuple[int, int, int, int, int]] = []
    for x in range(w - 90, w):
        bands = thumb_bands_at_x(im, x)
        if not bands:
            continue
        ya, yb = max(bands, key=lambda t: t[1] - t[0])
        score = yb - ya + 1
        # prefer columns that also have track-ish pixels nearby
        track_n = sum(1 for y in range(120, 660) if is_trackish(im.getpixel((x, y))))
        cands.append((score + track_n // 20, x, ya, yb, track_n))
    if not cands:
        return None
    cands.sort(reverse=True)
    _, x, ya, yb, track_n = cands[0]
    # refine track top/bottom near this x using lighter gray streak
    track_ys = [y for y in range(100, 700) if is_trackish(im.getpixel((x, y))) or is_thumb(im.getpixel((x, y)))]
    track_top = min(track_ys) if track_ys else ya
    track_bot = max(track_ys) if track_ys else yb
    return {
        "x": x,
        "thumb_ya": ya,
        "thumb_yb": yb,
        "thumb_h": yb - ya + 1,
        "thumb_cy": (ya + yb) // 2,
        "track_top": track_top,
        "track_bot": track_bot,
        "track_n": track_n,
        "x_ratio": round(x / w, 4),
        "thumb_cy_ratio": round(((ya + yb) / 2) / h, 4),
        "track_top_ratio": round(track_top / h, 4),
        "track_bot_ratio": round(track_bot / h, 4),
    }


def cross_count(serial: int) -> int:
    s = 0
    cross = 0
    for n in STRUCTURE:
        s += n
        if serial > s:
            cross += 1
        else:
            break
    return cross


def okww_y(serial: int, bar_top: float, h: int = 720) -> int:
    calib_h = BAR_BOTTOM_RATIO - bar_top - (len(STRUCTURE) - 1) * HEADER_H_RATIO
    item_h = calib_h / TOTAL
    y_ratio = min(bar_top + item_h * serial + cross_count(serial) * HEADER_H_RATIO, BAR_BOTTOM_RATIO)
    return int(y_ratio * h)


def main() -> None:
    rows = []
    for p in SHOTS:
        if not p.exists():
            print("MISSING", p)
            continue
        im = Image.open(p).convert("RGB")
        sb = detect_scrollbar(im)
        btns = find_go(im)
        print("===", p.name)
        print(" scrollbar:", sb)
        print(" pills:", btns)
        rows.append((p.name, sb, btns))

    print("\n--- ok-ww formula vs observed thumb_cy (bar_top=0.22) ---")
    for idx in range(1, 22):
        print(f"  index={idx:2d} cross={cross_count(idx)} y={okww_y(idx, 0.22)}")

    # Also dump rightmost column profiles for one top + one mid shot
    for name in ("20261031-205708-snap.png", "20261031-205657-snap.png"):
        im = Image.open(ROOT / "review/inbox" / name).convert("RGB")
        print(f"\n--- column gray profile {name} ---")
        for x in range(1235, 1260):
            ys_t = [y for y in range(100, 700) if is_thumb(im.getpixel((x, y)))]
            if len(ys_t) < 5:
                continue
            print(f"  x={x} thumb {min(ys_t)}-{max(ys_t)} n={len(ys_t)} cy={(min(ys_t)+max(ys_t))/2:.1f}")


if __name__ == "__main__":
    main()
