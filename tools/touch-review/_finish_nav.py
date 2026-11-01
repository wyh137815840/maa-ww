from datetime import datetime
from pathlib import Path
import time

from PIL import Image

from capture import capture_png, ensure_device
from common import load_config
from device_geom import raw_screen_size, tap720
from tacet_select_proto import find_go_buttons

cfg = load_config()
ensure_device(cfg["adb_path"], cfg["serial"])
dw, dh = raw_screen_size(cfg["adb_path"], cfg["serial"])
OUT = Path("../../review/inbox")


def snap(label):
    p = OUT / (datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{label}.png")
    print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)
    return p


def tap(x, y, w=1.3):
    print("tap", x, y, tap720(cfg["adb_path"], cfg["serial"], x, y, dw, dh))
    time.sleep(w)


# assume Terminal already open
p = snap("fin-terminal")
Image.open(p).convert("RGB").crop((480, 380, 780, 620)).save(OUT / "odin-sola-tile-crop.png")
tap(634, 500, 1.5)
p = snap("fin-sola")
tap(183, 531, 1.3)
p = snap("fin-tacet")
im = Image.open(p).convert("RGB")
btns = find_go_buttons(im)
print("btns", btns)
for i, (_cx, cy) in enumerate(btns[:4]):
    crop = im.crop((280, cy - 40, 720, cy + 25))
    crop.save(OUT / f"fin-name-{i+1}.png")
    print("name", i + 1)
