#!/usr/bin/env python3
"""Fix nested adb-push of resource/ and verify default_pipeline at bundle root."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
from common import load_config

PKG = "com.aliothmoon.maafw.maaww"
PI = f"/storage/emulated/0/Android/data/{PKG}/files/pi"


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
    print("BEFORE")
    print(adb(cfg, "shell", "find", f"{PI}/resource", "-type", "f").stdout)
    print(adb(cfg, "shell", "find", f"{PI}/resource_adb", "-maxdepth", "2", "-type", "f").stdout)

    # wipe and push files explicitly to correct places
    adb(cfg, "shell", "rm", "-rf", f"{PI}/resource")
    adb(cfg, "shell", "mkdir", "-p", f"{PI}/resource/pipeline")

    dp = {
        "Default": {
            "rate_limit": 1000,
            "pre_delay": 200,
            "post_delay": 200,
        }
    }
    local = ROOT / "review/inbox/_default_pipeline.json"
    local.write_text(json.dumps(dp, indent=4) + "\n", encoding="utf-8")
    print(adb(cfg, "push", str(local), f"{PI}/resource/default_pipeline.json").stdout)
    print(adb(cfg, "push", str(local), f"{PI}/resource_adb/default_pipeline.json").stdout)

    # Also try ONLY resource_adb as the Official path (single bundle with content)
    iface = {
        "interface_version": 2,
        "name": "MaaWW",
        "version": "v0.0.1",
        "description": "$description",
        "github": "https://cursor.com/codebase/yuanhao-wei/maa-ww",
        "languages": {
            "zh_cn": "locales/zh_cn.json",
            "en_us": "locales/en_us.json",
        },
        "controller": [
            {
                "name": "ADB",
                "label": "$controller.ADB.label",
                "description": "$controller.ADB.description",
                "type": "Adb",
                "attach_resource_path": [],
            }
        ],
        "resource": [
            {
                "name": "Official",
                "label": "$resource.Official.label",
                "path": ["./resource_adb"],
            }
        ],
        "task": json.loads((ROOT / "assets/interface.json").read_text(encoding="utf-8"))["task"],
    }
    iface_local = ROOT / "review/inbox/_iface2.json"
    iface_local.write_text(json.dumps(iface, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    print(adb(cfg, "push", str(iface_local), f"{PI}/interface.json").stdout)

    print("AFTER resource")
    print(adb(cfg, "shell", "find", f"{PI}/resource", "-type", "f").stdout)
    print("AFTER resource_adb top")
    print(adb(cfg, "shell", "ls", "-la", f"{PI}/resource_adb").stdout)
    print(adb(cfg, "shell", "ls", "-la", f"{PI}/resource_adb/default_pipeline.json").stdout)

    # enable debug via settings? skip — clear log and try start via UI quickly
    adb(cfg, "logcat", "-c")
    # dump privileged process log tag
    print("try maa resource via existing app: user must reload")
    # use run-as if possible to cat files
    print(adb(cfg, "shell", "cat", f"{PI}/resource_adb/default_pipeline.json").stdout)
    print(adb(cfg, "shell", "cat", f"{PI}/interface.json").stdout[:500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
