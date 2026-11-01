#!/usr/bin/env python3
"""More read-only detail on why /sdcard looks empty while emulated claims mounted."""
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
c = json.loads((ROOT / "tools/touch-review/config.json").read_text(encoding="utf-8"))
adb, s = c["adb_path"], c["serial"]


def sh(cmd: str):
    r = subprocess.run(
        [adb, "-s", s, "shell", cmd],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=20,
    )
    print(">>>", cmd)
    print(((r.stdout or "") + (r.stderr or "")).strip()[:2500] or "(empty)")


sh("mount | grep -iE 'emulated|fuse|media|sdcard|179' | head -40")
sh("ls -la /mnt/user/0/emulated 2>&1 | head")
sh("ls -la /mnt/user/0/emulated/0 2>&1 | head")
sh("ls -la /storage/emulated 2>&1")
sh("ls -laZ /storage/emulated/0 2>&1 | head")
sh("stat /storage/emulated/0 /sdcard 2>&1")
sh("sm list-disks adoptable 2>&1")
sh("sm list-volumes all")
# can other simple apps' external dirs be seen?
sh("ls /storage/emulated/0/Android/data 2>&1 | head -20")
sh("dumpsys package com.android.settings | grep dataDir | head -3")
