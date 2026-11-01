#!/usr/bin/env python3
from __future__ import annotations

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
WW_PI = f"/storage/emulated/0/Android/data/{WW}/files/pi"


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
    time.sleep(0.5)
    adb(cfg, "shell", "input", "keyevent", "82")
    time.sleep(0.4)
    adb(cfg, "shell", "input", "text", "753698")
    time.sleep(0.2)
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_ENTER")
    time.sleep(1.0)


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
        nodes.append({"text": tm.group(1) if tm else "", "desc": dm.group(1) if dm else "", "bounds": tuple(map(int, bm.groups()))})
    return nodes


def tap(cfg, x, y, w=1.2, label=""):
    print("tap", label, x, y)
    adb(cfg, "shell", "input", "tap", str(x), str(y))
    time.sleep(w)


def tap_text(cfg, needle, y_min=0, wait=1.2):
    nodes = dump(cfg)
    for n in nodes:
        if (n["text"] == needle or n["desc"] == needle) and n["bounds"][1] >= y_min:
            x1, y1, x2, y2 = n["bounds"]
            tap(cfg, (x1 + x2) // 2, (y1 + y2) // 2, wait, needle)
            return True
    print("miss", needle, [n["text"] for n in nodes if n["text"]][:12])
    return False


def snap(cfg, label):
    p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-n-{label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)


def main() -> int:
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    print("model?", adb(cfg, "shell", "ls", f"{WW_PI}/resource/model/ocr").stdout)
    print("stub?", adb(cfg, "shell", "ls", f"{WW_PI}/resource/pipeline").stdout)
    print("adb pipes?", adb(cfg, "shell", "ls", f"{WW_PI}/resource_adb/pipeline").stdout)
    print("iface attach?", adb(cfg, "shell", "grep", "-A2", "attach", f"{WW_PI}/interface.json").stdout)

    unlock(cfg)
    adb(cfg, "shell", "monkey", "-p", WW, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(2)
    snap(cfg, "u1")
    tap_text(cfg, "确定", wait=0.8)
    tap_text(cfg, "任务", y_min=900, wait=1.2)
    snap(cfg, "u2")
    # disable autosleep via quick options if checked
    tap_text(cfg, "快捷选项", wait=1.0)
    nodes = dump(cfg)
    print("quick", [n["text"] for n in nodes if n["text"]])
    # tap outside to close
    tap(cfg, 640, 200, 0.8, "dismiss-quick")

    adb(cfg, "shell", "am", "force-stop", "com.kurogame.mingchao")
    time.sleep(0.5)
    adb(cfg, "logcat", "-c")
    tap_text(cfg, "开始任务", wait=8.0)
    snap(cfg, "u3")
    print("pid", adb(cfg, "shell", "pidof", "com.kurogame.mingchao").stdout.strip())
    unlock(cfg)  # in case screen off during run
    adb(cfg, "shell", "monkey", "-p", WW, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(1.5)
    tap_text(cfg, "任务", y_min=900, wait=1.0)
    tap_text(cfg, "日志", wait=1.5)
    snap(cfg, "u4-log")
    nodes = dump(cfg)
    print("log", [n["text"] for n in nodes if n["text"]][:100])
    log = adb(cfg, "shell", "logcat", "-d", "-t", "300").stdout or ""
    for line in log.splitlines():
        if any(k in line for k in ("资源", "MaaRunner", "StartApp", "prepare", "mingchao", "PostBundle", "失败", "Started")):
            print(line[-240:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
