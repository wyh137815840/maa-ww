#!/usr/bin/env python3
"""Try remount primary/emulated storage so MaaWW can open."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
c = json.loads((ROOT / "tools/touch-review/config.json").read_text(encoding="utf-8"))
adb, s = c["adb_path"], c["serial"]
WW = "com.aliothmoon.maafw.maaww"


def sh(cmd: str, timeout=60):
    r = subprocess.run(
        [adb, "-s", s, "shell", cmd],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=timeout,
    )
    print(">>>", cmd)
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    if out:
        print(out[:3000])
    return r


def main() -> int:
    print("=== before ===")
    sh("sm list-volumes")
    sh("sm get-primary-storage-uuid")

    # Try mount the broken private volume and emulated
    for vol in ("private:179,2", "emulated;0", "private"):
        sh(f"sm mount '{vol}'")
        time.sleep(1)
        sh("sm list-volumes")

    # If primary is the unmountable UUID, try reset to internal (null)
    uuid = sh("sm get-primary-storage-uuid").stdout.strip()
    print("primary uuid raw:", repr(uuid))
    # Some devices accept: settings put / cmd
    sh("sm set-primary-storage-uuid null 2>&1 || true")
    sh("cmd storage set-primary-storage-uuid null 2>&1 || true")
    # Alternative known path on some AOSP
    sh("sm partition 2>&1 | head -5 || true")

    time.sleep(1)
    print("=== after mount attempts ===")
    sh("sm list-volumes")
    sh("ls /storage/emulated/0/Android 2>&1 | head")

    # If still broken, reboot (user-visible but often fixes unmounted emulated)
    still = sh("sm list-volumes").stdout
    if "emulated;0 unmounted" in still or "emulated;0" in still and "mounted" not in [
        ln for ln in still.splitlines() if "emulated;0" in ln
    ][0:1]:
        emu = [ln for ln in still.splitlines() if "emulated" in ln]
        print("emulated lines:", emu)
        if any("unmounted" in ln or "unmountable" in ln for ln in emu):
            print("=== reboot device to remount storage ===")
            sh("reboot")
            print("waiting for device...")
            subprocess.run([adb, "-s", s, "wait-for-device"], timeout=180)
            # wait for boot completed
            for i in range(60):
                boot = subprocess.run(
                    [adb, "-s", s, "shell", "getprop", "sys.boot_completed"],
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                if boot == "1":
                    break
                time.sleep(2)
            time.sleep(5)
            # unlock
            subprocess.run([adb, "-s", s, "shell", "input", "keyevent", "KEYCODE_WAKEUP"], capture_output=True)
            time.sleep(1)
            subprocess.run([adb, "-s", s, "shell", "input", "keyevent", "82"], capture_output=True)
            time.sleep(0.5)
            subprocess.run([adb, "-s", s, "shell", "input", "text", "753698"], capture_output=True)
            time.sleep(0.2)
            subprocess.run([adb, "-s", s, "shell", "input", "keyevent", "KEYCODE_ENTER"], capture_output=True)
            time.sleep(3)
            sh("wm dismiss-keyguard")
            time.sleep(2)

    print("=== final volumes ===")
    sh("sm list-volumes")
    sh("ls /storage/emulated/0/Android 2>&1 | head")
    sh("ls /sdcard/Android/data 2>&1 | head")

    # try launch MaaWW
    subprocess.run([adb, "-s", s, "logcat", "-c"], capture_output=True)
    r = subprocess.run(
        [adb, "-s", s, "shell", "am", "start", "-W", "-n", f"{WW}/com.aliothmoon.maafw.MainActivity"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    print("am start:", r.stdout, r.stderr)
    time.sleep(2)
    pid = subprocess.run(
        [adb, "-s", s, "shell", "pidof", WW],
        capture_output=True,
        text=True,
    ).stdout.strip()
    print("pid:", pid or "none")
    if not pid:
        log = subprocess.run(
            [adb, "-s", s, "logcat", "-d", "-t", "80"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        ).stdout
        for ln in log.splitlines():
            if "FATAL" in ln or "AppPaths" in ln or "external storage" in ln or "maaww" in ln.lower():
                print(ln)
        return 1
    print("PASS: MaaWW running")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
