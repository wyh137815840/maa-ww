#!/usr/bin/env python3
import _local_cfg
from pathlib import Path
import json
import subprocess
import time

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
        timeout=30,
    )
    print(">>>", cmd)
    print((r.stdout or "")[:2000])
    if r.stderr:
        print("ERR", r.stderr[:500])


# unlock again more carefully
subprocess.run([adb, "-s", s, "shell", "input", "keyevent", "KEYCODE_WAKEUP"], capture_output=True)
time.sleep(0.5)
subprocess.run([adb, "-s", s, "shell", "input", "keyevent", "82"], capture_output=True)
time.sleep(0.5)
# dismiss keyguard via wm if possible
sh("wm dismiss-keyguard")
time.sleep(0.3)
subprocess.run([adb, "-s", s, "shell", "input", "text", _local_cfg.pin()], capture_output=True)
time.sleep(0.2)
subprocess.run([adb, "-s", s, "shell", "input", "keyevent", "KEYCODE_ENTER"], capture_output=True)
time.sleep(1.5)

sh("dumpsys user | head -40")
sh("cmd lock_settings get-disabled")
sh("sm list-volumes")
sh("sm get-primary-storage-uuid")
sh("ls -la /data/media/0 2>&1 | head -20")
sh("ls -la /mnt/user/0 2>&1 | head")
sh("ls -la /mnt/pass_through/0 2>&1 | head")
sh("ls -la /storage 2>&1")
sh("ls -la /mnt/installer 2>&1 | head")
sh("getprop sys.user.0.ce_available")
sh("getprop vold.has_adoptable")
sh("getprop init.svc.vold")
sh("df -h /data /data/media /storage/emulated 2>&1")
# try force mount
sh("sm has-fusebox")
sh("cmd storage-service-status 2>&1 | head -20")
