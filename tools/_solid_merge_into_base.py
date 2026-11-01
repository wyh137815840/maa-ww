#!/usr/bin/env python3
"""Put WW pipelines+images into base resource (with model); no attach. Then cold-start."""
from __future__ import annotations
import _local_cfg

import json
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
GAME = "com.kurogame.mingchao"


def adb(cfg, *a):
    return subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *a],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )


def unlock(cfg):
    for _ in range(2):
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
    print("miss", needle)
    return False


def snap(cfg, label):
    p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-n-{label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)


def main() -> int:
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])

    # merge pipelines into base
    adb(cfg, "shell", "mkdir", "-p", f"{WW_PI}/resource/pipeline")
    adb(cfg, "shell", "mkdir", "-p", f"{WW_PI}/resource/image")
    for f in (ROOT / "assets/resource_adb/pipeline").glob("*.json"):
        adb(cfg, "push", str(f), f"{WW_PI}/resource/pipeline/{f.name}")
        print("pipe", f.name)
    # keep stub too
    stub = ROOT / "assets/resource/pipeline/Stub.json"
    if stub.exists():
        adb(cfg, "push", str(stub), f"{WW_PI}/resource/pipeline/Stub.json")
    img_root = ROOT / "assets/resource_adb/image"
    for png in img_root.rglob("*.png"):
        rel = png.relative_to(img_root).as_posix()
        remote_dir = f"{WW_PI}/resource/image/{png.parent.relative_to(img_root).as_posix()}"
        adb(cfg, "shell", "mkdir", "-p", remote_dir)
        adb(cfg, "push", str(png), f"{WW_PI}/resource/image/{rel}")
    adb(cfg, "shell", "chmod", "-R", "0777", f"{WW_PI}/resource")

    # interface: single path, no attach
    iface = json.loads((ROOT / "assets/interface.json").read_text(encoding="utf-8"))
    iface["resource"][0]["path"] = ["./resource"]
    for c in iface.get("controller", []):
        if c.get("name") == "ADB":
            c["attach_resource_path"] = []
    (ROOT / "assets/interface.json").write_text(
        json.dumps(iface, ensure_ascii=False, indent=4) + "\n", encoding="utf-8"
    )
    adb(cfg, "push", str(ROOT / "assets/interface.json"), f"{WW_PI}/interface.json")
    print("pipes on device", adb(cfg, "shell", "ls", f"{WW_PI}/resource/pipeline").stdout)

    unlock(cfg)
    adb(cfg, "shell", "monkey", "-p", WW, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(2)
    unlock(cfg)
    tap_text(cfg, "任务", y_min=900, wait=1.2)
    tap_text(cfg, "快捷选项", wait=1.0)
    tap_text(cfg, "重新加载项目", wait=3.5)
    unlock(cfg)
    adb(cfg, "shell", "monkey", "-p", WW, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(1.5)
    tap_text(cfg, "任务", y_min=900, wait=1.0)

    adb(cfg, "shell", "am", "force-stop", GAME)
    time.sleep(0.5)
    adb(cfg, "logcat", "-c")
    tap_text(cfg, "开始任务", wait=10.0)
    snap(cfg, "merge-start")
    print("pid", adb(cfg, "shell", "pidof", GAME).stdout.strip())
    unlock(cfg)
    adb(cfg, "shell", "monkey", "-p", WW, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(1.5)
    tap_text(cfg, "任务", y_min=900, wait=1.0)
    tap_text(cfg, "日志", wait=1.5)
    snap(cfg, "merge-log")
    nodes = dump(cfg)
    print("log", [n["text"] for n in nodes if n["text"]][:100])
    print("pid2", adb(cfg, "shell", "pidof", GAME).stdout.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
