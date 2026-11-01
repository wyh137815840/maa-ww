#!/usr/bin/env python3
"""Roughly locate 索拉指南 tile on Terminal screenshot (bright icon in bottom row of grid)."""
from pathlib import Path
from PIL import Image, ImageDraw

im = Image.open(Path(r"D:\git\maa-ww\review\inbox\20261031-222419-live-after-guidebook.png")).convert("RGB")
print("size", im.size)
w, h = im.size
# right panel grid area
x0, x1 = int(w * 0.48), int(w * 0.95)
y0, y1 = int(h * 0.35), int(h * 0.85)

# find bright-ish blobs (icon centers tend to be colorful)
scores = []
step = 8
for y in range(y0, y1, step):
    for x in range(x0, x1, step):
        r, g, b = im.getpixel((x, y))
        # guidebook often teal/cyan-ish with book
        sat = max(r, g, b) - min(r, g, b)
        bright = (r + g + b) / 3
        if sat > 40 and bright > 80:
            scores.append((sat + bright * 0.2, x, y, r, g, b))

scores.sort(reverse=True)
print("top colorful samples", scores[:20])

# Save annotated crop of right panel
crop = im.crop((x0, y0, x1, y1))
# upscale for reading
crop2 = crop.resize((crop.width * 2, crop.height * 2))
out = Path(r"D:\git\maa-ww\tools\touch-review\_scrollbar_calib\terminal_right.png")
crop2.save(out)
print("wrote", out)
