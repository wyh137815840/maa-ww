#!/usr/bin/env python3
"""Diagnose why MaaWW won't open — no UI taps except unlock if needed."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
c = json.loads((ROOT / "tools/touch-review/config.json").read_text(encoding="utf-8"))
adb, s = c["adb_path"], c["serial"]
WW = "com.aliothmoon.maafw.maaww"


def sh(*a, timeout=60):
    return subprocess.run(
        [adb, "-s", s, *a],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=timeout,
    )


def main() -> int:
    print("=== devices ===")
    print(sh("devices", "-l").stdout)

    print("=== unlock ===")
    sh("shell", "input", "keyevent", "KEYCODE_WAKEUP")
    time.sleep(0.4)
    sh("shell", "input", "keyevent", "82")
    time.sleep(0.35)
    sh("shell", "input", "text", "753698")
    time.sleep(0.15)
    sh("shell", "input", "keyevent", "KEYCODE_ENTER")
    time.sleep(1.0)

    print("=== storage ===")
    print(sh("shell", "ls", "/storage/emulated/0/Android").stdout or sh("shell", "ls", "/storage/emulated/0/Android").stderr)
    print(sh("shell", "ls", f"/storage/emulated/0/Android/data/{WW}").stdout or "(no external data dir)")

    print("=== package ===")
    print(sh("shell", f"pm path {WW}; dumpsys package {WW} | grep -E 'versionName|dataDir|enabled=' | head -15").stdout)

    print("=== clear logcat + launch ===")
    sh("logcat", "-c")
    # explicit start activity
    r = sh(
        "shell",
        "am",
        "start",
        "-W",
        "-n",
        f"{WW}/com.aliothmoon.maafw.MainActivity",
    )
    print("am start:", r.stdout, r.stderr)
    time.sleep(2.5)

    print("=== pid ===")
    print("pidof:", sh("shell", "pidof", WW).stdout.strip() or "none")

    print("=== logcat crash/fatal ===")
    log = sh("logcat", "-d", "-t", "400").stdout
    keys = ("FATAL", "AndroidRuntime", "maafw", "maaww", "AppPaths", "external", "Exception", "Error", "crash")
    hits = [ln for ln in log.splitlines() if any(k.lower() in ln.lower() for k in keys)]
    out = ROOT / "review/inbox/_maaww_crash_log.txt"
    out.write_text("\n".join(hits[-120:]), encoding="utf-8")
    print("\n".join(hits[-80:]))
    print("wrote", out)

    print("=== internal files ===")
    print(sh("shell", f"run-as {WW} ls -la files 2>&1; run-as {WW} ls -la cache 2>&1 | head").stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
