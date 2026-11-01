#!/usr/bin/env python3
"""Ensure background run mode, then start Tacet from Tasks (App UI only)."""
from __future__ import annotations

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


def adb(cfg, *args):
    return subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )


def snap(cfg, label):
    p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-n-{label}.png"
    print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)
    return p


def dump_nodes(cfg):
    adb(cfg, "shell", "uiautomator", "dump", "/sdcard/uidump.xml")
    p = OUT / "_uidump.xml"
    adb(cfg, "pull", "/sdcard/uidump.xml", str(p))
    text = p.read_text(encoding="utf-8", errors="ignore")
    nodes = []
    for m in re.finditer(r"<node\b([^>]*)/>", text):
        attrs = m.group(1)
        text_m = re.search(r'\btext="([^"]*)"', attrs)
        desc_m = re.search(r'\bcontent-desc="([^"]*)"', attrs)
        bound_m = re.search(r'\bbounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', attrs)
        class_m = re.search(r'\bclass="([^"]*)"', attrs)
        if not bound_m:
            continue
        nodes.append(
            {
                "text": text_m.group(1) if text_m else "",
                "desc": desc_m.group(1) if desc_m else "",
                "bounds": tuple(map(int, bound_m.groups())),
                "class": (class_m.group(1) if class_m else "").split(".")[-1],
            }
        )
    return nodes


def tap_raw(cfg, x, y, wait=1.2, label=""):
    print(f"tap_raw {label} ({x},{y})")
    adb(cfg, "shell", "input", "tap", str(x), str(y))
    time.sleep(wait)


def tap_match(cfg, needle, contains=False, prefer_desc=False, wait=1.2):
    nodes = dump_nodes(cfg)
    hit = None
    for n in nodes:
        vals = []
        if prefer_desc:
            vals = [n["desc"], n["text"]]
        else:
            vals = [n["text"], n["desc"]]
        for v in vals:
            if not v:
                continue
            if (needle in v) if contains else (v == needle):
                hit = n
                break
        if hit:
            break
    if not hit:
        print("NOT_FOUND", needle)
        for n in nodes:
            if n["text"] or n["desc"]:
                print(" ", n["text"] or n["desc"], n["bounds"])
        return False
    x1, y1, x2, y2 = hit["bounds"]
    # for Button near text
    if hit["text"] == needle or (contains and needle in hit["text"]):
        cy = (y1 + y2) // 2
        for n in nodes:
            if n["class"] == "Button":
                bx1, by1, bx2, by2 = n["bounds"]
                if by1 - 20 <= cy <= by2 + 20 and (bx2 - bx1) > 500:
                    x1, y1, x2, y2 = n["bounds"]
                    break
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    tap_raw(cfg, cx, cy, wait, needle)
    return True


def swipe_up(cfg):
    adb(cfg, "shell", "input", "swipe", "960", "800", "960", "350", "400")
    time.sleep(0.8)


def main() -> int:
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    adb(cfg, "shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(2.0)

    # Settings via nav desc
    tap_match(cfg, "设置", prefer_desc=True, wait=1.5)
    snap(cfg, "settings")

    # search 运行模式
    if tap_match(cfg, "搜索设置", wait=1.0):
        adb(cfg, "shell", "input", "text", "yunxingmoshi")  # may fail for CJK
        time.sleep(0.5)
        # try paste via am - skip; swipe find instead
        adb(cfg, "shell", "input", "keyevent", "KEYCODE_BACK")
        time.sleep(0.5)

    found = False
    for i in range(8):
        nodes = dump_nodes(cfg)
        texts = [n["text"] for n in nodes if n["text"]]
        print("settings texts:", [t for t in texts if t][:20])
        if any("运行模式" in t for t in texts):
            found = True
            break
        if any("后台" in t or "前台" in t for t in texts):
            found = True
            break
        swipe_up(cfg)
        snap(cfg, f"settings-scroll-{i}")

    if found:
        nodes = dump_nodes(cfg)
        for n in nodes:
            if "后台" in n["text"] or n["text"] == "后台模式":
                x1, y1, x2, y2 = n["bounds"]
                tap_raw(cfg, (x1 + x2) // 2, (y1 + y2) // 2, 1.0, "后台")
                snap(cfg, "after-bg")
                break
        for n in nodes:
            if "运行模式" in n["text"]:
                x1, y1, x2, y2 = n["bounds"]
                tap_raw(cfg, (x1 + x2) // 2, (y1 + y2) // 2, 1.2, "运行模式")
                snap(cfg, "run-mode-open")
                # pick 后台
                tap_match(cfg, "后台", contains=True, wait=1.0)
                snap(cfg, "run-mode-picked")
                break

    # back to tasks
    for _ in range(3):
        if tap_match(cfg, "任务", prefer_desc=True, wait=1.5):
            nodes = dump_nodes(cfg)
            if any(n["text"] == "开始任务" for n in nodes):
                break
            if any(n["text"] == "无音区" for n in nodes):
                break
    snap(cfg, "tasks-ready")

    # start
    tap_match(cfg, "开始任务", wait=2.0)
    snap(cfg, "after-start1")
    nodes = dump_nodes(cfg)
    # confirm dialog?
    for key in ("确定", "继续", "确认", "知道了", "仍要开始", "开始"):
        if any(key == n["text"] or key in n["text"] for n in nodes):
            tap_match(cfg, key, contains=True, wait=1.5)
            snap(cfg, f"confirm-{key}")
            nodes = dump_nodes(cfg)

    # status
    for n in nodes:
        if n["text"] in ("空闲", "运行中", "准备中", "未在运行", "忙碌") or "运行" in n["text"]:
            print("status node", n)

    snap(cfg, "final-status")
    # poll a few seconds
    for i in range(6):
        time.sleep(3)
        snap(cfg, f"poll-{i}")
        nodes = dump_nodes(cfg)
        st = [n["text"] for n in nodes if n["text"] in ("空闲", "运行中", "准备中", "未在运行") or "中" in n["text"]]
        print("poll", i, st[:10])
        if any("运行" in t or "准备" in t for t in st):
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
