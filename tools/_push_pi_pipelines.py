#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
from common import load_config

PKG = "com.aliothmoon.maafw.maaww"
BASE = f"/sdcard/Android/data/{PKG}/files/pi"


def adb(cfg, *args):
    return subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )


def main():
    cfg = load_config()
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_WAKEUP")
    time.sleep(0.3)
    adb(cfg, "shell", "input", "keyevent", "82")
    time.sleep(0.2)
    adb(cfg, "shell", "input", "text", "753698")
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_ENTER")
    time.sleep(0.4)
    adb(cfg, "shell", "am", "force-stop", PKG)

    pairs = [
        (
            ROOT / "assets/resource_adb/pipeline/Startup.json",
            f"{BASE}/resource_adb/pipeline/Startup.json",
        ),
        (
            ROOT / "assets/resource/pipeline/Startup.json",
            f"{BASE}/resource/pipeline/Startup.json",
        ),
        (
            ROOT / "assets/resource_adb/pipeline/Tacet.json",
            f"{BASE}/resource_adb/pipeline/Tacet.json",
        ),
        (
            ROOT / "assets/resource/pipeline/Tacet.json",
            f"{BASE}/resource/pipeline/Tacet.json",
        ),
        (
            ROOT / "assets/resource_adb/image/Guidebook/TacetTreasureDist.png",
            f"{BASE}/resource_adb/image/Guidebook/TacetTreasureDist.png",
        ),
        (
            ROOT / "assets/resource/image/Guidebook/TacetTreasureDist.png",
            f"{BASE}/resource/image/Guidebook/TacetTreasureDist.png",
        ),
    ]
    for src, dst in pairs:
        r = adb(cfg, "push", str(src), dst)
        print(src.name, "->", dst, (r.stdout or r.stderr or "").strip())

    r = adb(
        cfg,
        "shell",
        "sh",
        "-c",
        f"grep -c StartupPadReadyRT {BASE}/resource_adb/pipeline/Startup.json; "
        f"grep -c InInstanceClaimHint {BASE}/resource_adb/pipeline/Startup.json; "
        f"grep -n '\"threshold\"' {BASE}/resource_adb/pipeline/Startup.json | head -5",
    )
    print(r.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
