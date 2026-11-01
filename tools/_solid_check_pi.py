#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
from common import load_config

PKG = "com.aliothmoon.maafw.maaww"
BASE = f"/storage/emulated/0/Android/data/{PKG}/files"


def main() -> int:
    cfg = load_config()
    adb, s = cfg["adb_path"], cfg["serial"]

    def sh(*a):
        r = subprocess.run(
            [adb, "-s", s, *a],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        print("$", " ".join(a))
        print(r.stdout or r.stderr or "(empty)")

    sh("shell", "ls", "-la", BASE)
    sh("shell", "ls", "-la", f"{BASE}/pi")
    sh("shell", "ls", "-laR", f"{BASE}/pi/resource")
    sh("shell", "ls", "-la", f"{BASE}/pi.zip")
    # apk assets
    sh("shell", "pm", "path", PKG)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
