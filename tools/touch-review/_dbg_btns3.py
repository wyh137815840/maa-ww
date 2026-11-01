from pathlib import Path

from PIL import Image

from tacet_select_proto import find_go_buttons

p = Path("../../review/inbox/20261031-230956-s2-g0.png")
im = Image.open(p).convert("RGB")
print("find", find_go_buttons(im))
w, h = im.size
x0, x1 = int(w * 0.88), int(w * 0.96)
print("x range", x0, x1)
for y in range(200, 700, 5):
    cnt = sum(1 for x in range(x0, x1) if sum(im.getpixel((x, y))) < 120)
    if cnt > 40:
        print(f"y={y} dark={cnt}")
