from pathlib import Path

from PIL import Image

p = Path("../../review/inbox/20261031-230956-s2-g0.png")
im = Image.open(p).convert("RGB")
w, h = im.size
x0, x1 = int(w * 0.88), int(w * 0.96)
dark_ys = []
for y in range(max(220, int(h * 0.26)), int(h * 0.90)):
    cnt = sum(1 for x in range(x0, x1) if sum(im.getpixel((x, y))) < 120)
    if cnt > 55:
        dark_ys.append(y)
print("n dark ys", len(dark_ys), "first", dark_ys[:20], "...", dark_ys[-10:])
bands = []
if dark_ys:
    a = p0 = dark_ys[0]
    for y in dark_ys[1:]:
        if y - p0 > 3:
            bands.append((a, p0))
            a = y
        p0 = y
    bands.append((a, p0))
print("bands", bands)
for ya, yb in bands:
    hband = yb - ya + 1
    cy = (ya + yb) // 2
    xs = [x for x in range(x0, x1) if sum(im.getpixel((x, cy))) < 120]
    cx = (min(xs) + max(xs)) // 2 if xs else None
    print(f"  {ya}-{yb} h={hband} cy={cy} cx={cx} xs={len(xs)}")
