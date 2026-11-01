#!/usr/bin/env python3
"""Unlock, smoke-test stick pump, start Tacet from MaaWW App UI (no game taps)."""
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
PKG = "com.aliothmoon.maafw.maaww"
STICK = "/data/local/tmp/maaww_stick"
GPLOG = "/data/local/tmp/maaww-gamepad.log"
MAALOG = (
    "/storage/emulated/0/Android/data/com.aliothmoon.maafw.maaww/files/debug/maafw.log"
)


def adb(cfg, *args):
    return subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )


def snap(cfg, label: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-v-{label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)
    return p


def unlock(cfg):
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_WAKEUP")
    time.sleep(0.4)
    adb(cfg, "shell", "input", "keyevent", "82")
    time.sleep(0.3)
    adb(cfg, "shell", "input", "text", "753698")
    time.sleep(0.2)
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_ENTER")
    time.sleep(0.6)


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


def tap_raw(cfg, x, y, wait=1.0, label=""):
    print(f"tap {label} ({x},{y})")
    adb(cfg, "shell", "input", "tap", str(x), str(y))
    time.sleep(wait)


def tap_text(cfg, needle, contains=False, wait=1.2) -> bool:
    nodes = dump_nodes(cfg)
    for n in nodes:
        for v in (n["text"], n["desc"]):
            if not v:
                continue
            ok = (needle in v) if contains else (v == needle)
            if ok:
                x1, y1, x2, y2 = n["bounds"]
                tap_raw(cfg, (x1 + x2) // 2, (y1 + y2) // 2, wait, v)
                return True
    print("NOT_FOUND", needle)
    return False


def cat(cfg, path: str) -> str:
    r = adb(cfg, "shell", "cat", path)
    return (r.stdout or r.stderr or "").strip()


def smoke_stick(cfg) -> None:
    print("=== stick pump smoke ===")
    adb(cfg, "shell", "sh", "-c", f"echo '' > {GPLOG}; chmod 666 {GPLOG} {STICK} 2>/dev/null; true")
    # launch app so Forwarder can start
    adb(cfg, "shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(3.0)
    before = cat(cfg, GPLOG)
    print("gamepad log before:\n", before[-500:] if before else "(empty)")
    # write a forward pulse the way Go does
    adb(cfg, "shell", "sh", "-c", f"printf '0 -28000 350\\n' > {STICK}; chmod 666 {STICK}")
    time.sleep(0.8)
    after = cat(cfg, GPLOG)
    print("gamepad log after write:\n", after[-800:] if after else "(empty)")
    stick = cat(cfg, STICK)
    print("stick file now:", repr(stick))
    print("pump_seen=", ("stick pump" in after.lower()) or ("inject" in after.lower()) or ("axis" in after.lower()))


def pull_maa_tail(cfg, n=120) -> str:
    local = OUT / "maafw_verify_tail.log"
    r = adb(cfg, "shell", "sh", "-c", f"tail -n {n} {MAALOG} 2>/dev/null || true")
    local.write_text(r.stdout or "", encoding="utf-8")
    return r.stdout or ""


def start_tacet(cfg) -> None:
    print("=== start Tacet via App UI ===")
    adb(cfg, "shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(2.0)
    snap(cfg, "app")
    # dismiss dialogs
    for key in ("确定", "知道了", "取消"):
        if tap_text(cfg, key, contains=True, wait=0.8):
            snap(cfg, f"dismiss-{key}")
    tap_text(cfg, "任务", wait=1.5)
    snap(cfg, "tasks")
    # ensure 无音区 present
    nodes = dump_nodes(cfg)
    texts = [n["text"] for n in nodes if n["text"]]
    print("task texts:", texts[:30])
    if not tap_text(cfg, "开始任务", wait=2.0):
        # maybe need to scroll / already running
        tap_text(cfg, "开始", contains=True, wait=2.0)
    snap(cfg, "after-start")
    for key in ("确定", "继续", "确认", "仍要开始", "开始"):
        nodes = dump_nodes(cfg)
        if any(key == n["text"] or key in n["text"] for n in nodes):
            tap_text(cfg, key, contains=True, wait=1.2)
            snap(cfg, f"confirm-{key}")


def monitor(cfg, seconds=180) -> None:
    print(f"=== monitor {seconds}s ===")
    t0 = time.time()
    i = 0
    while time.time() - t0 < seconds:
        time.sleep(15)
        i += 1
        snap(cfg, f"poll-{i}")
        log = pull_maa_tail(cfg, 200)
        keys = (
            "WalkToTacetTreasure",
            "pulseStick",
            "WriteFile",
            "PostShell",
            "Shell is not supported",
            "ClaimReward",
            "TacetTreasureDist",
            "CombatLoop",
        )
        hits = [ln for ln in log.splitlines() if any(k in ln for k in keys)]
        print(f"-- poll {i} hits {len(hits)} --")
        for ln in hits[-25:]:
            print(ln[:240])
        gp = cat(cfg, GPLOG)
        if gp:
            print("gp tail:", " | ".join(gp.splitlines()[-6:]))
        stick = cat(cfg, STICK)
        if stick:
            print("stick:", repr(stick[:80]))


def main() -> int:
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    unlock(cfg)
    smoke_stick(cfg)
    start_tacet(cfg)
    monitor(cfg, seconds=210)
    # sleep screen
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_SLEEP")
    print("DONE sleep")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
