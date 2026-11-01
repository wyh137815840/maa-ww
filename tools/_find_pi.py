#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
c = json.loads((ROOT / "tools/touch-review/config.json").read_text(encoding="utf-8"))
adb, s = c["adb_path"], c["serial"]
WW = "com.aliothmoon.maafw.maaww"

cmds = [
    f"find /storage/emulated/0 -name 'interface.json' 2>/dev/null | head",
    f"find /data/media/0 -path '*maaww*' -name 'interface.json' 2>/dev/null | head",
    f"ls -la /data/user/0/{WW}/files/ 2>/dev/null | head -40",
    f"run-as {WW} ls -la files 2>&1 | head -40",
    f"run-as {WW} ls -la files/pi 2>&1 | head -40",
    f"ls -la /storage/emulated/0/Android/data/ | grep -i maa",
    f"stat /storage/emulated/0/Android/data/{WW} 2>&1",
    f"dumpsys package {WW} | grep -E 'legacyExternalStorage|dataDir|codePath' | head -20",
]
for cmd in cmds:
    print("====", cmd[:80])
    r = subprocess.run(
        [adb, "-s", s, "shell", cmd],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    print((r.stdout or "")[:1500])
    if r.stderr:
        print("err", r.stderr[:300])
