#!/usr/bin/env python3
"""Short retest: start tasks, watch for leave-confirm / guidebook / combat."""
from __future__ import annotations

import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
from capture import capture_png, ensure_device
from common import load_config

OUT = ROOT / "review/inbox"
PKG = "com.aliothmoon.maafw.maaww"
LOG = "/sdcard/Android/data/com.aliothmoon.maafw.maaww/files/log/maafw.log"
LOCAL = ROOT / "tools/_shots/maafw_leave1.log"


def adb(cfg, *args):
    return subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *args],
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
    adb(cfg, "shell", "input", "text", "753698")
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_ENTER")
    time.sleep(0.5)


def snap(cfg, label):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-lf-{label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)


def dump_nodes(cfg):
    adb(cfg, "shell", "uiautomator", "dump", "/sdcard/uidump.xml")
    p = OUT / "_uidump.xml"
    adb(cfg, "pull", "/sdcard/uidump.xml", str(p))
    text = p.read_text(encoding="utf-8", errors="ignore")
    nodes = []
    for m in re.finditer(r"<node\b([^>]*)/>", text):
        attrs = m.group(1)
        text_m = re.search(r'\btext="([^"]*)"', attrs)
        desc_m = re.search(r'\bcontent-desc="([^"]*)"', attrs)
        bound_m = re.search(r'\bbounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', attrs)
        if not bound_m:
            continue
        nodes.append(
            {
                "text": text_m.group(1) if text_m else "",
                "desc": desc_m.group(1) if desc_m else "",
                "bounds": tuple(map(int, bound_m.groups())),
            }
        )
    return nodes


def tap_text(cfg, needle, contains=False, wait=1.2) -> bool:
    for n in dump_nodes(cfg):
        for v in (n["text"], n["desc"]):
            if not v:
                continue
            if (needle in v) if contains else (v == needle):
                x1, y1, x2, y2 = n["bounds"]
                adb(cfg, "shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))
                print("tap", v)
                time.sleep(wait)
                return True
    print("NOT_FOUND", needle)
    return False


def main():
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    unlock(cfg)
    adb(cfg, "shell", "am", "force-stop", PKG)
    time.sleep(1)
    adb(cfg, "shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(2.5)
    tap_text(cfg, "任务", wait=1.2)
    tap_text(cfg, "开始任务", wait=2.0)
    snap(cfg, "started")

    interesting = (
        "LeaveInstanceMenuOCR",
        "ConfirmLeaveInstance",
        "TacetLeaveConfirmOCR",
        "TacetConfirmLeave",
        "StartupPadReadyRT",
        "OpenGuidebook",
        "SolaGuidebook",
        "InTacetCombat",
        "WalkToTacetTreasure",
        "TacetWalkToTreasure",
        "Task.Failed",
        "Task.Succeeded",
    )
    for i in range(16):
        time.sleep(12)
        adb(cfg, "pull", LOG, str(LOCAL))
        text = LOCAL.read_text(encoding="utf-8", errors="ignore")
        # last 8k lines only
        lines = text.splitlines()[-8000:]
        names = []
        for l in lines:
            if "Node.Action.Starting" in l:
                m = re.search(r'"name":"([^"]+)"', l)
                if m:
                    names.append(m.group(1))
        print(f"--- {i+1} last={names[-10:]} ---")
        for k in interesting:
            n = sum(1 for l in lines if k in l and ("Action.Starting" in l or "Task." in l or "reco hit" in l))
            if n:
                print(f"  {k}: {n}")
        snap(cfg, f"p{i+1}")
        if any("WalkToTacetTreasure" in l and "Action.Starting" in l for l in lines):
            print("WALK STARTED")
            break
        if names[-3:] == ["OpenGuidebook", "OpenGuidebook"] and i > 6:
            # still stuck?
            pass

    adb(cfg, "shell", "input", "keyevent", "KEYCODE_SLEEP")
    print("DONE sleep")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
