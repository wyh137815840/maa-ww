#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tacet_select_proto import detect_bar_top, find_go_buttons
from _calib_scrollbar3 import detect_thumb

a = Path(r"D:\git\maa-ww\review\inbox\20261031-222542-nav-retry-640-500.png")
b = Path(r"D:\git\maa-ww\review\inbox\20261031-222544-after-scroll-idx6.png")
for p in (a, b):
    im = Image.open(p).convert("RGB")
    print("===", p.name, im.size)
    print(" buttons", find_go_buttons(im))
    print(" bar_top", detect_bar_top(im))
    print(" thumb", detect_thumb(im))
    # sample scrollbar column
    for x in (1235, 1240, 1245, 1250, 1255):
        vals = [sum(im.getpixel((x, y))) // 3 for y in range(200, 620, 20)]
        print(f"  x={x} lum every20y", vals)
