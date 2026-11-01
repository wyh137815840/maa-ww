#!/usr/bin/env python3
"""Force-stop App so MaaResource reloads after pipeline push; then Cold StartApp."""
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
PI = f"/storage/emulated/0/Android/data/{WW}/files/pi"
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
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_WAKEUP")
    time.sleep(0.4)
    adb(cfg, "shell", "input", "keyevent", "82")
    time.sleep(0.35)
    adb(cfg, "shell", "input", "text", "753698")
    time.sleep(0.15)
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_ENTER")
    time.sleep(0.8)


def dump(cfg):
    adb(cfg, "shell", "uiautomator", "dump", "/sdcard/uidump.xml")
    adb(cfg, "pull", "/sdcard/uidump.xml", str(OUT / "_uidump.xml"))
    text = (OUT / "_uidump.xml").read_text(encoding="utf-8", errors="ignore")
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
                "attrs": attrs,
            }
        )
    return nodes


def tap(cfg, x, y, w=1.0, label=""):
    print("tap", label, (x, y))
    adb(cfg, "shell", "input", "tap", str(x), str(y))
    time.sleep(w)


def tap_text(cfg, needle, y_min=0, wait=1.0):
    for n in dump(cfg):
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
    unlock(cfg)

    # Ensure Startup-only official bundle on device
    adb(cfg, "shell", "rm", "-rf", f"{PI}/resource/pipeline")
    adb(cfg, "shell", "mkdir", "-p", f"{PI}/resource/pipeline")
    adb(cfg, "push", str(ROOT / "assets/resource_adb/pipeline/Startup.json"), f"{PI}/resource/pipeline/Startup.json")
    dp = {"Default": {"rate_limit": 1000, "pre_delay": 200, "post_delay": 200}}
    (OUT / "_dp.json").write_text(json.dumps(dp, indent=4) + "\n", encoding="utf-8")
    adb(cfg, "push", str(OUT / "_dp.json"), f"{PI}/resource/default_pipeline.json")

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
                "attach_resource_path": [],
            }
        ],
        "resource": [{"name": "Official", "label": "$resource.Official.label", "path": ["./resource"]}],
        "task": [
            {
                "name": "Startup",
                "label": "$task.Startup.label",
                "description": "$task.Startup.description",
                "entry": "StartupMain",
                "controller": ["ADB"],
            }
        ],
    }
    (OUT / "_iface.json").write_text(json.dumps(iface, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    adb(cfg, "push", str(OUT / "_iface.json"), f"{PI}/interface.json")
    adb(cfg, "push", str(ROOT / "assets/locales/zh_cn.json"), f"{PI}/locales/zh_cn.json")
    adb(cfg, "shell", "chmod", "-R", "0777", f"{PI}/resource")

    # CRITICAL: kill App so native MaaResource is destroyed; same path otherwise keeps stale bundle
    print("force-stop", WW)
    adb(cfg, "shell", "am", "force-stop", WW)
    time.sleep(1.0)

    adb(cfg, "shell", "monkey", "-p", WW, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(3.0)
    unlock(cfg)
    tap_text(cfg, "确定", wait=0.6)
    tap_text(cfg, "任务", y_min=900, wait=1.2)

    # check first task
    for n in dump(cfg):
        if "CheckBox" in n.get("attrs", ""):
            if 'checked="true"' not in n["attrs"]:
                x1, y1, x2, y2 = n["bounds"]
                tap(cfg, (x1 + x2) // 2, (y1 + y2) // 2, 0.6, "check")
            break

    adb(cfg, "shell", "am", "force-stop", GAME)
    time.sleep(0.8)
    print("pid0", adb(cfg, "shell", "pidof", GAME).stdout.strip())
    tap_text(cfg, "开始任务", wait=12.0)
    pid = adb(cfg, "shell", "pidof", GAME).stdout.strip()
    print("pid1", pid)
    snap(cfg, "startup-kill-result")

    # pull latest run log
    r = adb(
        cfg,
        "shell",
        "ls",
        "-t",
        f"/storage/emulated/0/Android/data/{WW}/files/log/run",
    )
    latest = (r.stdout or "").split()
    latest = latest[0] if latest else ""
    if latest:
        adb(
            cfg,
            "pull",
            f"/storage/emulated/0/Android/data/{WW}/files/log/run/{latest}",
            str(OUT / "_run_latest.jsonl"),
        )
        print((OUT / "_run_latest.jsonl").read_text(encoding="utf-8", errors="ignore"))

    grep = adb(
        cfg,
        "shell",
        f"grep -E 'StartupMain|task not found|StartApp|资源加载|Task.Failed|Task.Succeeded' /storage/emulated/0/Android/data/{WW}/files/log/maafw.log | tail -40",
    )
    print(grep.stdout)

    unlock(cfg)
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_SLEEP")
    if pid:
        print("PASS", pid)
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
