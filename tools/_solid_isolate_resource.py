#!/usr/bin/env python3
"""Bisect PostBundle failure: try minimal bundle then add pipelines."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
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


def push_tree(cfg, local: Path):
    adb(cfg, "shell", "rm", "-rf", f"{PI}/resource_adb")
    adb(cfg, "shell", "mkdir", "-p", f"{PI}/resource_adb/pipeline")
    adb(cfg, "shell", "mkdir", "-p", f"{PI}/resource_adb/image")
    # push default
    print(adb(cfg, "push", str(local / "default_pipeline.json"), f"{PI}/resource_adb/default_pipeline.json").stdout)
    pipe = local / "pipeline"
    if pipe.exists():
        for f in pipe.glob("*.json"):
            print(adb(cfg, "push", str(f), f"{PI}/resource_adb/pipeline/{f.name}").stdout.strip())
    img = local / "image"
    if img.exists():
        # push via tar for speed
        adb(cfg, "push", str(img), f"{PI}/resource_adb/image")


def try_start(cfg, label: str) -> list[str]:
    adb(cfg, "logcat", "-c")
    adb(cfg, "shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(1.2)
    tap_text(cfg, "任务", y_min=900, wait=1.0)
    tap_text(cfg, "快捷选项", wait=0.8)
    tap_text(cfg, "重新加载项目", wait=2.5)
    tap_text(cfg, "开始任务", wait=3.5)
    snap(cfg, f"iso-{label}")
    tap_text(cfg, "日志", wait=1.2)
    nodes = dump(cfg)
    texts = [n["text"] for n in nodes if n["text"]]
    print(label, "log:", [t for t in texts if "资源" in t or "失败" in t or "加载" in t or t in ("运行中", "准备中", "空闲")])
    # close log
    tap_text(cfg, "关闭", wait=0.8)
    return texts


def main() -> int:
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])

    # validate local pipelines
    for f in (ROOT / "assets/resource_adb/pipeline").glob("*.json"):
        try:
            json.loads(f.read_text(encoding="utf-8"))
            print("JSON OK", f.name)
        except Exception as e:
            print("JSON BAD", f.name, e)

    dp = {"Default": {"rate_limit": 1000, "pre_delay": 200, "post_delay": 200}}

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        # Case A: only default_pipeline
        (td_path / "default_pipeline.json").write_text(json.dumps(dp, indent=4) + "\n", encoding="utf-8")
        (td_path / "pipeline").mkdir()
        push_tree(cfg, td_path)
        try_start(cfg, "A-empty")

        # Case B: only Startup.json
        shutil.copy(ROOT / "assets/resource_adb/pipeline/Startup.json", td_path / "pipeline/Startup.json")
        push_tree(cfg, td_path)
        try_start(cfg, "B-startup")

        # Case C: all pipelines no images
        for f in (ROOT / "assets/resource_adb/pipeline").glob("*.json"):
            shutil.copy(f, td_path / "pipeline" / f.name)
        push_tree(cfg, td_path)
        try_start(cfg, "C-all-pipe")

        # Case D: full local resource_adb (files one by one)
        adb(cfg, "shell", "rm", "-rf", f"{PI}/resource_adb")
        # use adb push of each top-level via tmp staging without nested name
        staging = ROOT / "review/inbox/_pi_resource_adb"
        if staging.exists():
            shutil.rmtree(staging)
        shutil.copytree(ROOT / "assets/resource_adb", staging)
        # remove nested junk if any
        nested = staging / "resource_adb"
        if nested.exists():
            shutil.rmtree(nested)
        adb(cfg, "shell", "mkdir", "-p", f"{PI}/resource_adb")
        print(adb(cfg, "push", str(staging / "."), f"{PI}/resource_adb/").stdout)
        # fix if nested
        adb(cfg, "shell", "sh", "-c", f"if [ -d {PI}/resource_adb/resource_adb ]; then cp -a {PI}/resource_adb/resource_adb/* {PI}/resource_adb/; rm -rf {PI}/resource_adb/resource_adb; fi")
        print("find default", adb(cfg, "shell", "ls", f"{PI}/resource_adb/default_pipeline.json").stdout)
        print("pipelines", adb(cfg, "shell", "ls", f"{PI}/resource_adb/pipeline").stdout)
        try_start(cfg, "D-full")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
