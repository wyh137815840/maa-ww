#!/usr/bin/env python3
import _local_cfg
from pathlib import Path
import json
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
c = json.loads((ROOT / "tools/touch-review/config.json").read_text(encoding="utf-8"))
adb, s = c["adb_path"], c["serial"]
WW = "com.aliothmoon.maafw.maaww"


def sh(*a):
    r = subprocess.run([adb, "-s", s, *a], capture_output=True, text=True, encoding="utf-8", errors="ignore")
    print((r.stdout or "").strip() or (r.stderr or "").strip())
    return r


print("=== pkg ===")
sh("shell", "pm", "path", WW)
sh("shell", "dumpsys", "package", WW, "|", "head")  # won't work with pipe as args

r = subprocess.run(
    [adb, "-s", s, "shell", f"pm path {WW}; dumpsys package {WW} | grep -E 'versionName|dataDir|userId' | head -20"],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="ignore",
)
print(r.stdout)

print("=== unlock + launch ===")
sh("shell", "input", "keyevent", "KEYCODE_WAKEUP")
time.sleep(0.4)
sh("shell", "input", "keyevent", "82")
time.sleep(0.3)
sh("shell", "input", "text", _local_cfg.pin())
sh("shell", "input", "keyevent", "KEYCODE_ENTER")
time.sleep(0.8)
sh("shell", "monkey", "-p", WW, "-c", "android.intent.category.LAUNCHER", "1")
time.sleep(3.0)

r = subprocess.run(
    [adb, "-s", s, "shell", f"ls -la /storage/emulated/0/Android/data/{WW}/files/; ls -la /data/user/0/{WW}/ 2>/dev/null | head"],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="ignore",
)
print(r.stdout)
print(r.stderr)
