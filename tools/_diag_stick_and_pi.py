#!/usr/bin/env python3
from __future__ import annotations
import _local_cfg

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
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_WAKEUP")
    time.sleep(0.3)
    adb(cfg, "shell", "input", "keyevent", "82")
    time.sleep(0.2)
    adb(cfg, "shell", "input", "text", _local_cfg.pin())
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_ENTER")
    time.sleep(0.4)

    # pull device Startup.json
    for remote in (
        "/sdcard/Android/data/com.aliothmoon.maafw.maaww/files/pi/resource_adb/pipeline/Startup.json",
        "/sdcard/Android/data/com.aliothmoon.maafw.maaww/files/pi/resource/pipeline/Startup.json",
    ):
        local = ROOT / "tools/_shots" / ("device_" + remote.split("/")[-3] + "_Startup.json")
        adb(cfg, "pull", remote, str(local))
        text = local.read_text(encoding="utf-8", errors="ignore") if local.exists() else ""
        print(remote.split("/")[-3], "ReadyRT" in text, "roi18" in text or "[18, 667" in text, "InInstanceClaimHint" in text)
        if "StartupPadReadyRT" in text:
            i = text.find("StartupPadReadyRT")
            print(text[i : i + 180].replace("\n", " "))

    # stick write via adb push (reliable)
    payload = ROOT / "tools/_shots/_stick_payload.txt"
    payload.write_text("0 -30000 400\n", encoding="ascii")
    adb(cfg, "push", str(payload), STICK)
    adb(cfg, "shell", "chmod", "666", STICK)
    print("ls after push:", adb(cfg, "shell", "ls", "-l", STICK).stdout)
    print("cat after push:", repr(adb(cfg, "shell", "cat", STICK).stdout))
    time.sleep(1.0)
    print("GP after push:\n", adb(cfg, "shell", "cat", GPLOG).stdout)
    print("cat after pump:", repr(adb(cfg, "shell", "cat", STICK).stdout))

    # also toybox-compatible write
    adb(cfg, "shell", "sh", "-c", f"echo -e '1 -25000 350' > {STICK}; chmod 666 {STICK}; wc -c {STICK}; cat {STICK}")
    time.sleep(1.0)
    print("GP after echo -e:\n", adb(cfg, "shell", "cat", GPLOG).stdout[-600:])

    adb(cfg, "shell", "input", "keyevent", "KEYCODE_SLEEP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
