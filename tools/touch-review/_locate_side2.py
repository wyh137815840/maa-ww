#!/usr/bin/env python3
"""Find left-rail icon centers by looking for circular-ish bright icons."""
from pathlib import Path
from PIL import Image, ImageDraw

im = Image.open(Path(r"D:\git\maa-ww\review\inbox\20261031-222923-before-side2.png")).convert("RGB")
w, h = im.size
# scan x=120..220 for icon rows: high local variance / brightness peaks
xs = range(140, 210)
# vertical energy: colorful pixels
energy = []
for y in range(90, 650):
    sat = 0
    for x in xs:
        r, g, b = im.getpixel((x, y))
        sat += max(r, g, b) - min(r, g, b)
    energy.append((y, sat))

# smooth
win = 5
smooth = []
for i, (y, s) in enumerate(energy):
    lo = max(0, i - win)
    hi = min(len(energy), i + win + 1)
    smooth.append((y, sum(v for _, v in energy[lo:hi]) / (hi - lo)))

# peak pick with min distance 40
peaks = []
for i in range(10, len(smooth) - 10):
    y, s = smooth[i]
    if s > smooth[i - 1][1] and s >= smooth[i + 1][1] and s > 800:
        if not peaks or y - peaks[-1][0] > 45:
            peaks.append((y, s))
        elif s > peaks[-1][1]:
            peaks[-1] = (y, s)

print("peaks (y, energy):", peaks[:10])
vis = im.copy()
dr = ImageDraw.Draw(vis)
for i, (y, s) in enumerate(peaks[:8]):
    dr.ellipse((170, y - 10, 190, y + 10), outline=(255, 0, 0), width=2)
    dr.text((200, y - 8), f"#{i+1} y={y}", fill=(255, 40, 40))
out = Path(r"D:\git\maa-ww\tools\touch-review\_scrollbar_calib\side_peaks.png")
vis.crop((40, 80, 320, 680)).resize((560, 1200)).save(out)
print("wrote", out)
