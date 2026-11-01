#!/usr/bin/env python3
"""Read-only storage status. No mount/reboot/taps."""
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
    print(((r.stdout or "") + (r.stderr or "")).strip()[:2000])


sh("sm list-volumes")
sh("sm get-primary-storage-uuid")
sh("getprop sys.boot_completed")
sh("dumpsys user | grep -E 'Current user|State:|Unlock'")
sh("ls /storage/emulated/0 2>&1 | head -5")
sh("ls /sdcard 2>&1 | head -5")
