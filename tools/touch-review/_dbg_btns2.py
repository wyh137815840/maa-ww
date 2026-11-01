from pathlib import Path

from PIL import Image

from tacet_select_proto import find_go_buttons

inbox = Path(__file__).resolve().parents[2] / "review/inbox"
for name in [
    "20261031-225244-odin-tacetrail-183-531.png",  # known top
    "20261031-225652-live-before-idx1.png",
    "20261031-230037-live-skip-nav.png",
    "20261031-225924-live-scroll-top.png",
]:
    p = inbox / name
    if not p.exists():
        print("missing", name)
        continue
    im = Image.open(p).convert("RGB")
    print(name, find_go_buttons(im))
    # save name crops for first 4 rows
    for i, (cx, cy) in enumerate(find_go_buttons(im)[:4]):
        crop = im.crop((280, cy - 40, 700, cy + 20))
        out = inbox / f"_name-{name[:15]}-{i+1}.png"
        crop.save(out)
        print(" ", out.name)
