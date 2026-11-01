from pathlib import Path

from PIL import Image

p = Path(__file__).resolve().parents[2] / "review/inbox/20261031-225924-live-scroll-top.png"
im = Image.open(p).convert("RGB")
# find light vertical thumb near right
for x in range(1220, 1275):
    ys = []
    for y in range(140, 650):
        r, g, b = im.getpixel((x, y))
        v = 0.299 * r + 0.587 * g + 0.114 * b
        if v >= 160:
            ys.append(y)
    if len(ys) >= 20:
        print(f"x={x} light_n={len(ys)} y0={ys[0]} y1={ys[-1]} span={ys[-1]-ys[0]}")
