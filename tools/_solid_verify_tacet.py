#!/usr/bin/env python3
"""Solid APK verify helper: unlock, open MaaWW, screenshot UI; do NOT tap the game."""
from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
from capture import capture_png, ensure_device
from common import load_config
from device_geom import raw_screen_size, tap720

PKG = "com.aliothmoon.maafw.maaww"
OUT = ROOT / "review/inbox"


def adb(cfg, *args, check=False):
    return subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *args],
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )


def snap(cfg, label: str) -> Path:
    p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-solid-{label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)
    return p


def unlock(cfg):
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_WAKEUP")
    time.sleep(0.5)
    adb(cfg, "shell", "input", "keyevent", "82")
    time.sleep(0.4)
    adb(cfg, "shell", "input", "text", "753698")
    time.sleep(0.2)
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_ENTER")
    time.sleep(0.8)


def main() -> int:
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    dw, dh = raw_screen_size(cfg["adb_path"], cfg["serial"])
    print(f"device={cfg['serial']} raw={dw}x{dh}")

    unlock(cfg)
    snap(cfg, "hud")

    # launch MaaWW
    adb(cfg, "shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(2.5)
    snap(cfg, "app-start")

    # dismiss possible「检查更新失败」dialog — 确定 ≈ center-bottom of dialog
    # 720p coords: dialog confirm often ~ (720, 430) or (900, 480)
    for xy in [(900, 470), (720, 450), (640, 480)]:
        tap720(cfg["adb_path"], cfg["serial"], xy[0], xy[1], dw, dh)
        print("tap dismiss", xy)
        time.sleep(0.8)
    snap(cfg, "after-dismiss")

    # bottom nav: 任务 ≈ 2nd of 4 tabs
    tap720(cfg["adb_path"], cfg["serial"], 480, 680, dw, dh)
    time.sleep(1.0)
    snap(cfg, "tasks-tab")

    # shizuku package check
    r = adb(cfg, "shell", "dumpsys", "package", "moe.shizuku.privileged.api")
    print("shizuku installed=", "versionName" in (r.stdout or ""))
    r2 = adb(cfg, "shell", "sh", "-c", "ps -A | grep -i shizuku")
    print("shizuku ps=", (r2.stdout or "").strip()[:200])

    # WW package running?
    r3 = adb(cfg, "shell", "pidof", "com.kurogame.mingchao")
    print("mingchao pid=", (r3.stdout or "").strip() or "none")

    print("DONE — inspect review/inbox solid-*.png; start Tacet from App UI with Shizuku connected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
