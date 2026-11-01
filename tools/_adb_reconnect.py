#!/usr/bin/env python3
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
c = json.loads((ROOT / "tools/touch-review/config.json").read_text(encoding="utf-8"))
adb = c["adb_path"]
serial = c["serial"]
host, port = serial.split(":")

subprocess.run([adb, "kill-server"], capture_output=True)
time.sleep(1)
subprocess.run([adb, "start-server"], capture_output=True)
r = subprocess.run([adb, "connect", f"{host}:{port}"], capture_output=True, text=True)
print(r.stdout, r.stderr)
time.sleep(2)
r2 = subprocess.run([adb, "devices", "-l"], capture_output=True, text=True)
print(r2.stdout)
# also try common nearby ports if refused
if "refused" in (r.stdout + r.stderr).lower() or "offline" in r2.stdout:
    for p in range(int(port) - 5, int(port) + 6):
        if p == int(port):
            continue
        rr = subprocess.run([adb, "connect", f"{host}:{p}"], capture_output=True, text=True)
        print(f"try {p}:", rr.stdout.strip(), rr.stderr.strip())
    print(subprocess.run([adb, "devices", "-l"], capture_output=True, text=True).stdout)
