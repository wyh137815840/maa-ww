#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
c = json.loads((ROOT / "tools/touch-review/config.json").read_text(encoding="utf-8"))
log = "/storage/emulated/0/Android/data/com.aliothmoon.maafw.maaww/files/log/maafw.log"
r = subprocess.run(
    [
        c["adb_path"],
        "-s",
        c["serial"],
        "shell",
        f"grep -n '01:02:4' {log} | head -80; echo '===='; grep -nE 'parse_|invalid|missing|ERR|WRN' {log} | grep '01:02:' | head -60",
    ],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="ignore",
)
print(r.stdout)
print(r.stderr)
