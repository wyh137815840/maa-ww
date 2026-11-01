#!/usr/bin/env python3
"""Sync local assets PI bits to device extracted pi/ and trigger reload."""
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

    # Ensure default_pipeline + cleaned resource base
    dp = {
        "Default": {
            "rate_limit": 1000,
            "pre_delay": 200,
            "post_delay": 200,
        }
    }
    (ROOT / "assets/resource_adb/default_pipeline.json").write_text(
        json.dumps(dp, indent=4) + "\n", encoding="utf-8"
    )
    base = ROOT / "assets/resource"
    base.mkdir(parents=True, exist_ok=True)
    (base / "default_pipeline.json").write_text(json.dumps(dp, indent=4) + "\n", encoding="utf-8")
    (base / "pipeline").mkdir(exist_ok=True)
    # remove README that is not JSON
    readme = base / "pipeline/README.md"
    if readme.exists():
        readme.unlink()
        print("removed resource/pipeline/README.md")

    # interface: base resource + attach adb (MaaEnd style)
    iface_path = ROOT / "assets/interface.json"
    iface = json.loads(iface_path.read_text(encoding="utf-8"))
    iface["resource"][0]["path"] = ["./resource", "./resource_adb"]
    for c in iface.get("controller", []):
        if c.get("name") == "ADB":
            c["attach_resource_path"] = []
    iface_path.write_text(json.dumps(iface, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    print("interface paths:", iface["resource"][0]["path"])

    # push trees
    for rel in (
        "interface.json",
        "locales/zh_cn.json",
        "locales/en_us.json",
        "tasks",
        "resource",
        "resource_adb",
    ):
        src = ROOT / "assets" / rel
        dst = f"{PI}/{rel.replace(chr(92), '/')}"
        if src.is_dir():
            # adb push dir
            print(adb(cfg, "push", str(src), dst).stdout or adb(cfg, "push", str(src), dst).stderr)
        else:
            print(adb(cfg, "push", str(src), dst).stdout or "")

    # remove junk on device
    adb(cfg, "shell", "rm", "-f", f"{PI}/resource/pipeline/README.md")
    adb(cfg, "shell", "rm", "-f", f"{PI}/resource_adb/image/.gitkeep")
    print("device pipelines:", adb(cfg, "shell", "ls", f"{PI}/resource_adb/pipeline").stdout)
    print("device resource:", adb(cfg, "shell", "ls", "-la", f"{PI}/resource").stdout)

    adb(cfg, "logcat", "-c")
    adb(cfg, "shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(2)
    tap_text(cfg, "任务", y_min=900, wait=1.5)
    snap(cfg, "sync-tasks")
    tap_text(cfg, "快捷选项", wait=1.0)
    tap_text(cfg, "重新加载项目", wait=3.0)
    snap(cfg, "sync-reloaded")

    # start — config may still have only Tacet; try start anyway and check log
    tap_text(cfg, "开始任务", wait=3.0)
    snap(cfg, "sync-start")
    tap_text(cfg, "日志", wait=1.5)
    snap(cfg, "sync-log")
    nodes = dump(cfg)
    print("log:", [n["text"] for n in nodes if n["text"]][:60])

    log = adb(cfg, "shell", "logcat", "-d", "-t", "200").stdout or ""
    for line in log.splitlines():
        low = line.lower()
        if any(k in low for k in ("resource", "pipeline", "maafw", "bundle", "failed", "startapp", "mingchao")):
            print(line[-240:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
