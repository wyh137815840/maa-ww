#!/usr/bin/env python3
"""Find scrollbar via frame-diff + save annotated crops for visual check."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tools/touch-review/_scrollbar_calib"
OUT.mkdir(parents=True, exist_ok=True)

SEQ = [
    ("topish_708", ROOT / "review/inbox/20261031-205708-snap.png"),
    ("mid_704", ROOT / "review/inbox/20261031-205704-snap.png"),
    ("mid2_700", ROOT / "review/inbox/20261031-205700-snap.png"),
    ("mid3_657", ROOT / "review/inbox/20261031-205657-snap.png"),
]


def lum(rgb: tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.299 * r + 0.587 * g + 0.114 * b


def find_go(im: Image.Image) -> list[tuple[int, int]]:
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
    out: list[tuple[int, int]] = []
    for ya, yb in bands:
        if not (18 <= (yb - ya + 1) <= 60):
            continue
        cy = (ya + yb) // 2
        xs = [x for x in range(x0, x1) if sum(im.getpixel((x, cy))) < 120]
        if xs:
            out.append(((min(xs) + max(xs)) // 2, cy))
    return out


def column_diff_energy(a: Image.Image, b: Image.Image) -> list[tuple[int, float, int, int]]:
    """Per-x: (x, energy, y_min_of_strong_diff, y_max). Only narrow vertical movers."""
    w, h = a.size
    out = []
    for x in range(1180, w):
        diffs = []
        for y in range(140, 660):
            d = abs(lum(a.getpixel((x, y))) - lum(b.getpixel((x, y))))
            if d > 18:
                diffs.append((y, d))
        if len(diffs) < 6:
            continue
        energy = sum(d for _, d in diffs)
        ys = [y for y, _ in diffs]
        # Prefer thin features: few rows changed relative to span? Actually thumb moves so many rows change.
        out.append((x, energy, min(ys), max(ys), len(diffs)))
    out.sort(key=lambda t: t[1], reverse=True)
    return out


def local_dark_run(im: Image.Image, x: int, y0: int = 140, y1: int = 650) -> list[tuple[int, int]]:
    """Find contiguous darker-than-neighbors vertical runs (scrollbar thumb)."""
    vals = [lum(im.getpixel((x, y))) for y in range(y0, y1)]
    # relative darkness vs horizontal neighbors
    dark_ys = []
    for i, y in enumerate(range(y0, y1)):
        left = lum(im.getpixel((max(0, x - 3), y)))
        right = lum(im.getpixel((min(im.size[0] - 1, x + 3), y)))
        neigh = (left + right) / 2
        if vals[i] + 12 < neigh and vals[i] < 170:
            dark_ys.append(y)
    if not dark_ys:
        return []
    bands = []
    a = p = dark_ys[0]
    for y in dark_ys[1:]:
        if y - p > 2:
            bands.append((a, p))
            a = y
        p = y
    bands.append((a, p))
    return [b for b in bands if 12 <= b[1] - b[0] + 1 <= 120]


def annotate(im: Image.Image, name: str, pills: list[tuple[int, int]], marks: list[tuple[int, int, str]]) -> None:
    vis = im.copy()
    dr = ImageDraw.Draw(vis)
    for cx, cy in pills:
        dr.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), outline=(255, 0, 0), width=2)
        dr.text((cx - 40, cy - 18), f"{cy}", fill=(255, 0, 0))
    for x, y, label in marks:
        dr.line((x - 8, y, x + 8, y), fill=(0, 255, 0), width=2)
        dr.line((x, y - 8, x, y + 8), fill=(0, 255, 0), width=2)
        dr.text((x - 60, y + 10), label, fill=(0, 200, 0))
    # right strip crop
    strip = vis.crop((1180, 120, 1280, 680))
    strip = strip.resize((strip.width * 3, strip.height * 3), Image.NEAREST)
    strip.save(OUT / f"{name}_strip.png")
    vis.save(OUT / f"{name}_full.png")


def main() -> None:
    imgs = [(n, Image.open(p).convert("RGB")) for n, p in SEQ if p.exists()]
    print("loaded", [n for n, _ in imgs])

    # pairwise diffs: top vs each later
    base_n, base = imgs[0]
    for n, im in imgs[1:]:
        print(f"\n=== diff {base_n} vs {n} ===")
        cols = column_diff_energy(base, im)
        print(" top diff cols:", cols[:8])
        # focus on columns with moderate-height change (scrollbar-like)
        narrow = [c for c in cols if 20 <= c[4] <= 180]
        print(" narrow-ish:", narrow[:8])

    # neighbor-relative dark runs for candidate x around 1240-1255
    print("\n=== neighbor-dark bands ===")
    summary = []
    for n, im in imgs:
        pills = find_go(im)
        marks = []
        print(f"\n--- {n} pills={pills}")
        best = None
        for x in range(1238, 1256):
            bands = local_dark_run(im, x)
            if not bands:
                continue
            # pick band most likely thumb: medium height in list area
            for ya, yb in bands:
                h = yb - ya + 1
                if 15 <= h <= 100:
                    cy = (ya + yb) // 2
                    score = h
                    if best is None or score > best[0]:
                        best = (score, x, ya, yb, cy)
        if best:
            _, x, ya, yb, cy = best
            print(f"  thumb? x={x} {ya}-{yb} cy={cy} h={yb-ya+1}")
            marks.append((x, cy, f"t{cy}"))
            summary.append((n, x, ya, yb, cy, pills))
        else:
            # try wider
            for x in range(1225, 1265):
                bands = local_dark_run(im, x)
                if bands:
                    print(f"  x={x} bands={bands}")
            summary.append((n, None, None, None, None, pills))
        annotate(im, n, pills, marks)

    # Also: absolute luminance valleys on fixed x=1245 across sequence
    print("\n=== fixed-x=1245/1248 valley bands ===")
    for xfix in (1244, 1245, 1246, 1247, 1248, 1249, 1250):
        print(f" xfix={xref}")
        for n, im in imgs:
            bands = local_dark_run(im, xref)
            print(f"  {n}: {bands}")

    # Save difference heat strip between first and last
    a = imgs[0][1]
    b = imgs[-1][1]
    heat = Image.new("RGB", (100, 540))
    for xi, x in enumerate(range(1180, 1280)):
        for yi, y in enumerate(range(140, 680)):
            d = int(min(255, abs(lum(a.getpixel((x, y))) - lum(b.getpixel((x, y)))) * 4))
            heat.putpixel((xi, yi), (d, d // 2, 0))
    heat = heat.resize((300, 540 * 2), Image.NEAREST)
    heat.save(OUT / "diff_708_vs_657_heat.png")
    print("\nwrote", OUT)


if __name__ == "__main__":
    main()
