#!/usr/bin/env python3
"""Force-stop MaaWW, start Tacet, watch Walk + stick pump logs."""
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
GPLOG = "/data/local/tmp/maaww-gamepad.log"
STICK = "/data/local/tmp/maaww_stick"
LOCAL = ROOT / "tools/_shots/maafw_watch2.log"


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
    time.sleep(0.2)
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_ENTER")
    time.sleep(0.6)


def snap(cfg, label):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-r-{label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)
    return p


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
                print(f"tap {v} ({(x1+x2)//2},{(y1+y2)//2})")
                adb(cfg, "shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))
                time.sleep(wait)
                return True
    print("NOT_FOUND", needle)
    return False


def main():
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    unlock(cfg)

    adb(cfg, "shell", "am", "force-stop", PKG)
    time.sleep(1.0)
    adb(cfg, "shell", "sh", "-c", f"echo '' > {GPLOG}; chmod 666 {GPLOG} {STICK} 2>/dev/null; true")
    adb(cfg, "shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(3.0)
    snap(cfg, "app")
    for key in ("确定", "知道了"):
        tap_text(cfg, key, contains=True, wait=0.8)
    tap_text(cfg, "任务", wait=1.5)
    snap(cfg, "tasks")
    tap_text(cfg, "开始任务", wait=2.0)
    snap(cfg, "started")
    for key in ("确定", "继续", "仍要开始"):
        if any(key in n["text"] for n in dump_nodes(cfg)):
            tap_text(cfg, key, contains=True, wait=1.0)

    # wait association + pump
    time.sleep(8)
    gp = adb(cfg, "shell", "cat", GPLOG).stdout or ""
    print("GP early:\n", gp)

    # smoke stick after pump — Android toybox printf is broken; use adb push
    payload = ROOT / "tools/_shots/_stick_payload.txt"
    payload.parent.mkdir(parents=True, exist_ok=True)
    for i, y in enumerate((-30000, -28000, -26000)):
        payload.write_text(f"0 {y} 400\n", encoding="ascii")
        adb(cfg, "push", str(payload), STICK)
        adb(cfg, "shell", "chmod", "666", STICK)
        time.sleep(0.55)
    time.sleep(0.3)
    gp2 = adb(cfg, "shell", "cat", GPLOG).stdout or ""
    print("GP after smoke stick:\n", gp2)
    snap(cfg, "after-smoke-stick")

    for i in range(28):
        time.sleep(15)
        adb(cfg, "pull", LOG, str(LOCAL))
        text = LOCAL.read_text(encoding="utf-8", errors="ignore")
        names = []
        for l in text.splitlines():
            if "Node.Action.Starting" in l:
                m = re.search(r'"name":"([^"]+)"', l)
                if m:
                    names.append(m.group(1))
        print(f"--- poll {i+1} last={names[-12:]} top={Counter(names).most_common(8)}")
        walk_act = sum(
            1
            for l in text.splitlines()
            if "WalkToTacetTreasure" in l and "Node.Action.Starting" in l
        )
        combat_act = sum(
            1 for l in text.splitlines() if '"name":"InTacetCombat"' in l and "Node.Action.Starting" in l
        )
        print(f"    walk_action={walk_act} combat_action={combat_act}")
        gp3 = adb(cfg, "shell", "cat", GPLOG).stdout or ""
        pulses = [l for l in gp3.splitlines() if "stick pulse" in l]
        print(f"    stick_pulses={len(pulses)} last={pulses[-3:]}")
        snap(cfg, f"p{i+1}")
        if walk_act > 0 and len(pulses) > 3:
            print("WALK+STICK EVIDENCE")
            # keep a bit more for claim
        if any(
            "TacetClaimReward" in l and "Node.Action.Starting" in l for l in text.splitlines()
        ):
            print("CLAIM SEEN")
            break

    adb(cfg, "shell", "input", "keyevent", "KEYCODE_SLEEP")
    print("DONE sleep")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
