#!/usr/bin/env python3
"""Find minimal base resource that PostBundle accepts (model kept)."""
from __future__ import annotations

import json
import re
import subprocess
import sys
time = __import__("time")
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
    time.sleep(0.3)
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


def try_case(cfg, label: str) -> bool:
    adb(cfg, "shell", "monkey", "-p", WW, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(1.5)
    tap_text(cfg, "任务", y_min=900, wait=1.0)
    tap_text(cfg, "快捷选项", wait=0.8)
    tap_text(cfg, "重新加载项目", wait=2.5)
    tap_text(cfg, "开始任务", wait=4.0)
    # open log if needed
    nodes = dump(cfg)
    texts = [n["text"] for n in nodes if n["text"]]
    if "导出" not in texts:
        tap_text(cfg, "日志", wait=1.0)
        nodes = dump(cfg)
        texts = [n["text"] for n in nodes if n["text"]]
    fails = [t for t in texts if "失败" in t or "资源加载" in t]
    ok = any("资源加载失败" not in t for t in texts) and not any("资源加载失败" in t for t in texts)
    # more precise:
    failed = any("资源加载失败" in t for t in texts)
    print(label, "FAILED" if failed else "OK?", fails, [t for t in texts if "资源" in t or t in ("运行中", "准备中", "空闲")])
    tap_text(cfg, "关闭", wait=0.5)
    return not failed


def main() -> int:
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    unlock(cfg)

    # Case 1: model + default + trivial pipeline node
    stub = {"MaaWWStub": {"recognition": "DirectHit", "action": "DoNothing", "next": []}}
    local = OUT / "_stub.json"
    local.write_text(json.dumps(stub, indent=4) + "\n", encoding="utf-8")
    adb(cfg, "shell", "mkdir", "-p", f"{WW_PI}/resource/pipeline")
    adb(cfg, "push", str(local), f"{WW_PI}/resource/pipeline/Stub.json")
    # interface: only ./resource first (no attach) to isolate
    iface = {
        "interface_version": 2,
        "name": "MaaWW",
        "version": "v0.0.1",
        "description": "$description",
        "github": "https://cursor.com/codebase/yuanhao-wei/maa-ww",
        "languages": {"zh_cn": "locales/zh_cn.json", "en_us": "locales/en_us.json"},
        "controller": [{"name": "ADB", "label": "$controller.ADB.label", "description": "$controller.ADB.description", "type": "Adb", "attach_resource_path": []}],
        "resource": [{"name": "Official", "label": "$resource.Official.label", "path": ["./resource"]}],
        "task": [{"name": "Startup", "label": "$task.Startup.label", "description": "$task.Startup.description", "entry": "StartupMain", "controller": ["ADB"]}],
    }
    # keep existing tasks from file for later
    full_tasks = json.loads((ROOT / "assets/interface.json").read_text(encoding="utf-8"))["task"]
    iface["task"] = full_tasks
    il = OUT / "_iface_case.json"
    il.write_text(json.dumps(iface, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    adb(cfg, "push", str(il), f"{WW_PI}/interface.json")
    print("resource files", adb(cfg, "shell", "find", f"{WW_PI}/resource", "-type", "f").stdout[:500])
    if try_case(cfg, "C1-stub-pipe"):
        print("C1 success — stub enough")
    else:
        # Case 2: put ALL ww pipelines into base resource (no attach)
        adb(cfg, "shell", "rm", "-rf", f"{WW_PI}/resource/pipeline")
        adb(cfg, "shell", "mkdir", "-p", f"{WW_PI}/resource/pipeline")
        for f in (ROOT / "assets/resource_adb/pipeline").glob("*.json"):
            adb(cfg, "push", str(f), f"{WW_PI}/resource/pipeline/{f.name}")
        # also copy images into resource/image
        adb(cfg, "shell", "rm", "-rf", f"{WW_PI}/resource/image")
        adb(cfg, "shell", "mkdir", "-p", f"{WW_PI}/resource/image")
        img_root = ROOT / "assets/resource_adb/image"
        for png in img_root.rglob("*.png"):
            rel = png.relative_to(img_root).as_posix()
            remote_dir = f"{WW_PI}/resource/image/{png.parent.relative_to(img_root).as_posix()}"
            adb(cfg, "shell", "mkdir", "-p", remote_dir)
            adb(cfg, "push", str(png), f"{WW_PI}/resource/image/{rel}")
        adb(cfg, "shell", "chmod", "-R", "0777", f"{WW_PI}/resource")
        if try_case(cfg, "C2-ww-in-base"):
            print("C2 success — WW pipelines in base with model works")
        else:
            print("C2 failed")

    # Case 3: restore attach style if C2 worked
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
