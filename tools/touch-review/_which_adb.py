#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from PIL import Image

adb = r"D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe"
inbox = Path(__file__).resolve().parents[2] / "review" / "inbox"
inbox.mkdir(parents=True, exist_ok=True)


def run(args: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(args, capture_output=True)


for port in ("16384", "16416"):
    serial = f"127.0.0.1:{port}"
    print(f"======== {serial} ========")
    run([adb, "connect", serial])
    echo = run([adb, "-s", serial, "shell", "echo", "ok"])
    if b"ok" not in echo.stdout:
        print("not reachable", echo.stderr[:200])
        continue

    remote = "/data/local/tmp/maa_ww_which.png"
    out = inbox / f"_which-{port}.png"
    run([adb, "-s", serial, "shell", "rm", "-f", remote])
    run([adb, "-s", serial, "shell", "screencap", "-p", remote])
    with tempfile.TemporaryDirectory() as tmp:
        local = Path(tmp) / "raw.png"
        pull = run([adb, "-s", serial, "pull", remote, str(local)])
        if not local.is_file():
            print("pull failed", pull.stderr[:200])
            continue
        im = Image.open(local).convert("RGB")
        im.save(out)
        cx, cy = im.size[0] // 2, im.size[1] // 2
        print("size", im.size, "center", im.getpixel((cx, cy)), "->", out.name)

    pid = run([adb, "-s", serial, "shell", "pidof", "com.kurogame.mingchao"])
    print("pidof mingchao=", pid.stdout.decode("utf-8", "ignore").strip() or "none")

    act = run([adb, "-s", serial, "shell", "dumpsys", "activity", "activities"])
    text = act.stdout.decode("utf-8", "ignore")
    for line in text.splitlines():
        if "topResumedActivity" in line or "mResumedActivity" in line:
            print(line.strip()[:180])
            break
