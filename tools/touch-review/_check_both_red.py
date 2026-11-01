#!/usr/bin/env python3
from pathlib import Path
from PIL import Image

p = Path(__file__).resolve().parents[2] / "review/inbox/20261031-202612-snap.png"
im = Image.open(p).convert("RGB")
# button band from prior find
red_l = red_r = 0
for y in range(420, 480):
    for x in range(450, 650):  # left 60
        r, g, b = im.getpixel((x, y))
        if r > 150 and g < 110 and b < 110:
            red_l += 1
    for x in range(700, 900):  # right 120
        r, g, b = im.getpixel((x, y))
        if r > 150 and g < 110 and b < 110:
            red_r += 1
print(f"size={im.size} red_left={red_l} red_right={red_r}")
