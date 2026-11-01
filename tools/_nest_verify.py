#!/usr/bin/env python3
"""Nest P1 acceptance helper: unlock, open MaaWW App, list UI nodes (step 'ui'),
start tasks from the App task page (step 'start'), watch maafw.log (step 'watch').
No game taps: only the MaaWW App UI (固化测试流程)."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
from capture import capture_png
from common import load_config

PKG = "com.aliothmoon.maafw.maaww"
LOG = f"/sdcard/Android/data/{PKG}/files/log/maafw.log"
GOLOG = f"/sdcard/Android/data/{PKG}/files/pi/debug/go-service.log"
OUT = ROOT / "tools/_shots"
SERIAL = os.environ.get("ANDROID_SERIAL") or load_config()["serial"]


def adb(cfg, *args):
    return subprocess.run(
        [cfg["adb_path"], "-s", SERIAL, *args],
        capture_output=True, text=True, encoding="utf-8", errors="ignore",
    )


def unlock(cfg):
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_WAKEUP")
    time.sleep(0.4)
    adb(cfg, "shell", "input", "keyevent", "82")
    time.sleep(0.3)
    pin = os.environ.get("ODIN_PIN", "")  # local-only PIN, never commit
    if pin:
        adb(cfg, "shell", "input", "text", pin)
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_ENTER")
    time.sleep(0.6)


def nodes(cfg):
    adb(cfg, "shell", "uiautomator", "dump", "/sdcard/uidump.xml")
    p = OUT / "_nest_uidump.xml"
    subprocess.run(
        f'cmd /c ""{cfg["adb_path"]}" -s {SERIAL} exec-out cat /sdcard/uidump.xml > "{p}""',
        shell=True,
    )
    text = p.read_text(encoding="utf-8", errors="ignore")
    out = []
    for m in re.finditer(r"<node\b([^>]*)/?>", text):
        a = m.group(1)
        t = re.search(r'\btext="([^"]*)"', a)
        d = re.search(r'\bcontent-desc="([^"]*)"', a)
        b = re.search(r'\bbounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', a)
        c = re.search(r'\bchecked="(true|false)"', a)
        if b:
            out.append((t.group(1) if t else "", d.group(1) if d else "", tuple(map(int, b.groups())),
                        c.group(1) if c else ""))
    return out


def show(cfg):
    for t, d, b, c in nodes(cfg):
        if t or d:
            print(f"{b} text={t!r} desc={d!r} checked={c}")


def tap_text(cfg, needle, contains=False, wait=1.2):
    for t, d, b, _ in nodes(cfg):
        for v in (t, d):
            if v and ((needle in v) if contains else (v == needle)):
                x1, y1, x2, y2 = b
                adb(cfg, "shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))
                print("tap", v)
                time.sleep(wait)
                return True
    print("NOT_FOUND", needle)
    return False


def snap(cfg, label):
    p = OUT / f"nest_{datetime.now().strftime('%H%M%S')}_{label}.png"
    print(capture_png(cfg["adb_path"], SERIAL, p, cfg), p.name)


def main():
    cfg = load_config()
    step = sys.argv[1] if len(sys.argv) > 1 else "ui"
    OUT.mkdir(parents=True, exist_ok=True)
    if step == "ui":
        unlock(cfg)
        adb(cfg, "shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
        time.sleep(2.5)
        show(cfg)
    elif step == "dump":
        show(cfg)
    elif step == "tap":
        tap_text(cfg, sys.argv[2], contains=len(sys.argv) > 3)
        time.sleep(1)
        show(cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
