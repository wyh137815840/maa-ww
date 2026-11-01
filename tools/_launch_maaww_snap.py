import _local_cfg
from datetime import datetime
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
from capture import capture_png, ensure_device
from common import load_config

cfg = load_config()
adb, serial = cfg["adb_path"], cfg["serial"]
ensure_device(adb, serial)

# wake + pin
subprocess.run([adb, "-s", serial, "shell", "input", "keyevent", "KEYCODE_WAKEUP"], check=False)
time.sleep(0.4)
subprocess.run([adb, "-s", serial, "shell", "input", "keyevent", "82"], check=False)
time.sleep(0.3)
subprocess.run([adb, "-s", serial, "shell", "input", "text", _local_cfg.pin()], check=False)
time.sleep(0.2)
subprocess.run([adb, "-s", serial, "shell", "input", "keyevent", "KEYCODE_ENTER"], check=False)
time.sleep(0.8)

pkg = "com.aliothmoon.maafw.maaww"
r = subprocess.run([adb, "-s", serial, "shell", "pm", "path", pkg], capture_output=True, text=True)
print("pm", r.stdout.strip() or r.stderr.strip())
subprocess.run(
    [adb, "-s", serial, "shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"],
    check=False,
)
time.sleep(3)
out = ROOT / "review/inbox" / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-maaww-app.png"
print(capture_png(adb, serial, out, cfg), out.name)
