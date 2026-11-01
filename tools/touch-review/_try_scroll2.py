"""Calibrate gentle content swipes; then select index 6 via swipe+click."""
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
        im.crop((280, btns[0][1] - 40, 700, btns[0][1] + 20)).save(OUT / f"{p.stem}-n1.png")
        print("  n1 saved")
    return im, btns


def tap(x, y, w=1.0):
    print("tap", tap720(cfg["adb_path"], cfg["serial"], x, y, dw, dh))
    time.sleep(w)


def reopen():
    tap(1235, 35, 1.0)
    tap(1235, 35, 0.8)
    time.sleep(0.5)
    tap(1198, 38, 1.5)
    tap(634, 500, 1.5)
    tap(183, 531, 1.3)
    return snap("s2-reopen")


im, btns = snap("s2-start")
if len(btns) < 3:
    print("reopen…")
    im, btns = reopen()

# gentle swipes until first button y drifts or names change — aim index 6 near bottom
# index 6 = 2 past first page of 4 → need ~2 rows of scroll
for i, (y1, y2, dur) in enumerate([(500, 400, 350), (500, 380, 400), (520, 360, 450)]):
    print(f"gentle swipe {y1}->{y2}")
    swipe720(cfg["adb_path"], cfg["serial"], 700, y1, 700, y2, dw, dh, dur)
    time.sleep(0.6)
    im, btns = snap(f"s2-g{i}")
    if not btns:
        break
    # stop when first btn no longer at ~237 (scrolled)
    if btns[0][1] > 260 or i >= 1:
        # after one successful scroll, for index 6 click 2nd visible if we moved 2 rows...
        pass

# heuristic for index 6 after scrolling so that target is bottom: keep gentle swiping
# until we have 4 buttons and first name would be ~3-4; then click bottom
# Simpler: from top, swipe enough that index6 is bottom-most, click max y
# From top, indices 1-4 visible. Need index 6 at bottom → show 3,4,5,6 → scroll by 2 rows
# One gentle swipe of ~100px content ≈ 1 row (pitch 102)

# Reset to top via reopen if drifted badly
if not btns or btns[0][1] > 280:
    im, btns = reopen()

print("scroll 2 rows for idx6")
for i in range(2):
    swipe720(cfg["adb_path"], cfg["serial"], 700, 500, 700, 398, dw, dh, 380)
    time.sleep(0.55)
    im, btns = snap(f"s2-row{i}")

if btns:
    cx, cy = max(btns, key=lambda b: b[1])
    print("click bottom", cx, cy)
    tap(cx, cy, 1.6)
    im, btns2 = snap("s2-after6")
    im.crop((20, 20, 520, 110)).save(OUT / "s2-after6-title.png")
    print("team?", len(btns2) == 0)
