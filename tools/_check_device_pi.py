#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
c = json.loads((ROOT / "tools/touch-review/config.json").read_text(encoding="utf-8"))
adb, s = c["adb_path"], c["serial"]


def sh(*a):
    r = subprocess.run([adb, "-s", s, *a], capture_output=True, text=True, encoding="utf-8", errors="ignore")
    print("CMD", a)
    print(r.stdout or r.stderr)
    return r


sh("devices", "-l")
sh("shell", "ls", "-la", "/storage/emulated/0/Android/data/com.aliothmoon.maafw.maaww/")
sh("shell", "ls", "-la", "/storage/emulated/0/Android/data/com.aliothmoon.maafw.maaww/files/")
sh("shell", "cat", "/storage/emulated/0/Android/data/com.aliothmoon.maafw.maaww/files/pi.roots")
sh("shell", "ls", "-la", "/sdcard/Android/data/com.aliothmoon.maafw.maaww/files/")
