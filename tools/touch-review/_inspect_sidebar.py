#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw

p = Path(r"D:\git\maa-ww\review\inbox\20261031-222624-tacet-here-start.png")
im = Image.open(p).convert("RGB")
print(im.size)
# crop left sidebar
side = im.crop((40, 80, 280, 680))
side2 = side.resize((side.width * 2, side.height * 2))
out = Path(r"D:\git\maa-ww\tools\touch-review\_scrollbar_calib\guidebook_sidebar.png")
side2.save(out)
print("wrote", out)

# also mark pipeline click (183,531)
vis = im.copy()
dr = ImageDraw.Draw(vis)
for xy, c in [((183, 531), "red"), ((180, 450), "yellow"), ((180, 400), "cyan"), ((180, 350), "lime")]:
    x, y = xy
    dr.ellipse((x - 8, y - 8, x + 8, y + 8), outline=c, width=3)
    dr.text((x + 12, y - 8), str(xy), fill=c)
vis.crop((0, 80, 320, 680)).resize((640, 1200)).save(
    Path(r"D:\git\maa-ww\tools\touch-review\_scrollbar_calib\sidebar_marks.png")
)
