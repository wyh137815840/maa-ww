from datetime import datetime
from pathlib import Path
import subprocess
import tempfile

from PIL import Image

from common import load_config

cfg = load_config()
adb = cfg["adb_path"]
serial = cfg["serial"]
subprocess.run([adb, "connect", serial], capture_output=True, text=True)
print(subprocess.run([adb, "devices"], capture_output=True, text=True).stdout)

with tempfile.TemporaryDirectory() as tmp:
    remote = "/data/local/tmp/maa_ww_touch_review.png"
    local_raw = Path(tmp) / "raw.png"
    subprocess.run([adb, "-s", serial, "shell", "rm", "-f", remote], capture_output=True)
    r = subprocess.run(
        [adb, "-s", serial, "shell", "screencap", "-p", remote],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise SystemExit(r.stderr or r.stdout or "screencap failed")
    subprocess.run([adb, "-s", serial, "pull", remote, str(local_raw)], check=True, capture_output=True)
    subprocess.run([adb, "-s", serial, "shell", "rm", "-f", remote], capture_output=True)
    img = Image.open(local_raw).convert("RGB")

tw, th = cfg["target_size"]
if img.size != (tw, th):
    img = img.resize((tw, th), Image.Resampling.LANCZOS)

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
path = cfg["inbox_dir"] / f"{stamp}-next-ui.png"
img.save(path)
print(path)
print("size", img.size)
