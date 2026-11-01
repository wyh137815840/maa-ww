import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "touch-review"))
from capture import capture_png
from common import load_config

cfg = load_config()
out = Path(__file__).resolve().parent / "_shots" / "now.png"
print(capture_png(cfg["adb_path"], cfg["serial"], out, cfg), out)
