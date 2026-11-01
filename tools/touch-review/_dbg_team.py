from pathlib import Path
from PIL import Image
from tacet_select_proto import find_go_buttons

inbox = Path("../../review/inbox")
for name in [
    "20261031-231649-acc-after-1.png",
    "20261031-231704-acc-after-2.png",
    "20261031-231720-acc-after-3.png",
    "20261031-231736-acc-after-4.png",
]:
    im = Image.open(inbox / name).convert("RGB")
    btns = find_go_buttons(im)
    bright = sum(
        1 for y in range(640, 690) for x in range(1020, 1180, 2) if sum(im.getpixel((x, y))) > 520
    )
    rail = sum(
        1 for y in range(120, 500, 6) for x in range(35, 85, 4) if sum(im.getpixel((x, y))) < 100
    )
    lore = sum(
        1 for y in range(80, 200, 4) for x in range(900, 1200, 6) if sum(im.getpixel((x, y))) > 400
    )
    print(name, "btns", len(btns), "bright", bright, "rail", rail, "lore", lore)
