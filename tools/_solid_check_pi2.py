#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
from common import load_config

PKG = "com.aliothmoon.maafw.maaww"
BASE = f"/storage/emulated/0/Android/data/{PKG}/files/pi"


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
        out = (r.stdout or r.stderr or "").strip()
        print(out[:3000] if out else "(empty)")

    sh("shell", "ls", "-la", f"{BASE}/resource_adb")
    sh("shell", "find", BASE, "-type", "f")
    sh("shell", "cat", f"{BASE}/interface.json")
    sh("shell", "cat", f"{BASE}/resource/pipeline/README.md")
    # local assets count
    local = ROOT / "assets"
    print("local resource_adb images", len(list((local / "resource_adb/image").rglob("*.png"))) if (local / "resource_adb/image").exists() else 0)
    print("local resource_adb pipeline", len(list((local / "resource_adb/pipeline").rglob("*.json"))) if (local / "resource_adb/pipeline").exists() else 0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
