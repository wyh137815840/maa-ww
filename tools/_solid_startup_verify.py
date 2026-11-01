#!/usr/bin/env python3
"""Push single-bundle PI, keep only Startup enabled, cold-start, assert mingchao pid."""
from __future__ import annotations
import _local_cfg

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
from device_geom import raw_screen_size

OUT = ROOT / "review/inbox"
WW = "com.aliothmoon.maafw.maaww"
END = "com.aliothmoon.maafw.maaend"
WW_PI = f"/storage/emulated/0/Android/data/{WW}/files/pi"
END_PI = f"/storage/emulated/0/Android/data/{END}/files/pi"
GAME = "com.kurogame.mingchao"


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
    time.sleep(0.35)
    adb(cfg, "shell", "input", "text", _local_cfg.pin())
    time.sleep(0.2)
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_ENTER")
    time.sleep(0.9)


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


def tap_text(cfg, needle, y_min=0, contains=False, wait=1.2):
    nodes = dump(cfg)
    for n in nodes:
        vals = (n["text"], n["desc"])
        hit = any((needle in v) if contains else (v == needle) for v in vals if v)
        if hit and n["bounds"][1] >= y_min:
            x1, y1, x2, y2 = n["bounds"]
            tap(cfg, (x1 + x2) // 2, (y1 + y2) // 2, wait, needle)
            return True
    print("miss", needle)
    return False


def snap(cfg, label):
    p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-n-{label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)
    return p


def sleep_device(cfg):
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_SLEEP")


def ensure_model(cfg):
    check = adb(cfg, "shell", "ls", f"{WW_PI}/resource/model/ocr/rec.onnx").stdout
    if "rec.onnx" in check:
        print("model ok")
        return
    print("copying model from MaaEnd…")
    sh = OUT / "_cp_model.sh"
    sh.write_text(
        f"""
set -e
mkdir -p {WW_PI}/resource
rm -rf {WW_PI}/resource/model
cp -R {END_PI}/resource/model {WW_PI}/resource/model
cp {END_PI}/resource/default_pipeline.json {WW_PI}/resource/default_pipeline.json || true
chmod -R 0777 {WW_PI}/resource/model
ls {WW_PI}/resource/model/ocr | head
""",
        encoding="utf-8",
        newline="\n",
    )
    adb(cfg, "push", str(sh), "/sdcard/_cp_model.sh")
    print(adb(cfg, "shell", "sh", "/sdcard/_cp_model.sh").stdout)


def push_official_bundle(cfg):
    # sync local resource_adb → resource on host first
    subprocess.run([sys.executable, str(ROOT / "tools/sync_resource_from_adb.py")], check=False)

    adb(cfg, "shell", "mkdir", "-p", f"{WW_PI}/resource/pipeline")
    adb(cfg, "shell", "mkdir", "-p", f"{WW_PI}/resource/image")
    adb(cfg, "push", str(ROOT / "assets/resource/default_pipeline.json"), f"{WW_PI}/resource/default_pipeline.json")
    # clear old pipes then push
    adb(cfg, "shell", "rm", "-rf", f"{WW_PI}/resource/pipeline")
    adb(cfg, "shell", "mkdir", "-p", f"{WW_PI}/resource/pipeline")
    for f in (ROOT / "assets/resource_adb/pipeline").glob("*.json"):
        adb(cfg, "push", str(f), f"{WW_PI}/resource/pipeline/{f.name}")
        print("pipe", f.name)
    adb(cfg, "shell", "rm", "-rf", f"{WW_PI}/resource/image")
    adb(cfg, "shell", "mkdir", "-p", f"{WW_PI}/resource/image")
    img_root = ROOT / "assets/resource_adb/image"
    for png in img_root.rglob("*.png"):
        rel = png.relative_to(img_root).as_posix()
        remote_dir = f"{WW_PI}/resource/image/{png.parent.relative_to(img_root).as_posix()}"
        adb(cfg, "shell", "mkdir", "-p", remote_dir)
        adb(cfg, "push", str(png), f"{WW_PI}/resource/image/{rel}")
    adb(cfg, "push", str(ROOT / "assets/interface.json"), f"{WW_PI}/interface.json")
    adb(cfg, "push", str(ROOT / "assets/locales/zh_cn.json"), f"{WW_PI}/locales/zh_cn.json")
    adb(cfg, "push", str(ROOT / "assets/locales/en_us.json"), f"{WW_PI}/locales/en_us.json")
    adb(cfg, "push", str(ROOT / "assets/tasks"), f"{WW_PI}/tasks")
    adb(cfg, "shell", "chmod", "-R", "0777", f"{WW_PI}/resource")
    print("pipes", adb(cfg, "shell", "ls", f"{WW_PI}/resource/pipeline").stdout)


def uncheck_tacet_keep_startup(cfg):
    """Ensure Startup checked, Tacet unchecked via checkbox taps if needed."""
    nodes = dump(cfg)
    # CheckBoxes near task rows — first is often Startup, second Tacet
    boxes = []
    for n in nodes:
        # dump doesn't include class; re-dump with heuristic from earlier: clickable CheckBox
        pass
    # Use uidump with class
    adb(cfg, "shell", "uiautomator", "dump", "/sdcard/uidump.xml")
    adb(cfg, "pull", "/sdcard/uidump.xml", str(OUT / "_uidump.xml"))
    text = (OUT / "_uidump.xml").read_text(encoding="utf-8", errors="ignore")
    checks = []
    for m in re.finditer(r"<node\b([^>]*)/>", text):
        attrs = m.group(1)
        if 'class="android.widget.CheckBox"' not in attrs and "CheckBox" not in attrs:
            continue
        bm = re.search(r'\bbounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', attrs)
        checked = re.search(r'\bchecked="([^"]*)"', attrs)
        if not bm:
            continue
        checks.append((tuple(map(int, bm.groups())), checked.group(1) if checked else "?"))
    print("checkboxes", checks)
    # Task texts
    texts = [(n["text"], n["bounds"]) for n in dump(cfg) if n["text"] in ("启动进游戏", "无音区") or "启动" in n["text"]]
    print("task rows", texts)
    # If two checkboxes: ensure first checked, second unchecked
    if len(checks) >= 2:
        (x1, y1, x2, y2), c0 = checks[0]
        (a1, b1, a2, b2), c1 = checks[1]
        if c0 == "false":
            tap(cfg, (x1 + x2) // 2, (y1 + y2) // 2, 0.8, "check-startup")
        if c1 == "true":
            tap(cfg, (a1 + a2) // 2, (b1 + b2) // 2, 0.8, "uncheck-tacet")


def main() -> int:
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    OUT.mkdir(parents=True, exist_ok=True)
    unlock(cfg)
    ensure_model(cfg)
    push_official_bundle(cfg)

    adb(cfg, "shell", "monkey", "-p", WW, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(2)
    unlock(cfg)
    for _ in range(2):
        tap_text(cfg, "确定", wait=0.7)
    tap_text(cfg, "任务", y_min=900, wait=1.2)
    snap(cfg, "su-tasks")
    tap_text(cfg, "快捷选项", wait=1.0)
    tap_text(cfg, "重新加载项目", wait=3.5)
    unlock(cfg)
    adb(cfg, "shell", "monkey", "-p", WW, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(1.5)
    tap_text(cfg, "任务", y_min=900, wait=1.0)
    uncheck_tacet_keep_startup(cfg)
    snap(cfg, "su-ready")

    adb(cfg, "shell", "am", "force-stop", GAME)
    time.sleep(0.8)
    print("pid before", repr(adb(cfg, "shell", "pidof", GAME).stdout.strip()))
    adb(cfg, "logcat", "-c")
    tap_text(cfg, "开始任务", wait=12.0)
    unlock(cfg)
    pid = adb(cfg, "shell", "pidof", GAME).stdout.strip()
    print("pid after", repr(pid))
    snap(cfg, "su-after")

    # bring app back for logs
    adb(cfg, "shell", "monkey", "-p", WW, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(1.5)
    unlock(cfg)
    tap_text(cfg, "任务", y_min=900, wait=1.0)
    tap_text(cfg, "日志", wait=1.5)
    snap(cfg, "su-log")
    nodes = dump(cfg)
    print("log", [n["text"] for n in nodes if n["text"]][:80])

    ok = bool(pid)
    print("RESULT", "PASS" if ok else "FAIL", "game_pid=", pid)
    sleep_device(cfg)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
