#!/usr/bin/env python3
"""Unlock Odin, copy MaaEnd OCR models into MaaWW resource, restore adb pack, reload+start."""
from __future__ import annotations

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
END = "com.aliothmoon.maafw.maaend"
WW_PI = f"/storage/emulated/0/Android/data/{WW}/files/pi"
END_PI = f"/storage/emulated/0/Android/data/{END}/files/pi"


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


def tap_text(cfg, needle, y_min=0, wait=1.2):
    nodes = dump(cfg)
    for n in nodes:
        if (n["text"] == needle or n["desc"] == needle) and n["bounds"][1] >= y_min:
            x1, y1, x2, y2 = n["bounds"]
            tap(cfg, (x1 + x2) // 2, (y1 + y2) // 2, wait, needle)
            return True
    print("miss", needle, "seen=", [n["text"] or n["desc"] for n in nodes if n["text"] or n["desc"]][:15])
    return False


def snap(cfg, label):
    p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-n-{label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)


def main() -> int:
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    unlock(cfg)

    # device-side copy with toybox-friendly flags
    script = f"""
set -e
rm -rf {WW_PI}/resource
mkdir -p {WW_PI}/resource/pipeline
cp {END_PI}/resource/default_pipeline.json {WW_PI}/resource/default_pipeline.json
cp -R {END_PI}/resource/model {WW_PI}/resource/model
ls -la {WW_PI}/resource
du -sh {WW_PI}/resource/model
ls {WW_PI}/resource/model
"""
    r = adb(cfg, "shell", "sh", "-c", script)
    print("copy out:", r.stdout)
    print("copy err:", r.stderr)

    # ensure resource_adb still has pipelines (may already)
    print("pipelines:", adb(cfg, "shell", "ls", f"{WW_PI}/resource_adb/pipeline").stdout)
    if "Startup.json" not in (adb(cfg, "shell", "ls", f"{WW_PI}/resource_adb/pipeline").stdout or ""):
        adb(cfg, "shell", "mkdir", "-p", f"{WW_PI}/resource_adb/pipeline")
        for f in (ROOT / "assets/resource_adb/pipeline").glob("*.json"):
            adb(cfg, "push", str(f), f"{WW_PI}/resource_adb/pipeline/{f.name}")

    # interface Official -> ./resource ; attach resource_adb
    iface = {
        "interface_version": 2,
        "name": "MaaWW",
        "version": "v0.0.1",
        "description": "$description",
        "github": "https://cursor.com/codebase/yuanhao-wei/maa-ww",
        "languages": {"zh_cn": "locales/zh_cn.json", "en_us": "locales/en_us.json"},
        "controller": [
            {
                "name": "ADB",
                "label": "$controller.ADB.label",
                "description": "$controller.ADB.description",
                "type": "Adb",
                "attach_resource_path": ["./resource_adb"],
            }
        ],
        "resource": [
            {
                "name": "Official",
                "label": "$resource.Official.label",
                "path": ["./resource"],
            }
        ],
        "task": json.loads((ROOT / "assets/interface.json").read_text(encoding="utf-8"))["task"],
    }
    local = OUT / "_iface_models.json"
    local.write_text(json.dumps(iface, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    (ROOT / "assets/interface.json").write_text(
        json.dumps(iface, ensure_ascii=False, indent=4) + "\n", encoding="utf-8"
    )
    print(adb(cfg, "push", str(local), f"{WW_PI}/interface.json").stdout)

    adb(cfg, "logcat", "-c")
    adb(cfg, "shell", "monkey", "-p", WW, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(2.0)
    tap_text(cfg, "任务", y_min=900, wait=1.5)
    tap_text(cfg, "快捷选项", wait=1.0)
    tap_text(cfg, "重新加载项目", wait=3.5)
    tap_text(cfg, "开始任务", wait=5.0)
    snap(cfg, "withmodel-start")
    nodes = dump(cfg)
    print("status:", [n["text"] for n in nodes if n["text"] in ("空闲", "运行中", "准备中", "未在运行")])
    tap_text(cfg, "日志", wait=1.5)
    snap(cfg, "withmodel-log")
    nodes = dump(cfg)
    print("log:", [n["text"] for n in nodes if n["text"]][:80])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
