#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
from common import load_config


def run(cfg, *args):
    r = subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    return r.stdout or ""


def main() -> int:
    cfg = load_config()
    print("=== wm size ===")
    print(run(cfg, "shell", "wm", "size"))
    print("=== displays cur= ===")
    for line in run(cfg, "shell", "dumpsys", "window", "displays").splitlines():
        if "mDisplayId" in line or "cur=" in line or "init=" in line:
            print(line)
    print("=== focus ===")
    for line in run(cfg, "shell", "dumpsys", "window", "windows").splitlines():
        if "mCurrentFocus" in line or "mFocusedApp" in line:
            print(line)
    print("=== resumed ===")
    for line in run(cfg, "shell", "dumpsys", "activity", "activities").splitlines():
        if "topResumedActivity" in line or "mResumedActivity" in line or "maafw" in line.lower():
            print(line.strip()[:200])
    print("=== packages ww ===")
    print(run(cfg, "shell", "pidof", "com.kurogame.mingchao")[:100])
    print(run(cfg, "shell", "pidof", "com.aliothmoon.maafw.maaww")[:100])
    print("=== logcat ===")
    log = run(cfg, "shell", "logcat", "-d", "-t", "120")
    for line in log.splitlines():
        low = line.lower()
        if any(k in low for k in ("maafw", "maaww", "pipeline", "shizuku", "tasker", "worker")):
            print(line[-220:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
