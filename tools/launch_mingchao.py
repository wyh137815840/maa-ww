#!/usr/bin/env python3
"""Host-side ADB launch / force-stop for 鸣潮.

Mirrors the verified commands from D:\\git\\_ref_maaww:
  MainActivity.launchGame():
    Intent.setClassName(\"com.kurogame.mingchao\", \"com.epicgames.ue4.GameActivity\")
    + FLAG_ACTIVITY_REORDER_TO_FRONT
  ShizukuCaptureService.restartGame():
    am force-stop com.kurogame.mingchao
    am start -n com.kurogame.mingchao/com.epicgames.ue4.GameActivity
  ShizukuCaptureService.forceStopGame():
    am force-stop com.kurogame.mingchao

Solid MaaWW App path must use Pipeline StartApp / StopApp (see
assets/resource_adb/pipeline/Startup.json), not this script and not
game UI taps. This helper is for host diagnostics / bring-up only.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
from common import load_config  # noqa: E402

GAME_PACKAGE = "com.kurogame.mingchao"
GAME_ACTIVITY = "com.epicgames.ue4.GameActivity"
GAME_COMPONENT = f"{GAME_PACKAGE}/{GAME_ACTIVITY}"


def adb(cfg: dict, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )


def force_stop(cfg: dict) -> int:
    r = adb(cfg, "shell", "am", "force-stop", GAME_PACKAGE)
    print("force-stop", GAME_PACKAGE, "rc=", r.returncode)
    if r.stdout.strip():
        print(r.stdout.strip())
    if r.stderr.strip():
        print(r.stderr.strip())
    return r.returncode


def start(cfg: dict) -> int:
    r = adb(cfg, "shell", "am", "start", "-n", GAME_COMPONENT)
    print("am start -n", GAME_COMPONENT, "rc=", r.returncode)
    if r.stdout.strip():
        print(r.stdout.strip())
    if r.stderr.strip():
        print(r.stderr.strip())
    return r.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        choices=("start", "stop", "restart"),
        help="start=am start; stop=force-stop; restart=force-stop then start",
    )
    args = parser.parse_args()
    cfg = load_config()
    if args.mode == "stop":
        return force_stop(cfg)
    if args.mode == "restart":
        rc = force_stop(cfg)
        if rc != 0:
            return rc
        return start(cfg)
    return start(cfg)


if __name__ == "__main__":
    raise SystemExit(main())
