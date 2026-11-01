from pathlib import Path

from PIL import Image

from tacet_select_proto import detect_thumb, find_go_buttons

inbox = Path(__file__).resolve().parents[2] / "review/inbox"
for name in [
    "20261031-225244-odin-tacetrail-183-531.png",
    "20261031-225924-live-scroll-top.png",
    "20261031-230329-live-before-scroll-top-0.png",
    "20261031-225705-live-after-scroll-idx6.png",
]:
    p = inbox / name
    if not p.exists():
        print("missing", name)
        continue
    im = Image.open(p).convert("RGB")
    print(name, "thumb", detect_thumb(im), "btns", find_go_buttons(im))
    # column profile at 1245
    x = 1245
    bands = []
    run = None
    for y in range(140, 650):
        r, g, b = im.getpixel((x, y))
        v = 0.299 * r + 0.587 * g + 0.114 * b
        left = sum(im.getpixel((x - 10, y))) / 3
        hit = v >= 170 and v > left + 12
        if hit:
            if run is None:
                run = [y, y]
            else:
                run[1] = y
        elif run is not None:
            if run[1] - run[0] >= 8:
                bands.append(tuple(run))
            run = None
    if run is not None and run[1] - run[0] >= 8:
        bands.append(tuple(run))
    print("  light bands@1245", bands)
