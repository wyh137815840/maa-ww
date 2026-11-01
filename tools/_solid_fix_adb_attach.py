#!/usr/bin/env python3
"""Keep OCR model base; replace resource_adb with clean MaaWW pack; verify load."""
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
WW = "com.aliothmoon.maafw.maaww"
WW_PI = f"/storage/emulated/0/Android/data/{WW}/files/pi"


def adb(cfg, *a):
    return subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *a],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )


def unlock(cfg):
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_WAKEUP")
    time.sleep(0.4)
    adb(cfg, "shell", "input", "keyevent", "82")
    time.sleep(0.3)
    adb(cfg, "shell", "input", "text", "753698")
    time.sleep(0.2)
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_ENTER")
    time.sleep(0.8)


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


def snap(cfg, label):
    p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-n-{label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)


def main() -> int:
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    unlock(cfg)

    # strip MaaEnd pipelines/images from base; keep model + default only
    sh = OUT / "_strip_base.sh"
    sh.write_text(
        f"""
set -e
# keep model
rm -rf {WW_PI}/resource/image {WW_PI}/resource/pipeline
mkdir -p {WW_PI}/resource/pipeline
# ensure default
test -f {WW_PI}/resource/default_pipeline.json
test -d {WW_PI}/resource/model/ocr
chmod -R 0777 {WW_PI}/resource
# rebuild resource_adb clean
rm -rf {WW_PI}/resource_adb
mkdir -p {WW_PI}/resource_adb/pipeline {WW_PI}/resource_adb/image
ls -la {WW_PI}/resource
""",
        encoding="utf-8",
        newline="\n",
    )
    adb(cfg, "push", str(sh), "/sdcard/_strip_base.sh")
    print(adb(cfg, "shell", "sh", "/sdcard/_strip_base.sh").stdout)

    dp = {"Default": {"rate_limit": 1000, "pre_delay": 200, "post_delay": 200}}
    dpl = OUT / "_dp.json"
    dpl.write_text(json.dumps(dp, indent=4) + "\n", encoding="utf-8")
    adb(cfg, "push", str(dpl), f"{WW_PI}/resource_adb/default_pipeline.json")

    for f in (ROOT / "assets/resource_adb/pipeline").glob("*.json"):
        adb(cfg, "push", str(f), f"{WW_PI}/resource_adb/pipeline/{f.name}")
        print("pipe", f.name)

    img_root = ROOT / "assets/resource_adb/image"
    for png in img_root.rglob("*.png"):
        rel = png.relative_to(img_root).as_posix()
        remote_dir = f"{WW_PI}/resource_adb/image/{png.parent.relative_to(img_root).as_posix()}"
        adb(cfg, "shell", "mkdir", "-p", remote_dir)
        adb(cfg, "push", str(png), f"{WW_PI}/resource_adb/image/{rel}")
    adb(cfg, "shell", "chmod", "-R", "0777", f"{WW_PI}/resource_adb")

    print("adb tree:", adb(cfg, "shell", "find", f"{WW_PI}/resource_adb", "-type", "f").stdout)

    # interface
    iface = json.loads((ROOT / "assets/interface.json").read_text(encoding="utf-8"))
    iface["resource"][0]["path"] = ["./resource"]
    for c in iface.get("controller", []):
        if c.get("name") == "ADB":
            c["attach_resource_path"] = ["./resource_adb"]
    local = OUT / "_iface_ok.json"
    local.write_text(json.dumps(iface, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    (ROOT / "assets/interface.json").write_text(
        json.dumps(iface, ensure_ascii=False, indent=4) + "\n", encoding="utf-8"
    )
    adb(cfg, "push", str(local), f"{WW_PI}/interface.json")

    adb(cfg, "logcat", "-c")
    adb(cfg, "shell", "monkey", "-p", WW, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(2)
    for _ in range(2):
        tap_text(cfg, "确定", wait=0.8)
    tap_text(cfg, "任务", y_min=900, wait=1.2)
    tap_text(cfg, "快捷选项", wait=1.0)
    tap_text(cfg, "重新加载项目", wait=3.5)
    tap_text(cfg, "开始任务", wait=6.0)
    snap(cfg, "attach-start")
    nodes = dump(cfg)
    print("nodes", [n["text"] for n in nodes if n["text"]][:40])
    # if log sheet not open, open it
    if not any(n["text"] == "导出" for n in nodes):
        tap_text(cfg, "日志", wait=1.5)
        nodes = dump(cfg)
    snap(cfg, "attach-log")
    print("log", [n["text"] for n in nodes if n["text"]][:80])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
