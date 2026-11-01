#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
from common import load_config

PKGS = (
    "com.aliothmoon.maafw.maaww",
    "com.aliothmoon.maafw.maaend",
)


def adb(cfg, *a):
    return subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *a],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )


def main() -> int:
    cfg = load_config()
    for pkg in PKGS:
        base = f"/storage/emulated/0/Android/data/{pkg}/files"
        print("=" * 60, pkg)
        print("files:", adb(cfg, "shell", "ls", "-la", base).stdout)
        print("pi:", adb(cfg, "shell", "ls", "-la", f"{base}/pi").stdout)
        print("pi.version:", adb(cfg, "shell", "cat", f"{base}/pi.version").stdout)
        print("pi.roots:", adb(cfg, "shell", "cat", f"{base}/pi.roots").stdout)
        print(
            "resource top:",
            adb(cfg, "shell", "ls", "-la", f"{base}/pi/resource").stdout,
        )
        print(
            "resource_adb top:",
            adb(cfg, "shell", "ls", "-la", f"{base}/pi/resource_adb").stdout,
        )
        print(
            "has default_pipeline resource:",
            adb(cfg, "shell", "ls", f"{base}/pi/resource/default_pipeline.json").stdout,
        )
        print(
            "find model:",
            adb(cfg, "shell", "find", f"{base}/pi", "-type", "d", "-name", "model").stdout,
        )
        print(
            "count files:",
            adb(cfg, "shell", "sh", "-c", f"find {base}/pi -type f | wc -l").stdout,
        )
        # can shell cat a file?
        print(
            "shell read test:",
            adb(
                cfg,
                "shell",
                "sh",
                "-c",
                f"id; ls {base}/pi/interface.json; head -c 80 {base}/pi/interface.json",
            ).stdout,
        )
    # check native libs in maaww apk
    print("=== maaww lib ===")
    print(adb(cfg, "shell", "pm", "path", "com.aliothmoon.maafw.maaww").stdout)
    print(
        adb(
            cfg,
            "shell",
            "sh",
            "-c",
            "ls /data/app/*/com.aliothmoon.maafw.maaww*/lib/arm64 2>/dev/null | head",
        ).stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
