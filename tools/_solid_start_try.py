#!/usr/bin/env python3
"""Force-start: clear logcat, multi-method tap Start, capture status + logs."""
from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
from capture import capture_png, ensure_device
from common import load_config

OUT = ROOT / "review/inbox"
PKG = "com.aliothmoon.maafw.maaww"


def adb(cfg, *args):
    return subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )


def main() -> int:
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    adb(cfg, "shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(1.0)
    # tasks tab raw
    adb(cfg, "shell", "input", "tap", "720", "942")
    time.sleep(1.0)

    adb(cfg, "logcat", "-c")
    # Button center from dump
    x, y = 839, 849
    methods = [
        ("tap", ["shell", "input", "tap", str(x), str(y)]),
        ("tap-d0", ["shell", "input", "-d", "0", "tap", str(x), str(y)]),
        ("swipe", ["shell", "input", "swipe", str(x), str(y), str(x), str(y), "80"]),
        ("motion", None),  # special
    ]
    for name, args in methods:
        print("=== method", name)
        if name == "motion":
            adb(cfg, "shell", "input", "motionevent", "DOWN", str(x), str(y))
            time.sleep(0.05)
            adb(cfg, "shell", "input", "motionevent", "UP", str(x), str(y))
        else:
            r = adb(cfg, *args)
            if r.stderr:
                print("stderr", r.stderr[:200])
            if r.stdout:
                print("stdout", r.stdout[:200])
        time.sleep(2.0)
        p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-n-start-{name}.png"
        print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)
        # dump status texts
        adb(cfg, "shell", "uiautomator", "dump", "/sdcard/uidump.xml")
        adb(cfg, "pull", "/sdcard/uidump.xml", str(OUT / "_uidump.xml"))
        text = (OUT / "_uidump.xml").read_text(encoding="utf-8", errors="ignore")
        for key in ("空闲", "运行", "准备", "错误", "失败", "停止", "开始任务", "未在运行"):
            if key in text:
                print("  has:", key)

    log = adb(cfg, "shell", "logcat", "-d", "-t", "200").stdout or ""
    print("=== log filtered ===")
    for line in log.splitlines():
        low = line.lower()
        if any(k in low for k in ("maafw", "maaww", "runner", "session", "start", "pipeline", "error", "toast")):
            print(line[-240:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
