#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw

im = Image.open(Path(r"D:\git\maa-ww\review\inbox\20261031-224856-odin-menu-1198-38.png")).convert("RGB")
x0, x1 = 520, 1100
# grid bottom row ~476-521 from previous scan
ya, yb = 470, 530
cy = (ya + yb) // 2
xs = []
for x in range(x0, x1):
    bright = 0
    for y in range(ya, yb):
        r, g, b = im.getpixel((x, y))
        if min(r, g, b) > 160 and max(r, g, b) - min(r, g, b) < 50:
            bright += 1
    if bright > 8:
        xs.append(x)
bands = []
if xs:
    a = p = xs[0]
    for x in xs[1:]:
        if x - p > 6:
            bands.append((a, p))
            a = x
        p = x
    bands.append((a, p))
centers = [((a + b) // 2, cy) for a, b in bands if b - a >= 8]
print("row3/4 centers", centers)
vis = im.copy()
dr = ImageDraw.Draw(vis)
for i, (cx, cy) in enumerate(centers):
    dr.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), outline=(0, 255, 0), width=3)
    dr.text((cx - 8, cy + 18), str(i + 1), fill=(0, 255, 0))
out = Path(r"D:\git\maa-ww\tools\touch-review\_scrollbar_calib\terminal_grid_row.png")
vis.crop((500, 250, 1150, 600)).save(out)
print("wrote", out)
if centers:
    print("SOLA=#1", centers[0])
