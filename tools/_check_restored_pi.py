#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
c = json.loads((ROOT / "tools/touch-review/config.json").read_text(encoding="utf-8"))
pi = "/storage/emulated/0/Android/data/com.aliothmoon.maafw.maaww/files/pi"
cmd = f"""
echo '=== iface ==='
cat {pi}/interface.json
echo
echo '=== tasks ==='
ls -laR {pi}/tasks
echo '=== image count ==='
find {pi}/resource/image -name '*.png' 2>/dev/null | wc -l
echo '=== model ==='
ls {pi}/resource/model/ocr/rec.onnx 2>&1
echo '=== Tacet option ==='
head -c 300 {pi}/tasks/Tacet.json; echo
"""
r = subprocess.run(
    [c["adb_path"], "-s", c["serial"], "shell", cmd],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="ignore",
)
print(r.stdout)
print(r.stderr)
