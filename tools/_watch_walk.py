#!/usr/bin/env python3
"""Unlock, snap, poll maafw.log for Walk/Combat; sleep when done."""
from __future__ import annotations
import _local_cfg

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
LOG = "/sdcard/Android/data/com.aliothmoon.maafw.maaww/files/log/maafw.log"
GPLOG = "/data/local/tmp/maaww-gamepad.log"
LOCAL = ROOT / "tools/_shots/maafw_watch.log"


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
    adb(cfg, "shell", "input", "text", _local_cfg.pin())
    time.sleep(0.2)
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_ENTER")
    time.sleep(0.5)


def snap(cfg, label):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-w-{label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)
    return p


def pull_log(cfg):
    adb(cfg, "pull", LOG, str(LOCAL))
    return LOCAL.read_text(encoding="utf-8", errors="ignore") if LOCAL.exists() else ""


def summarize(text: str) -> None:
    keys = (
        "WalkToTacetTreasure",
        "TacetWalkToTreasure",
        "CombatLoop",
        "InTacetCombat",
        "TacetClaimReward",
        "TacetChallengeComplete",
        "Shell is not supported",
        "WriteFile failed",
        "pulseStick",
        "StartupPadSwitchOnce",
        "OpenGuidebook",
    )
    for k in keys:
        # action start only
        n = sum(1 for l in text.splitlines() if k in l and "Node.Action.Starting" in l)
        n2 = sum(1 for l in text.splitlines() if k in l)
        print(f"  {k}: action_start={n} any={n2}")
    names = []
    for l in text.splitlines():
        if "Node.Action.Starting" in l:
            m = re.search(r'"name":"([^"]+)"', l)
            if m:
                names.append(m.group(1))
    print("  last actions:", names[-15:])
    c = Counter(names)
    print("  top:", c.most_common(10))


def main():
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    unlock(cfg)
    snap(cfg, "start")
    gp = adb(cfg, "shell", "cat", GPLOG).stdout or ""
    print("gamepad:\n", gp[-500:])

    # stick pulses while UI up
    for i in range(4):
        adb(cfg, "shell", "sh", "-c", "printf '0 -30000 450\\n' > /data/local/tmp/maaww_stick")
        time.sleep(0.6)
    time.sleep(0.5)
    gp2 = adb(cfg, "shell", "cat", GPLOG).stdout or ""
    print("gamepad after stick:\n", gp2[-800:])
    snap(cfg, "after-stick")

    for i in range(24):  # ~6 min
        time.sleep(15)
        text = pull_log(cfg)
        print(f"--- poll {i+1} ---")
        summarize(text)
        snap(cfg, f"p{i+1}")
        if "WalkToTacetTreasure" in text and "Node.Action.Starting" in text:
            # check specifically
            for l in text.splitlines():
                if "WalkToTacetTreasure" in l and ("Custom" in l or "Action.Starting" in l or "ERR" in l or "pulse" in l):
                    if "register action" in l:
                        continue
                    print("WALK LINE", l[:250])
        # stop early if walk succeeded then claim
        if any(
            "TacetClaimReward" in l and "Node.Action.Starting" in l for l in text.splitlines()
        ):
            print("CLAIM ACTION SEEN")
            break

    adb(cfg, "shell", "input", "keyevent", "KEYCODE_SLEEP")
    print("sleep")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
