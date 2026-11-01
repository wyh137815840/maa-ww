#!/usr/bin/env python3
from __future__ import annotations
import _local_cfg

import re
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
WW = "com.aliothmoon.maafw.maaww"


def adb(cfg, *a):
    return subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *a],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )


def unlock(cfg):
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_WAKEUP")
    time.sleep(0.4)
    adb(cfg, "shell", "input", "keyevent", "82")
    time.sleep(0.3)
    adb(cfg, "shell", "input", "text", _local_cfg.pin())
    time.sleep(0.2)
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_ENTER")
    time.sleep(0.8)


def dump(cfg):
    adb(cfg, "shell", "uiautomator", "dump", "/sdcard/uidump.xml")
    p = OUT / "_uidump.xml"
    adb(cfg, "pull", "/sdcard/uidump.xml", str(p))
    text = p.read_text(encoding="utf-8", errors="ignore")
    nodes = []
    for m in re.finditer(r"<node\b([^>]*)/>", text):
        attrs = m.group(1)
        tm = re.search(r'\btext="([^"]*)"', attrs)
        dm = re.search(r'\bcontent-desc="([^"]*)"', attrs)
        bm = re.search(r'\bbounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', attrs)
        if not bm:
            continue
        nodes.append(
            {
                "text": tm.group(1) if tm else "",
                "desc": dm.group(1) if dm else "",
                "bounds": tuple(map(int, bm.groups())),
            }
        )
    return nodes


def tap(cfg, x, y, w=1.2, label=""):
    print("tap", label, x, y)
    adb(cfg, "shell", "input", "tap", str(x), str(y))
    time.sleep(w)


def tap_text(cfg, needle, y_min=0, contains=False, wait=1.2):
    nodes = dump(cfg)
    for n in nodes:
        vals = (n["text"], n["desc"])
        hit = any((needle in v) if contains else (v == needle) for v in vals if v)
        if hit and n["bounds"][1] >= y_min:
            x1, y1, x2, y2 = n["bounds"]
            tap(cfg, (x1 + x2) // 2, (y1 + y2) // 2, wait, needle)
            return True
    print("miss", needle)
    return False


def snap(cfg, label):
    p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-n-{label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)


def main() -> int:
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    unlock(cfg)
    adb(cfg, "shell", "monkey", "-p", WW, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(2)
    snap(cfg, "app")
    # dismiss update dialog
    for _ in range(3):
        if tap_text(cfg, "确定", wait=1.0):
            snap(cfg, "dismissed")
            break
        time.sleep(0.5)
    tap_text(cfg, "任务", y_min=900, wait=1.5)
    snap(cfg, "tasks")
    tap_text(cfg, "快捷选项", wait=1.0)
    tap_text(cfg, "重新加载项目", wait=4.0)
    adb(cfg, "logcat", "-c")
    tap_text(cfg, "开始任务", wait=6.0)
    snap(cfg, "started")
    nodes = dump(cfg)
    print("status", [n["text"] for n in nodes if n["text"]])
    tap_text(cfg, "日志", wait=1.5)
    snap(cfg, "log")
    nodes = dump(cfg)
    print("log", [n["text"] for n in nodes if n["text"]][:80])
    log = adb(cfg, "shell", "logcat", "-d", "-t", "300").stdout or ""
    for line in log.splitlines():
        if any(k in line for k in ("MaaRunner", "资源", "PostBundle", "prepare", "MaaResource", "StartApp", "mingchao")):
            print(line[-260:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
