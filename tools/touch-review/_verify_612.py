"""Clean reopen then verify indices 6 and 12 only."""
from datetime import datetime
from pathlib import Path
import subprocess
import sys
import time

from PIL import Image

from capture import capture_png, ensure_device
from common import load_config
from device_geom import raw_screen_size, tap720
from tacet_select_proto import find_go_buttons

cfg = load_config()
ensure_device(cfg["adb_path"], cfg["serial"])
dw, dh = raw_screen_size(cfg["adb_path"], cfg["serial"])
OUT = Path(__file__).resolve().parents[2] / "review/inbox"
HERE = Path(__file__).resolve().parent


def snap(label):
    p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)
    return p


def tap(x, y, w=1.2):
    print("tap", tap720(cfg["adb_path"], cfg["serial"], x, y, dw, dh))
    time.sleep(w)


# Escape to HUD
for _ in range(4):
    tap(1235, 35, 0.7)
    im = Image.open(snap("esc")).convert("RGB")
    if len(find_go_buttons(im)) < 2:
        # maybe hud or terminal
        break
time.sleep(1.0)
tap(1198, 38, 1.6)
snap("v-term")
tap(634, 500, 1.5)
snap("v-sola")
tap(183, 531, 1.3)
p = snap("v-tacet")
btns = find_go_buttons(Image.open(p).convert("RGB"))
print("list btns", btns)
if len(btns) < 3:
    raise SystemExit("failed reopen")

r = subprocess.run(
    [sys.executable, str(HERE / "_live_test_select.py"), "--skip-nav", "--indices", "6,12"],
    cwd=HERE,
)
raise SystemExit(r.returncode)
