"""Reopen tacet list then run select verify for 1,6,12."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# reopen
r = subprocess.run([sys.executable, str(HERE / "_odin_reopen_tacet.py")], cwd=HERE)
# fix wait: use finish path if reopen got empty
from datetime import datetime
import time
from PIL import Image
from capture import capture_png, ensure_device
from common import load_config
from device_geom import raw_screen_size, tap720
from tacet_select_proto import find_go_buttons

cfg = load_config()
ensure_device(cfg["adb_path"], cfg["serial"])
dw, dh = raw_screen_size(cfg["adb_path"], cfg["serial"])
OUT = HERE.parents[1] / "review/inbox"


def snap(label):
    p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{label}.png"
    capture_png(cfg["adb_path"], cfg["serial"], p, cfg)
    return p


def tap(x, y, w=1.2):
    tap720(cfg["adb_path"], cfg["serial"], x, y, dw, dh)
    time.sleep(w)


p = snap("rav-check")
btns = find_go_buttons(Image.open(p).convert("RGB"))
print("check btns", btns)
if len(btns) < 3:
    tap(1235, 35, 1.0)
    time.sleep(0.8)
    tap(1198, 38, 1.6)
    snap("rav-term")
    tap(634, 500, 1.5)
    tap(183, 531, 1.3)
    p = snap("rav-tacet")
    btns = find_go_buttons(Image.open(p).convert("RGB"))
    print("reopened btns", btns)

r2 = subprocess.run(
    [sys.executable, str(HERE / "_live_test_select.py"), "--skip-nav", "--indices", "1,6,12"],
    cwd=HERE,
)
raise SystemExit(r2.returncode)
