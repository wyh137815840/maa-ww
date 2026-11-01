#!/usr/bin/env python3
"""Detect LIGHT scrollbar thumb on dark track; calibrate ok-ww formula against scroll sequence."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tools/touch-review/_scrollbar_calib"
OUT.mkdir(parents=True, exist_ok=True)

SHOTS = [
    ("657", ROOT / "review/inbox/20261031-205657-snap.png"),
    ("700", ROOT / "review/inbox/20261031-205700-snap.png"),
    ("704", ROOT / "review/inbox/20261031-205704-snap.png"),
    ("708", ROOT / "review/inbox/20261031-205708-snap.png"),
    ("201", ROOT / "review/inbox/20261031-205201-snap.png"),
    ("216", ROOT / "review/inbox/20261031-205216-snap.png"),
]

STRUCTURE = [4, 5, 5, 7]
TOTAL = sum(STRUCTURE)
HEADER_H = 0.028


def lum(rgb: tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.299 * r + 0.587 * g + 0.114 * b


def find_go(im: Image.Image) -> list[tuple[int, int]]:
    w, h = im.size
    x0, x1 = int(w * 0.81), int(w * 0.96)
    dark_ys: list[int] = []
    for y in range(int(h * 0.16), int(h * 0.92)):
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
    out: list[tuple[int, int]] = []
    for ya, yb in bands:
        if not (18 <= (yb - ya + 1) <= 60):
            continue
        cy = (ya + yb) // 2
        xs = [x for x in range(x0, x1) if sum(im.getpixel((x, cy))) < 120]
        if xs:
            out.append(((min(xs) + max(xs)) // 2, cy))
    return out


def light_thumb_at_x(im: Image.Image, x: int) -> list[tuple[int, int]]:
    """Bright vertical run that is brighter than left neighbor (list edge)."""
    y0, y1 = 150, 660
    ys = []
    for y in range(y0, y1):
        v = lum(im.getpixel((x, y)))
        left = lum(im.getpixel((x - 6, y)))
        # thumb: fairly bright, and brighter than panel to the left OR sits on dark track
        if v >= 175 and (v > left + 8 or left < 80):
            ys.append(y)
    if not ys:
        return []
    bands = []
    a = p = ys[0]
    for y in ys[1:]:
        if y - p > 2:
            bands.append((a, p))
            a = y
        p = y
    bands.append((a, p))
    # thumb height roughly 30-120px on this UI
    return [b for b in bands if 20 <= b[1] - b[0] + 1 <= 140]


def score_column(im: Image.Image, x: int) -> tuple[float, tuple[int, int] | None]:
    bands = light_thumb_at_x(im, x)
    if not bands:
        return 0.0, None
    # prefer single medium band; penalize many bands (button shine)
    best = max(bands, key=lambda b: b[1] - b[0])
    h = best[1] - best[0] + 1
    # also require some dark track pixels above/below near this x
    track = 0
    for y in range(160, 640):
        if lum(im.getpixel((x, y))) < 55:
            track += 1
    score = h + track * 0.15 - max(0, len(bands) - 1) * 30
    return score, best


def detect_thumb(im: Image.Image) -> dict | None:
    best = None
    for x in range(1235, 1260):
        sc, band = score_column(im, x)
        if band is None:
            continue
        ya, yb = band
        cy = (ya + yb) // 2
        cand = (sc, x, ya, yb, cy)
        if best is None or cand[0] > best[0]:
            best = cand
    if not best:
        return None
    _, x, ya, yb, cy = best
    # track extents: dark pixels near x
    dark = [y for y in range(140, 680) if lum(im.getpixel((x, y))) < 60]
    track_top = min(dark) if dark else 160
    track_bot = max(dark) if dark else 640
    h = im.size[1]
    return {
        "x": x,
        "ya": ya,
        "yb": yb,
        "cy": cy,
        "thumb_h": yb - ya + 1,
        "track_top": track_top,
        "track_bot": track_bot,
        "x_ratio": round(x / im.size[0], 4),
        "cy_ratio": round(cy / h, 4),
        "ya_ratio": round(ya / h, 4),
        "track_top_ratio": round(track_top / h, 4),
        "track_bot_ratio": round(track_bot / h, 4),
    }


def cross_count(serial: int) -> int:
    s = cross = 0
    for n in STRUCTURE:
        s += n
        if serial > s:
            cross += 1
        else:
            break
    return cross


def formula_y(serial: int, bar_top: float, bar_bottom: float, h: int = 720) -> int:
    calib = bar_bottom - bar_top - (len(STRUCTURE) - 1) * HEADER_H
    item = calib / TOTAL
    r = min(bar_top + item * serial + cross_count(serial) * HEADER_H, bar_bottom)
    return int(r * h)


def annotate(im: Image.Image, name: str, thumb: dict | None, pills: list[tuple[int, int]]) -> None:
    vis = im.copy()
    dr = ImageDraw.Draw(vis)
    for cx, cy in pills:
        dr.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), outline=(255, 40, 40), width=2)
        dr.text((cx - 36, cy - 16), str(cy), fill=(255, 40, 40))
    if thumb:
        x, ya, yb, cy = thumb["x"], thumb["ya"], thumb["yb"], thumb["cy"]
        dr.rectangle((x - 2, ya, x + 2, yb), outline=(0, 255, 80), width=2)
        dr.line((x - 12, cy, x + 12, cy), fill=(0, 255, 80), width=2)
        dr.text((x - 70, cy - 10), f"cy={cy}", fill=(0, 220, 80))
        dr.line((x, thumb["track_top"], x, thumb["track_bot"]), fill=(80, 160, 255), width=1)
    strip = vis.crop((1200, 130, 1280, 670))
    strip.resize((strip.width * 4, strip.height * 2), Image.NEAREST).save(OUT / f"light_{name}_strip.png")
    vis.save(OUT / f"light_{name}_full.png")


def main() -> None:
    results = []
    for name, path in SHOTS:
        if not path.exists():
            print("missing", path)
            continue
        im = Image.open(path).convert("RGB")
        thumb = detect_thumb(im)
        pills = find_go(im)
        print("===", name, path.name)
        print(" thumb", thumb)
        print(" pills", pills)
        annotate(im, name, thumb, pills)
        results.append({"id": name, "file": path.name, "thumb": thumb, "pills": pills})

    # Estimate bar_top/bottom from extremes of detected thumbs + track
    cys = [r["thumb"]["cy"] for r in results if r["thumb"]]
    tops = [r["thumb"]["track_top"] for r in results if r["thumb"]]
    bots = [r["thumb"]["track_bot"] for r in results if r["thumb"]]
    xs = [r["thumb"]["x"] for r in results if r["thumb"]]
    print("\ncy range", min(cys), max(cys) if cys else None)
    print("track_top median-ish", sorted(tops)[len(tops) // 2] if tops else None)
    print("track_bot median-ish", sorted(bots)[len(bots) // 2] if bots else None)
    print("x values", xs)

    if tops and bots and xs:
        bar_top = sorted(tops)[len(tops) // 2] / 720
        bar_bot = sorted(bots)[len(bots) // 2] / 720
        bar_x = sorted(xs)[len(xs) // 2]
        print(f"\ncalibrated bar_top={bar_top:.4f} bar_bottom={bar_bot:.4f} bar_x={bar_x}")
        print("formula click y for index 1..21:")
        for i in range(1, 22):
            print(f"  {i:2d}: y={formula_y(i, bar_top, bar_bot)} cross={cross_count(i)}")

        calib = {
            "bar_x": bar_x,
            "bar_x_ratio": round(bar_x / 1280, 4),
            "bar_top_ratio": round(bar_top, 4),
            "bar_bottom_ratio": round(bar_bot, 4),
            "header_h_ratio": HEADER_H,
            "structure": STRUCTURE,
            "total": TOTAL,
            "viewport_rows": 4,
            "button_search_roi": [1040, 160, 200, 520],
            "click_x_typical": 1146,
            "row_pitch_px": 102,
            "thumb_detection": "light-on-dark",
            "source_snaps": [r["file"] for r in results],
            "observed": [
                {
                    "file": r["file"],
                    "thumb_cy": r["thumb"]["cy"] if r["thumb"] else None,
                    "thumb_ya": r["thumb"]["ya"] if r["thumb"] else None,
                    "thumb_yb": r["thumb"]["yb"] if r["thumb"] else None,
                    "bar_x": r["thumb"]["x"] if r["thumb"] else None,
                    "pills_y": [p[1] for p in r["pills"]],
                }
                for r in results
            ],
            "note": "Click scrollbar at formula y to bring target near viewport bottom; then re-detect pills and click bottom-most (ok-ww).",
        }
        out_json = ROOT / "docs/zh_cn/tacet-scrollbar-calib.json"
        out_json.write_text(json.dumps(calib, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("wrote", out_json)

    # also dump per-x bands for one mid shot for sanity
    im = Image.open(ROOT / "review/inbox/20261031-205700-snap.png").convert("RGB")
    print("\nper-x light bands on 700:")
    for x in range(1238, 1256):
        print(x, light_thumb_at_x(im, x), "score", score_column(im, x)[0])


if __name__ == "__main__":
    main()
