#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
c = json.loads((ROOT / "tools/touch-review/config.json").read_text(encoding="utf-8"))
adb, s = c["adb_path"], c["serial"]
cmd = r"""
echo '=== mounts ==='
mount | grep -E 'emulated|sdcard|fuse' | head -30
echo '=== emulated ==='
ls -la /storage/emulated/ 2>&1 | head
ls -la /storage/emulated/0/ 2>&1 | head
ls -la /sdcard/ 2>&1 | head
echo '=== Android ==='
ls -la /sdcard/Android 2>&1 | head
ls -la /sdcard/Android/data 2>&1 | head
echo '=== df ==='
df -h | head -20
echo '=== maaend ==='
ls /sdcard/Android/data/com.aliothmoon.maafw.maaend/files/pi/resource/model/ocr/rec.onnx 2>&1
"""
r = subprocess.run(
    [adb, "-s", s, "shell", cmd],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="ignore",
)
print(r.stdout)
print(r.stderr)
