"""Probe which gesture scrolls the tacet list on Odin."""
from datetime import datetime
from pathlib import Path
import time

from PIL import Image

from capture import capture_png, ensure_device
from common import load_config
from device_geom import raw_screen_size, swipe720, tap720
from tacet_select_proto import find_go_buttons

cfg = load_config()
ensure_device(cfg["adb_path"], cfg["serial"])
dw, dh = raw_screen_size(cfg["adb_path"], cfg["serial"])
OUT = Path("../../review/inbox")


def snap(label):
    p = OUT / (datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{label}.png")
    print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)
    im = Image.open(p).convert("RGB")
    btns = find_go_buttons(im)
    print("  btns", btns)
    if btns:
        im.crop((280, btns[0][1] - 40, 720, btns[0][1] + 25)).save(OUT / f"{p.stem}-n1.png")
    return btns


print("start", snap("scr-start"))

# A: content swipe up (reveal lower rows)
print("A content swipe up")
swipe720(cfg["adb_path"], cfg["serial"], 700, 520, 700, 220, dw, dh, 500)
time.sleep(0.7)
print("after A", snap("scr-A"))

# reset? if moved, note it. Try more swipes
print("A2 another swipe up")
swipe720(cfg["adb_path"], cfg["serial"], 700, 520, 700, 220, dw, dh, 600)
time.sleep(0.7)
print("after A2", snap("scr-A2"))

# B: drag scrollbar thumb down
print("B drag bar thumb down")
swipe720(cfg["adb_path"], cfg["serial"], 1245, 200, 1245, 450, dw, dh, 600)
time.sleep(0.7)
print("after B", snap("scr-B"))

# C: tap track mid with slight left x
print("C tap bar 1240,400")
tap720(cfg["adb_path"], cfg["serial"], 1240, 400, dw, dh)
time.sleep(0.7)
print("after C", snap("scr-C"))
