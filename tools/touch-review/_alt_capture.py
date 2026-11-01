#!/usr/bin/env python3
"""Try alternate capture paths when MuMu screencap misses the game surface."""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

from PIL import Image

adb = r"D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe"
serial = "127.0.0.1:16416"
inbox = Path(__file__).resolve().parents[2] / "review" / "inbox"


def run(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(args, capture_output=True, timeout=timeout)


def save_raw(name: str, data: bytes) -> None:
    p = inbox / name
    p.write_bytes(data)
    try:
        im = Image.open(p)
        print(name, "ok", im.size, im.convert("RGB").getpixel((im.size[0] // 2, im.size[1] // 2)))
    except Exception as exc:
        print(name, "not image", len(data), exc)


# 1) exec-out screencap
r = run([adb, "-s", serial, "exec-out", "screencap", "-p"])
save_raw("_cap-execout.png", r.stdout)

# 2) screencap to stdout via shell
r = run([adb, "-s", serial, "shell", "screencap", "-p"], timeout=20)
# may contain CRLF corruption on Windows; still try
data = r.stdout.replace(b"\r\n", b"\n")
save_raw("_cap-shell.png", data)

# 3) displays
disp = run([adb, "-s", serial, "shell", "dumpsys", "display"])
text = disp.stdout.decode("utf-8", "ignore")
for line in text.splitlines():
    if "mDisplayId" in line or "uniqueId" in line or "DisplayDeviceInfo" in line or "mCurrentLayerStack" in line:
        print(line.strip()[:160])

# 4) surfaces briefly
sf = run([adb, "-s", serial, "shell", "dumpsys", "SurfaceFlinger", "--display-id"])
print("sf-display-id", sf.stdout.decode("utf-8", "ignore")[:500])

# 5) try input keyevent for MuMu? skip
# 6) list MuMu helper binaries
ls = run([adb, "-s", serial, "shell", "ls", "/system/bin"])
bins = ls.stdout.decode("utf-8", "ignore")
for key in ("screencap", "screenshot", "nemu", "mumu"):
    if key in bins.lower():
        print("bin has", key)
