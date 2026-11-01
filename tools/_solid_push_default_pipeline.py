#!/usr/bin/env python3
"""Push default_pipeline.json into on-device resource_adb and retry start; capture MaaFw logs."""
from __future__ import annotations

import json
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
PI = f"/storage/emulated/0/Android/data/{PKG}/files/pi"


def adb(cfg, *a):
    return subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *a],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )


def snap(cfg, label):
    p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-n-{label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)


def dump(cfg):
    adb(cfg, "shell", "uiautomator", "dump", "/sdcard/uidump.xml")
    p = OUT / "_uidump.xml"
    adb(cfg, "pull", "/sdcard/uidump.xml", str(p))
    text = p.read_text(encoding="utf-8", errors="ignore")
    nodes = []
    for m in re.finditer(r"<node\b([^>]*)/>", text):
        attrs = m.group(1)
        tm = re.search(r'\btext="([^"]*)"', attrs)
        dm = re.search(r'\bcontent-desc="([^"]*)"', attrs)
        bm = re.search(r'\bbounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', attrs)
        if not bm:
            continue
        nodes.append(
            {
                "text": tm.group(1) if tm else "",
                "desc": dm.group(1) if dm else "",
                "bounds": tuple(map(int, bm.groups())),
            }
        )
    return nodes


def tap(cfg, x, y, w=1.2, label=""):
    print("tap", label, x, y)
    adb(cfg, "shell", "input", "tap", str(x), str(y))
    time.sleep(w)


def tap_text(cfg, needle, y_min=0, wait=1.2):
    nodes = dump(cfg)
    for n in nodes:
        if (n["text"] == needle or n["desc"] == needle) and n["bounds"][1] >= y_min:
            x1, y1, x2, y2 = n["bounds"]
            tap(cfg, (x1 + x2) // 2, (y1 + y2) // 2, wait, needle)
            return True
    print("miss", needle)
    return False


def main() -> int:
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])

    dp = {
        "Default": {
            "rate_limit": 1000,
            "pre_delay": 200,
            "post_delay": 200,
        }
    }
    local_dp = OUT / "_default_pipeline.json"
    local_dp.write_text(json.dumps(dp, indent=4) + "\n", encoding="utf-8")
    # also into repo
    repo_dp = ROOT / "assets/resource_adb/default_pipeline.json"
    repo_dp.write_text(json.dumps(dp, indent=4) + "\n", encoding="utf-8")
    print(adb(cfg, "push", str(local_dp), f"{PI}/resource_adb/default_pipeline.json").stdout)

    # validate a pipeline JSON quickly
    for name in ("Tacet.json", "Startup.json"):
        p = ROOT / "assets/resource_adb/pipeline" / name
        json.loads(p.read_text(encoding="utf-8"))
        print("ok json", name)

    adb(cfg, "logcat", "-c")
    adb(cfg, "shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(1.5)
    tap_text(cfg, "任务", y_min=900, wait=1.2)
    tap_text(cfg, "快捷选项", wait=1.0)
    tap_text(cfg, "重新加载项目", wait=3.0)
    snap(cfg, "reloaded2")
    tap_text(cfg, "开始任务", wait=3.0)
    snap(cfg, "start2")

    # log sheet
    tap_text(cfg, "日志", wait=1.5)
    snap(cfg, "log2")
    nodes = dump(cfg)
    print("log texts:", [n["text"] for n in nodes if n["text"]][:60])

    log = adb(cfg, "shell", "logcat", "-d", "-t", "400").stdout or ""
    print("=== filtered log ===")
    for line in log.splitlines():
        low = line.lower()
        if any(
            k in low
            for k in (
                "resource",
                "pipeline",
                "maafw",
                "maaresource",
                "bundle",
                "failed",
                "error",
                "ocr",
                "onnx",
            )
        ):
            print(line[-240:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
