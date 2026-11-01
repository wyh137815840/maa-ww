#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
c = json.loads((ROOT / "tools/touch-review/config.json").read_text(encoding="utf-8"))
pi = "/storage/emulated/0/Android/data/com.aliothmoon.maafw.maaww/files/pi"
cmd = f"""
echo '=== model ==='
ls -la {pi}/resource/model/ocr/rec.onnx 2>&1 | head -3
echo '=== pipeline ==='
ls -la {pi}/resource/pipeline 2>&1
echo '=== resource root ==='
ls -la {pi}/resource 2>&1
echo '=== iface resource ==='
grep -A5 '"resource"' {pi}/interface.json | head -20
echo '=== Startup head ==='
head -c 400 {pi}/resource/pipeline/Startup.json 2>&1
echo
echo '=== logcat maa ==='
logcat -d -t 80 | grep -iE 'maa|PostBundle|resource|pipeline|StartApp|error' | tail -40
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
