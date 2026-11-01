#!/usr/bin/env python3
"""While pump is running: write stick file, check gamepad log + stick consume."""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
from common import load_config
from capture import capture_png, ensure_device

STICK = "/data/local/tmp/maaww_stick"
GPLOG = "/data/local/tmp/maaww-gamepad.log"
OUT = ROOT / "review/inbox"


def adb(cfg, *args):
    return subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )


def main():
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    # unlock
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_WAKEUP")
    time.sleep(0.4)
    adb(cfg, "shell", "input", "keyevent", "82")
    time.sleep(0.3)
    adb(cfg, "shell", "input", "text", "753698")
    time.sleep(0.2)
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_ENTER")
    time.sleep(0.5)

    before = adb(cfg, "shell", "cat", GPLOG).stdout or ""
    print("BEFORE lines", len(before.splitlines()))
    print(before[-400:])

    # three forward pulses
    for i in range(3):
        adb(cfg, "shell", "sh", "-c", f"printf '0 -30000 400\\n' > {STICK}")
        time.sleep(0.55)
        stick = (adb(cfg, "shell", "cat", STICK).stdout or "").strip()
        print(f"pulse {i} stick_after={stick!r}")

    after = adb(cfg, "shell", "cat", GPLOG).stdout or ""
    print("AFTER:")
    print(after)
    new = [l for l in after.splitlines() if l not in before.splitlines()]
    print("NEW lines:", new)

    OUT.mkdir(parents=True, exist_ok=True)
    from datetime import datetime

    p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-stick-smoke.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)

    # pull fresh log snippet
    adb(
        cfg,
        "pull",
        "/sdcard/Android/data/com.aliothmoon.maafw.maaww/files/log/maafw.log",
        str(ROOT / "tools/_shots/maafw_now3b.log"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
