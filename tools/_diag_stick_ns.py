#!/usr/bin/env python3
"""Diagnose whether stick file is visible across adb/shell vs pump consumption."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
from common import load_config

STICK = "/data/local/tmp/maaww_stick"
GPLOG = "/data/local/tmp/maaww-gamepad.log"
PKG = "com.aliothmoon.maafw.maaww"


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
    # unlock
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_WAKEUP")
    time.sleep(0.3)
    adb(cfg, "shell", "input", "keyevent", "82")
    time.sleep(0.2)
    adb(cfg, "shell", "input", "text", "753698")
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_ENTER")
    time.sleep(0.5)

    print("=== ls before ===")
    print(adb(cfg, "shell", "ls", "-lZ", STICK, GPLOG).stdout or adb(cfg, "shell", "ls", "-l", "/data/local/tmp/").stdout)

    # ensure MaaWW running so pump exists
    adb(cfg, "shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(4)
    # if tasks not running, pump may not start — try start anyway and also write while idle
    print("=== GP before write ===")
    print(adb(cfg, "shell", "cat", GPLOG).stdout)

    # write via several methods
    for label, cmd in [
        ("printf", f"printf '11 -22000 300\\n' > {STICK}; chmod 666 {STICK}; ls -l {STICK}; od -An -tx1 {STICK} | head -1"),
        ("echo", f"echo 12 -23000 310 > {STICK}; ls -l {STICK}; cat {STICK}"),
    ]:
        print(f"=== write {label} ===")
        r = adb(cfg, "shell", "sh", "-c", cmd)
        print(r.stdout)
        print(r.stderr)
        time.sleep(0.8)
        print("cat after:", repr(adb(cfg, "shell", "cat", STICK).stdout))
        print("GP:", adb(cfg, "shell", "cat", GPLOG).stdout)

    # check if new Startup nodes exist on device PI
    print("=== device Startup pad nodes ===")
    r = adb(
        cfg,
        "shell",
        "sh",
        "-c",
        "grep -n StartupPadReady /data/user/0/com.aliothmoon.maafw.maaww/files/pi/resource*/pipeline/Startup.json 2>/dev/null | head -40; "
        "grep -n StartupPadReady /sdcard/Android/data/com.aliothmoon.maafw.maaww/files/pi*/**/Startup.json 2>/dev/null | head -20; "
        "find /data/user/0/com.aliothmoon.maafw.maaww /sdcard/Android/data/com.aliothmoon.maafw.maaww -name Startup.json 2>/dev/null | head -20",
    )
    print(r.stdout)
    print(r.stderr)

    # greplog for ReadyRT / ClaimHint / stick read
    local = ROOT / "tools/_shots/maafw_diag2.log"
    adb(cfg, "pull", "/sdcard/Android/data/com.aliothmoon.maafw.maaww/files/log/maafw.log", str(local))
    text = local.read_text(encoding="utf-8", errors="ignore") if local.exists() else ""
    for k in ("StartupPadReadyRT", "StartupPadReadyDPad", "StartupPadReadyMenu", "InInstanceClaimHint", "stick read", "stick pulse"):
        print(k, text.count(k))

    adb(cfg, "shell", "input", "keyevent", "KEYCODE_SLEEP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
