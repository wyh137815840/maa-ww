#!/usr/bin/env python3
"""Bisect attach failure: empty adb vs Startup-only vs all pipelines vs +images."""
from __future__ import annotations
import _local_cfg

import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
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
    time.sleep(0.3)
    adb(cfg, "shell", "input", "keyevent", "82")
    time.sleep(0.3)
    adb(cfg, "shell", "input", "text", _local_cfg.pin())
    time.sleep(0.2)
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_ENTER")
    time.sleep(0.7)


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
        nodes.append({"text": tm.group(1) if tm else "", "desc": dm.group(1) if dm else "", "bounds": tuple(map(int, bm.groups()))})
    return nodes


def tap(cfg, x, y, w=1.0, label=""):
    print("tap", label, x, y)
    adb(cfg, "shell", "input", "tap", str(x), str(y))
    time.sleep(w)


def tap_text(cfg, needle, y_min=0, wait=1.0):
    nodes = dump(cfg)
    for n in nodes:
        if (n["text"] == needle or n["desc"] == needle) and n["bounds"][1] >= y_min:
            x1, y1, x2, y2 = n["bounds"]
            tap(cfg, (x1 + x2) // 2, (y1 + y2) // 2, wait, needle)
            return True
    print("miss", needle)
    return False


def set_iface_attach(cfg, attach: bool):
    iface = {
        "interface_version": 2,
        "name": "MaaWW",
        "version": "v0.0.1",
        "description": "$description",
        "github": "https://cursor.com/codebase/yuanhao-wei/maa-ww",
        "languages": {"zh_cn": "locales/zh_cn.json", "en_us": "locales/en_us.json"},
        "controller": [
            {
                "name": "ADB",
                "label": "$controller.ADB.label",
                "description": "$controller.ADB.description",
                "type": "Adb",
                "attach_resource_path": ["./resource_adb"] if attach else [],
            }
        ],
        "resource": [{"name": "Official", "label": "$resource.Official.label", "path": ["./resource"]}],
        "task": json.loads((ROOT / "assets/interface.json").read_text(encoding="utf-8"))["task"],
    }
    p = OUT / "_iface_bisect.json"
    p.write_text(json.dumps(iface, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    adb(cfg, "push", str(p), f"{WW_PI}/interface.json")


def try_start(cfg, label: str) -> bool:
    unlock(cfg)
    adb(cfg, "shell", "monkey", "-p", WW, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(1.5)
    unlock(cfg)
    tap_text(cfg, "任务", y_min=900, wait=1.0)
    tap_text(cfg, "快捷选项", wait=0.8)
    tap_text(cfg, "重新加载项目", wait=2.5)
    unlock(cfg)
    adb(cfg, "shell", "monkey", "-p", WW, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(1.2)
    tap_text(cfg, "任务", y_min=900, wait=1.0)
    tap_text(cfg, "开始任务", wait=4.0)
    unlock(cfg)
    adb(cfg, "shell", "monkey", "-p", WW, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(1.0)
    tap_text(cfg, "任务", y_min=900, wait=0.8)
    tap_text(cfg, "日志", wait=1.2)
    nodes = dump(cfg)
    texts = [n["text"] for n in nodes if n["text"]]
    failed = any("资源加载失败" in t for t in texts)
    print(label, "FAIL" if failed else "PASS", [t for t in texts if "资源" in t or "失败" in t or t in ("运行中", "准备中")])
    tap_text(cfg, "关闭", wait=0.5)
    return not failed


def wipe_adb(cfg):
    adb(cfg, "shell", "rm", "-rf", f"{WW_PI}/resource_adb")
    adb(cfg, "shell", "mkdir", "-p", f"{WW_PI}/resource_adb/pipeline")
    adb(cfg, "shell", "mkdir", "-p", f"{WW_PI}/resource_adb/image")
    dp = {"Default": {"rate_limit": 1000, "pre_delay": 200, "post_delay": 200}}
    p = OUT / "_dp.json"
    p.write_text(json.dumps(dp, indent=4) + "\n", encoding="utf-8")
    adb(cfg, "push", str(p), f"{WW_PI}/resource_adb/default_pipeline.json")


def main() -> int:
    cfg = load_config()
    # ensure base still has model+stub only (remove WW pipes from base if present)
    adb(cfg, "shell", "rm", "-f", f"{WW_PI}/resource/pipeline/Startup.json")
    adb(cfg, "shell", "rm", "-f", f"{WW_PI}/resource/pipeline/Tacet.json")
    adb(cfg, "shell", "rm", "-f", f"{WW_PI}/resource/pipeline/TacetSelect.json")
    adb(cfg, "shell", "rm", "-f", f"{WW_PI}/resource/pipeline/CommonDisconnect.json")
    adb(cfg, "shell", "rm", "-f", f"{WW_PI}/resource/pipeline/SkipDialog.json")
    # ensure stub
    stub = {"MaaWWBaseStub": {"recognition": "DirectHit", "action": "DoNothing", "next": []}}
    sp = OUT / "_stub.json"
    sp.write_text(json.dumps(stub, indent=4) + "\n", encoding="utf-8")
    adb(cfg, "shell", "mkdir", "-p", f"{WW_PI}/resource/pipeline")
    adb(cfg, "push", str(sp), f"{WW_PI}/resource/pipeline/Stub.json")

    set_iface_attach(cfg, True)

    wipe_adb(cfg)
    try_start(cfg, "A-empty-adb")

    wipe_adb(cfg)
    adb(cfg, "push", str(ROOT / "assets/resource_adb/pipeline/Startup.json"), f"{WW_PI}/resource_adb/pipeline/Startup.json")
    try_start(cfg, "B-startup-only")

    wipe_adb(cfg)
    for f in (ROOT / "assets/resource_adb/pipeline").glob("*.json"):
        adb(cfg, "push", str(f), f"{WW_PI}/resource_adb/pipeline/{f.name}")
    try_start(cfg, "C-all-pipes")

    # D: all pipes + images
    img_root = ROOT / "assets/resource_adb/image"
    for png in img_root.rglob("*.png"):
        rel = png.relative_to(img_root).as_posix()
        remote_dir = f"{WW_PI}/resource_adb/image/{png.parent.relative_to(img_root).as_posix()}"
        adb(cfg, "shell", "mkdir", "-p", remote_dir)
        adb(cfg, "push", str(png), f"{WW_PI}/resource_adb/image/{rel}")
    try_start(cfg, "D-pipes+images")

    # E: no attach, WW merged in base
    set_iface_attach(cfg, False)
    for f in (ROOT / "assets/resource_adb/pipeline").glob("*.json"):
        adb(cfg, "push", str(f), f"{WW_PI}/resource/pipeline/{f.name}")
    try_start(cfg, "E-merged-base-no-attach")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
