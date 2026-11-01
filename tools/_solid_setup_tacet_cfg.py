#!/usr/bin/env python3
"""Create MaaWW run config + add Tacet task (App UI only; no game taps)."""
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


def adb(cfg, *args):
    return subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )


def snap(cfg, label: str) -> Path:
    p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-cfg-{label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)
    return p


def tap(cfg, x, y, dw, dh, wait=1.0, label=""):
    print(f"tap {label} ({x},{y})", tap720(cfg["adb_path"], cfg["serial"], x, y, dw, dh))
    time.sleep(wait)


def main() -> int:
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    dw, dh = raw_screen_size(cfg["adb_path"], cfg["serial"])

    adb(cfg, "shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(2)
    # tasks tab
    tap(cfg, 480, 690, dw, dh, 1.2, "tasks-tab")
    snap(cfg, "01-tasks")

    # 选择配置
    tap(cfg, 500, 150, dw, dh, 1.0, "select-config")
    snap(cfg, "02-select")

    # try create empty / template — common sheet items mid screen
    for xy, name in [
        ((640, 360), "mid-option"),
        ((640, 300), "opt-a"),
        ((640, 420), "opt-b"),
        ((640, 480), "opt-c"),
    ]:
        tap(cfg, xy[0], xy[1], dw, dh, 0.9, name)
        snap(cfg, f"03-{name}")

    # +添加任务
    tap(cfg, 1050, 150, dw, dh, 1.2, "add-task")
    snap(cfg, "04-add-task")

    # pick Tacet if listed — scan mid list
    for y in (220, 280, 340, 400, 460, 520):
        tap(cfg, 640, y, dw, dh, 0.7, f"pick-y{y}")
        path = snap(cfg, f"05-pick-y{y}")
        # if we left picker, stop
        # heuristic: continue; user/agent will inspect images

    # open task options if Tacet added — gear/chevron on row
    tap(cfg, 1180, 280, dw, dh, 1.0, "task-options")
    snap(cfg, "06-options")

    # try select index 1
    for y in (250, 320, 390, 460):
        tap(cfg, 640, y, dw, dh, 0.6, f"case-y{y}")
    snap(cfg, "07-after-case")

    # back / confirm
    tap(cfg, 80, 60, dw, dh, 0.8, "back")
    snap(cfg, "08-back")

    # 开始任务 if enabled
    tap(cfg, 640, 620, dw, dh, 1.5, "start")
    snap(cfg, "09-start")

    print("inspect cfg-*.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
