#!/usr/bin/env python3
"""Final: stub+model base + clean resource_adb attach; add Startup then start; verify game launch."""
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

OUT = ROOT / "review/inbox"
WW = "com.aliothmoon.maafw.maaww"
WW_PI = f"/storage/emulated/0/Android/data/{WW}/files/pi"
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
    time.sleep(0.3)
    adb(cfg, "shell", "input", "keyevent", "82")
    time.sleep(0.3)
    adb(cfg, "shell", "input", "text", _local_cfg.pin())
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


def tap_text(cfg, needle, y_min=0, contains=False, wait=1.2):
    nodes = dump(cfg)
    for n in nodes:
        vals = (n["text"], n["desc"])
        ok = any((needle in v) if contains else (v == needle) for v in vals if v)
        if ok and n["bounds"][1] >= y_min:
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

    # persist stub into repo assets/resource
    stub = {"MaaWWBaseStub": {"desc": "占位节点，使底座 PostBundle 可过（需 OCR model）。", "recognition": "DirectHit", "action": "DoNothing", "next": []}}
    base_pipe = ROOT / "assets/resource/pipeline"
    base_pipe.mkdir(parents=True, exist_ok=True)
    (base_pipe / "Stub.json").write_text(json.dumps(stub, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    dp = {"Default": {"rate_limit": 1000, "pre_delay": 200, "post_delay": 200}}
    (ROOT / "assets/resource/default_pipeline.json").write_text(json.dumps(dp, indent=4) + "\n", encoding="utf-8")
    # note: model/ must be present on device; document sync later
    (ROOT / "assets/resource/model/.gitkeep").parent.mkdir(parents=True, exist_ok=True)
    (ROOT / "assets/resource/model/.gitkeep").write_text("", encoding="utf-8")
    (ROOT / "assets/resource/README.md").write_text(
        "# resource（底座）\n\n需含 `default_pipeline.json`、`pipeline/Stub.json`、以及 OCR `model/`（可从本机已装 MaaEnd 的 "
        "`Android/data/.../pi/resource/model` 拷贝，约 224MB）。\n"
        "业务 Pipeline/模板放 `resource_adb`，由 ADB controller `attach_resource_path` 挂载。\n",
        encoding="utf-8",
    )

    # device: ensure stub + model; rebuild resource_adb
    adb(cfg, "shell", "mkdir", "-p", f"{WW_PI}/resource/pipeline")
    adb(cfg, "push", str(base_pipe / "Stub.json"), f"{WW_PI}/resource/pipeline/Stub.json")
    adb(cfg, "push", str(ROOT / "assets/resource/default_pipeline.json"), f"{WW_PI}/resource/default_pipeline.json")

    adb(cfg, "shell", "rm", "-rf", f"{WW_PI}/resource_adb")
    adb(cfg, "shell", "mkdir", "-p", f"{WW_PI}/resource_adb/pipeline")
    adb(cfg, "shell", "mkdir", "-p", f"{WW_PI}/resource_adb/image")
    adb(cfg, "push", str(ROOT / "assets/resource_adb/default_pipeline.json"), f"{WW_PI}/resource_adb/default_pipeline.json")
    for f in (ROOT / "assets/resource_adb/pipeline").glob("*.json"):
        adb(cfg, "push", str(f), f"{WW_PI}/resource_adb/pipeline/{f.name}")
    img_root = ROOT / "assets/resource_adb/image"
    for png in img_root.rglob("*.png"):
        rel = png.relative_to(img_root).as_posix()
        remote_dir = f"{WW_PI}/resource_adb/image/{png.parent.relative_to(img_root).as_posix()}"
        adb(cfg, "shell", "mkdir", "-p", remote_dir)
        adb(cfg, "push", str(png), f"{WW_PI}/resource_adb/image/{rel}")
    adb(cfg, "shell", "chmod", "-R", "0777", f"{WW_PI}/resource")
    adb(cfg, "shell", "chmod", "-R", "0777", f"{WW_PI}/resource_adb")

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
                "attach_resource_path": ["./resource_adb"],
            }
        ],
        "resource": [
            {
                "name": "Official",
                "label": "$resource.Official.label",
                "path": ["./resource"],
            }
        ],
        "task": json.loads((ROOT / "assets/interface.json").read_text(encoding="utf-8"))["task"],
    }
    (ROOT / "assets/interface.json").write_text(
        json.dumps(iface, ensure_ascii=False, indent=4) + "\n", encoding="utf-8"
    )
    adb(cfg, "push", str(ROOT / "assets/interface.json"), f"{WW_PI}/interface.json")
    adb(cfg, "push", str(ROOT / "assets/locales/zh_cn.json"), f"{WW_PI}/locales/zh_cn.json")
    adb(cfg, "push", str(ROOT / "assets/tasks"), f"{WW_PI}/tasks")

    # UI: reload, ensure Startup task present (add if needed), start
    adb(cfg, "logcat", "-c")
    adb(cfg, "shell", "monkey", "-p", WW, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(2)
    tap_text(cfg, "确定", wait=0.8)
    tap_text(cfg, "任务", y_min=900, wait=1.2)
    tap_text(cfg, "快捷选项", wait=1.0)
    tap_text(cfg, "重新加载项目", wait=3.0)
    snap(cfg, "fin-tasks")

    # add Startup if missing
    nodes = dump(cfg)
    texts = [n["text"] for n in nodes if n["text"]]
    print("before add", texts)
    if "启动进游戏（开发中）" not in texts and not any("启动" in t for t in texts):
        if tap_text(cfg, "添加任务", wait=1.5):
            # pick 启动
            if not tap_text(cfg, "启动进游戏（开发中）", wait=1.0):
                tap_text(cfg, "启动", contains=True, wait=1.0)
            tap_text(cfg, "确认添加", contains=True, wait=1.5)
            snap(cfg, "fin-added-startup")

    # reorder: want Startup before Tacet — drag not reliable; if both present start anyway
    # force-stop game first to prove cold start
    adb(cfg, "shell", "am", "force-stop", GAME)
    time.sleep(0.8)
    print("pid before", adb(cfg, "shell", "pidof", GAME).stdout.strip())

    tap_text(cfg, "开始任务", wait=8.0)
    snap(cfg, "fin-running")
    nodes = dump(cfg)
    print("status", [n["text"] for n in nodes if n["text"]][:30])
    print("pid after", adb(cfg, "shell", "pidof", GAME).stdout.strip())

    for i in range(5):
        time.sleep(3)
        snap(cfg, f"fin-poll-{i}")
        pid = adb(cfg, "shell", "pidof", GAME).stdout.strip()
        nodes = dump(cfg)
        st = [n["text"] for n in nodes if n["text"] in ("空闲", "运行中", "准备中", "未在运行") or "失败" in (n["text"] or "")]
        print("poll", i, "pid", pid, st)
        if pid:
            print("GAME LAUNCHED")
            break

    tap_text(cfg, "日志", wait=1.5)
    snap(cfg, "fin-log")
    nodes = dump(cfg)
    print("log", [n["text"] for n in nodes if n["text"]][:80])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
