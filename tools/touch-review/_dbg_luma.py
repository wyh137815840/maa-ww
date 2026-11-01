from pathlib import Path

from PIL import Image

inbox = Path(__file__).resolve().parents[2] / "review/inbox"
for name, x in [
    ("20261031-225244-odin-tacetrail-183-531.png", 1245),
    ("20261031-225924-live-scroll-top.png", 1245),
    ("20261031-205700-snap.png", 1245),
]:
    im = Image.open(inbox / name).convert("RGB")
    print("===", name)
    for y in range(140, 650, 10):
        r, g, b = im.getpixel((x, y))
        v = 0.299 * r + 0.587 * g + 0.114 * b
        left = sum(im.getpixel((x - 10, y))) / 3
        mark = "*" if v >= 160 and v > left + 10 else "."
        print(f"  y={y:3d} v={v:6.1f} left={left:6.1f} {mark}")
