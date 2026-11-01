#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "review/inbox"
c = json.loads((ROOT / "tools/touch-review/config.json").read_text(encoding="utf-8"))
ww = "/storage/emulated/0/Android/data/com.aliothmoon.maafw.maaww"
cmd = f"""
echo '=== find logs ==='
find {ww} -type f \\( -name '*.log' -o -name '*log*' -o -name '*.txt' \\) 2>/dev/null | head -80
echo '=== files dir ==='
ls -laR {ww}/files 2>/dev/null | head -120
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
# also dump logcat filtered for maaww package
r2 = subprocess.run(
    [c["adb_path"], "-s", c["serial"], "logcat", "-d", "-t", "500"],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="ignore",
)
keys = ("MaaResource", "PostBundle", "资源", "Prepare", "pipeline", "maaww", "MaaRunner", "StartApp", "任务失败", "error", "Error")
lines = [ln for ln in r2.stdout.splitlines() if any(k.lower() in ln.lower() for k in keys)]
(OUT / "_logcat_maa.txt").write_text("\n".join(lines[-200:]), encoding="utf-8")
print("logcat hits", len(lines))
print("\n".join(lines[-80:]))
