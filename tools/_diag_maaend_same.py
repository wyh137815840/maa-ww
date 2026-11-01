#!/usr/bin/env python3
"""Confirm MaaEnd fails for the same external-storage reason. No remount."""
from pathlib import Path
import json
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
c = json.loads((ROOT / "tools/touch-review/config.json").read_text(encoding="utf-8"))
adb, s = c["adb_path"], c["serial"]
END = "com.aliothmoon.maafw.maaend"


def sh(*a):
    return subprocess.run(
        [adb, "-s", s, *a],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=30,
    )


print("=== volumes (read-only) ===")
print(sh("shell", "sm", "list-volumes").stdout)
print("primary:", sh("shell", "sm", "get-primary-storage-uuid").stdout.strip())
print("sdcard Android:", sh("shell", "ls", "/sdcard/Android").stdout or sh("shell", "ls", "/sdcard/Android").stderr)

sh("logcat", "-c")
r = sh("shell", "am", "start", "-W", "-n", f"{END}/com.aliothmoon.maafw.MainActivity")
print("am start:", (r.stdout or "")[:300], (r.stderr or "")[:200])
time.sleep(2)
print("pid:", sh("shell", "pidof", END).stdout.strip() or "none")
log = sh("logcat", "-d", "-t", "120").stdout
for ln in log.splitlines():
    if any(k in ln for k in ("FATAL", "AppPaths", "external storage", "SecurityException", "maaend", "Invalid mkdirs")):
        print(ln)
