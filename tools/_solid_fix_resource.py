#!/usr/bin/env python3
"""Point Official resource to resource_adb on-device; reload project; start Tacet."""
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


def tap_text(cfg, needle, prefer_desc=False, y_min=0, wait=1.2):
    nodes = dump(cfg)
    cands = []
    for n in nodes:
        fields = [n["desc"], n["text"]] if prefer_desc else [n["text"], n["desc"]]
        for v in fields:
            if v == needle and n["bounds"][1] >= y_min:
                cands.append(n)
                break
    if not cands:
        for n in nodes:
            if needle in (n["text"], n["desc"]) and n["bounds"][1] >= y_min:
                cands.append(n)
    if not cands:
        print("miss", needle)
        return False
    n = cands[0]
    x1, y1, x2, y2 = n["bounds"]
    tap(cfg, (x1 + x2) // 2, (y1 + y2) // 2, wait, needle)
    return True


def main() -> int:
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])

    # pull, patch, push interface.json
    local = OUT / "_interface.json"
    adb(cfg, "pull", f"{PI}/interface.json", str(local))
    data = json.loads(local.read_text(encoding="utf-8"))
    data["resource"][0]["path"] = ["./resource_adb"]
    # keep attach for safety or clear duplicate
    for c in data.get("controller", []):
        if c.get("name") == "ADB":
            c["attach_resource_path"] = []
    local.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    print(adb(cfg, "push", str(local), f"{PI}/interface.json").stdout)
    print("patched interface resource -> ./resource_adb")

    # also patch repo interface for next rebuild
    repo_if = ROOT / "assets/interface.json"
    repo = json.loads(repo_if.read_text(encoding="utf-8"))
    if repo["resource"][0]["path"] != ["./resource_adb"]:
        repo["resource"][0]["path"] = ["./resource_adb"]
        for c in repo.get("controller", []):
            if c.get("name") == "ADB":
                # attach same path would double-load; clear
                c["attach_resource_path"] = []
        repo_if.write_text(json.dumps(repo, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
        print("repo interface.json updated")

    # verify pipelines exist
    print(adb(cfg, "shell", "ls", f"{PI}/resource_adb/pipeline").stdout)

    adb(cfg, "shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(1.5)

    # reload via settings 重新解压 is heavy; use quick options 重新加载项目
    tap_text(cfg, "任务", prefer_desc=True, y_min=900, wait=1.5)
    snap(cfg, "tasks-before-reload")
    # open quick options
    if tap_text(cfg, "快捷选项", wait=1.2):
        snap(cfg, "quick")
        nodes = dump(cfg)
        print("quick:", [n["text"] for n in nodes if n["text"]])
        if not tap_text(cfg, "重新加载项目", wait=2.5):
            # try contains
            for n in nodes:
                if "重新加载" in n["text"] or "重载" in n["text"]:
                    x1, y1, x2, y2 = n["bounds"]
                    tap(cfg, (x1 + x2) // 2, (y1 + y2) // 2, 2.5, n["text"])
                    break
        snap(cfg, "after-reload")

    # start
    tap_text(cfg, "任务", prefer_desc=True, y_min=900, wait=1.0)
    tap_text(cfg, "开始任务", wait=2.5)
    snap(cfg, "started")
    nodes = dump(cfg)
    print("status:", [n["text"] for n in nodes if n["text"] in ("空闲", "未在运行", "运行中", "准备中") or "失败" in n["text"] or "资源" in n["text"]])

    # confirm dialogs
    for _ in range(3):
        nodes = dump(cfg)
        hit = False
        for key in ("确定", "继续", "仍要开始", "确认"):
            for n in nodes:
                if n["text"] == key or key in n["text"]:
                    x1, y1, x2, y2 = n["bounds"]
                    if y1 > 300:
                        tap(cfg, (x1 + x2) // 2, (y1 + y2) // 2, 1.5, key)
                        hit = True
                        snap(cfg, f"ack-{key}")
                        break
            if hit:
                break
        if not hit:
            break

    for i in range(8):
        time.sleep(3)
        snap(cfg, f"run-poll-{i}")
        nodes = dump(cfg)
        st = [n["text"] for n in nodes if n["text"]]
        interesting = [t for t in st if t in ("空闲", "未在运行", "运行中", "准备中") or "失败" in t or "资源" in t]
        print("poll", i, interesting)
        if any(t in ("运行中", "准备中") for t in interesting):
            break
        if any("失败" in t for t in interesting):
            break

    # logs
    if tap_text(cfg, "日志", wait=1.5):
        snap(cfg, "run-log")
        nodes = dump(cfg)
        print("log:", [n["text"] for n in nodes if n["text"]][:50])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
