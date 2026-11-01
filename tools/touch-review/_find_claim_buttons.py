#!/usr/bin/env python3
from pathlib import Path
from PIL import Image

p = Path(__file__).resolve().parents[2] / "review/inbox/20261031-202033-snap.png"
im = Image.open(p).convert("RGB")
# Find dark horizontal pill buttons in center band
hits = []
for y in range(300, 520):
    for x in range(400, 900):
        r, g, b = im.getpixel((x, y))
        if r < 50 and g < 50 and b < 50:
            hits.append((x, y))
if not hits:
    print("no dark pixels")
else:
    xs = [h[0] for h in hits]
    ys = [h[1] for h in hits]
    print(f"dark bbox x={min(xs)}-{max(xs)} y={min(ys)}-{max(ys)} n={len(hits)}")
    # sample mid of left/right halves
    midy = (min(ys) + max(ys)) // 2
    leftx = min(xs) + 40
    rightx = (min(xs) + max(xs)) // 2 + 40
    for label, x in [("L", leftx), ("R", rightx)]:
        # scan upward/down for non-dark (digit color)
        for dy in range(-15, 16):
            for dx in range(0, 80):
                px = im.getpixel((x + dx, midy + dy))
                if px[0] > 180 or px[0] < 100:  # white-ish or red-ish
                    if not (px[0] < 50 and px[1] < 50 and px[2] < 50):
                        if abs(px[0] - px[1]) > 30 or px[0] > 200:
                            print(label, "sample", x + dx, midy + dy, px)
                            break
            else:
                continue
            break

# Also check 201915 and list red-ish pixels in button region
for name in ["20261031-201915-tacet-stamina.png", "20261031-202033-snap.png"]:
    im = Image.open(Path(__file__).resolve().parents[2] / "review/inbox" / name).convert("RGB")
    reds = []
    whites = []
    for y in range(360, 480):
        for x in range(450, 880):
            r, g, b = im.getpixel((x, y))
            if r > 160 and g < 100 and b < 100:
                reds.append((x, y, (r, g, b)))
            elif r > 200 and g > 200 and b > 200 and not (r > 240 and g > 240 and b > 240):
                pass
            elif 180 < r < 255 and 180 < g < 255 and 180 < b < 255 and max(r, g, b) - min(r, g, b) < 25:
                # near-white text on dark? white text is high RGB on dark bg
                if r > 200 and g > 200 and b > 200:
                    # need dark neighbors
                    if x > 0:
                        nr, ng, nb = im.getpixel((x, y + 1)) if y + 1 < 720 else (0, 0, 0)
                        if nr < 60:
                            whites.append((x, y, (r, g, b)))
    print(name, "red_count", len(reds), "white_on_dark", len(whites))
    if reds:
        print("  first reds", reds[:5], "last", reds[-3:])
    if whites:
        print("  first whites", whites[:5])
