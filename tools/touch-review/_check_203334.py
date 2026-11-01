#!/usr/bin/env python3
from pathlib import Path
from PIL import Image

im = Image.open(Path(__file__).resolve().parents[2] / "review/inbox/20261031-203334-snap.png").convert("RGB")
print("stamina area sample", im.getpixel((1180, 40)))
# dump some pixels around left/right cost digits
for label, x0, x1 in [("L60", 430, 520), ("R120", 720, 820)]:
    reds = []
    for y in range(430, 475):
        for x in range(x0, x1):
            r, g, b = im.getpixel((x, y))
            if r > 140 and g < 120 and b < 120 and r > g + 40:
                reds.append((x, y, (r, g, b)))
    print(label, "red_n", len(reds), "sample", reds[:3], reds[-2:] if reds else None)
    # also any bright non-white
    for y in (448, 455, 460):
        row = [im.getpixel((x, y)) for x in range(x0, x1, 8)]
        print(" ", y, row[:8])
