from datetime import datetime
from pathlib import Path
import subprocess
import time

from capture import capture_png, ensure_device
from common import load_config

cfg = load_config()
ensure_device(cfg["adb_path"], cfg["serial"])
# 确认 ~ dialog bottom
subprocess.run(
    [cfg["adb_path"], "-s", cfg["serial"], "shell", "input", "tap", "720", "470"],
    check=False,
)
time.sleep(1.2)
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
dest = Path(cfg["inbox_dir"]) / f"{stamp}-after-disconnect-confirm.png"
print(capture_png(cfg["adb_path"], cfg["serial"], dest, cfg))
print(dest)
