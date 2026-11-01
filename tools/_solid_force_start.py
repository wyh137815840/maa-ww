#!/usr/bin/env python3
"""Home: ensure BACKGROUND; Tasks: prove taps via 日志; then start; dump log sheet."""
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
    return p


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


def find(nodes, needle, field="text", contains=False):
    for n in nodes:
        v = n[field]
        if not v:
            continue
        if (needle in v) if contains else (v == needle):
            return n
    return None


def tap_node(cfg, n, w=1.2, label=""):
    x1, y1, x2, y2 = n["bounds"]
    tap(cfg, (x1 + x2) // 2, (y1 + y2) // 2, w, label or n["text"] or n["desc"])


def nav(cfg, name):
    nodes = dump(cfg)
    n = find(nodes, name, "desc") or find(nodes, name, "text")
    if not n:
        print("nav miss", name)
        return False
    # prefer bottom nav: y > 900
    cands = [x for x in nodes if (x["desc"] == name or x["text"] == name) and x["bounds"][1] > 900]
    tap_node(cfg, cands[0] if cands else n, 1.5, f"nav-{name}")
    return True


def main() -> int:
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    adb(cfg, "logcat", "-c")
    adb(cfg, "shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(2)

    nav(cfg, "首页")
    snap(cfg, "home")
    nodes = dump(cfg)
    print("home texts:", [n["text"] for n in nodes if n["text"]][:30])

    # run mode
    bg = find(nodes, "后台", contains=True) or find(nodes, "前台", contains=True)
    mode = find(nodes, "运行模式")
    if mode:
        print("run mode row", mode, bg)
    # if showing 前台, toggle switch — switch usually right of label
    if bg and "前台" in bg["text"]:
        x1, y1, x2, y2 = bg["bounds"]
        # switch to the right
        tap(cfg, min(x2 + 120, 1850), (y1 + y2) // 2, 1.0, "toggle-bg")
        snap(cfg, "toggled-bg")
    elif mode:
        x1, y1, x2, y2 = mode["bounds"]
        tap(cfg, 1750, (y1 + y2) // 2, 1.0, "toggle-mode-right")
        snap(cfg, "toggled-mode")

    nodes = dump(cfg)
    print("after mode:", [n["text"] for n in nodes if "台" in n["text"] or "模式" in n["text"]])

    # Shizuku connect if needed
    for n in nodes:
        if n["text"] in ("连接", "授权", "启动", "重试"):
            print("action", n)
            tap_node(cfg, n, 2.0, n["text"])
            snap(cfg, f"home-act-{n['text']}")

    nav(cfg, "任务")
    snap(cfg, "tasks")
    nodes = dump(cfg)
    print("tasks:", [n["text"] for n in nodes if n["text"]])

    # prove tap: open 日志
    logb = find(nodes, "日志")
    if logb:
        tap_node(cfg, logb, 1.5, "日志")
        snap(cfg, "log-sheet")
        # close
        close = find(dump(cfg), "关闭", "desc") or find(dump(cfg), "关闭")
        if close:
            tap_node(cfg, close, 1.0, "关闭日志")

    nodes = dump(cfg)
    start = find(nodes, "开始任务")
    if not start:
        print("no start button")
        return 2
    # also find wide Button by re-dump with class - approximate wider tap box
    x1, y1, x2, y2 = start["bounds"]
    # try several points across the blue bar
    points = [
        ((x1 + x2) // 2, (y1 + y2) // 2),
        (400, 849),
        (960, 849),
        (1200, 849),
        (839, 830),
        (839, 870),
    ]
    for i, (x, y) in enumerate(points):
        tap(cfg, x, y, 2.0, f"start-{i}")
        snap(cfg, f"start-{i}")
        nodes = dump(cfg)
        texts = [n["text"] for n in nodes if n["text"]]
        print("after", i, [t for t in texts if t in ("空闲", "未在运行", "运行中", "准备中", "确定", "继续") or "前台" in t or "失败" in t or "无法" in t])
        # confirm dialogs
        for key in ("确定", "继续", "仍要开始", "知道了"):
            n = find(nodes, key) or find(nodes, key, contains=True)
            if n and n["bounds"][1] > 400:
                tap_node(cfg, n, 1.5, key)
                snap(cfg, f"dlg-{key}-{i}")
                nodes = dump(cfg)
        if any(t in ("运行中", "准备中") for t in texts):
            print("STARTED")
            break
        if any("前台" in t for t in texts):
            print("foreground toast/dialog?")
            break

    # open logs again
    nodes = dump(cfg)
    logb = find(nodes, "日志")
    if logb:
        tap_node(cfg, logb, 1.5, "日志2")
        snap(cfg, "log-after")
        nodes = dump(cfg)
        print("log texts:", [n["text"] for n in nodes if n["text"]][:40])

    log = adb(cfg, "shell", "logcat", "-d", "-t", "300", "-s", "MaaFw:D", "MaaFw:I", "MaaFw:W", "MaaFw:E", "AndroidRuntime:E").stdout or ""
    print("=== MaaFw log ===")
    print(log[-3000:] if log else "(empty)")
    log2 = adb(cfg, "shell", "logcat", "-d", "-t", "200").stdout or ""
    for line in log2.splitlines():
        if "maafw" in line.lower() or "MaaRunner" in line or "Session" in line:
            print(line[-220:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
