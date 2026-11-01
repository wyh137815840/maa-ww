from pathlib import Path

from PIL import Image

from tacet_select_proto import find_go_buttons

inbox = Path(__file__).resolve().parents[2] / "review/inbox"
names = [
    "20261031-225652-live-before-idx1.png",
    "20261031-225705-live-after-scroll-idx6.png",
    "20261031-225723-live-after-scroll-idx12.png",
    "20261031-225656-live-after-click-idx1.png",
    "20261031-225708-live-after-click-idx6.png",
    "20261031-225727-live-after-click-idx12.png",
]
for name in names:
    p = inbox / name
    im = Image.open(p).convert("RGB")
    print(name, "btns", find_go_buttons(im))
    if "after-click" in name:
        crop = im.crop((20, 20, 480, 100))
        out = inbox / name.replace(".png", "-title.png")
        crop.save(out)
        print(" wrote", out.name)
