#!/usr/bin/env python3
"""Copy OCR model pack from working MaaEnd on-device PI into MaaWW, then restore resource_adb."""
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
END = "com.aliothmoon.maafw.maaend"
WW_PI = f"/storage/emulated/0/Android/data/{WW}/files/pi"
END_PI = f"/storage/emulated/0/Android/data/{END}/files/pi"


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


def main() -> int:
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])

    print("END model listing:")
    print(adb(cfg, "shell", "ls", "-la", f"{END_PI}/resource/model").stdout)
    print(adb(cfg, "shell", "du", "-sh", f"{END_PI}/resource/model").stdout)

    # copy model via device-side cp (same storage)
    adb(cfg, "shell", "rm", "-rf", f"{WW_PI}/resource")
    adb(cfg, "shell", "mkdir", "-p", f"{WW_PI}/resource")
    # copy default_pipeline + model from MaaEnd
    r = adb(
        cfg,
        "shell",
        "sh",
        "-c",
        f"cp -a {END_PI}/resource/default_pipeline.json {WW_PI}/resource/ && "
        f"cp -a {END_PI}/resource/model {WW_PI}/resource/ && "
        f"mkdir -p {WW_PI}/resource/pipeline && "
        f"ls -la {WW_PI}/resource && du -sh {WW_PI}/resource/model",
    )
    print(r.stdout or r.stderr)

    # restore resource_adb cleanly: rm then mkdir, push files individually
    adb(cfg, "shell", "rm", "-rf", f"{WW_PI}/resource_adb")
    adb(cfg, "shell", "mkdir", "-p", f"{WW_PI}/resource_adb/pipeline")
    adb(cfg, "shell", "mkdir", "-p", f"{WW_PI}/resource_adb/image")
    dp = ROOT / "assets/resource_adb/default_pipeline.json"
    if not dp.exists():
        dp.write_text(
            json.dumps(
                {"Default": {"rate_limit": 1000, "pre_delay": 200, "post_delay": 200}},
                indent=4,
            )
            + "\n",
            encoding="utf-8",
        )
    print(adb(cfg, "push", str(dp), f"{WW_PI}/resource_adb/default_pipeline.json").stdout)
    for f in (ROOT / "assets/resource_adb/pipeline").glob("*.json"):
        print(adb(cfg, "push", str(f), f"{WW_PI}/resource_adb/pipeline/{f.name}").stdout.strip())
    # images: push each subdir
    img_root = ROOT / "assets/resource_adb/image"
    for sub in img_root.iterdir():
        if sub.is_dir():
            adb(cfg, "shell", "mkdir", "-p", f"{WW_PI}/resource_adb/image/{sub.name}")
            for png in sub.rglob("*.png"):
                rel = png.relative_to(img_root).as_posix()
                remote_dir = f"{WW_PI}/resource_adb/image/{png.parent.relative_to(img_root).as_posix()}"
                adb(cfg, "shell", "mkdir", "-p", remote_dir)
                adb(cfg, "push", str(png), f"{WW_PI}/resource_adb/image/{rel}")

    # interface: Official = resource + attach empty; controller attach resource_adb
    iface = json.loads((ROOT / "assets/interface.json").read_text(encoding="utf-8"))
    iface["resource"][0]["path"] = ["./resource"]
    for c in iface.get("controller", []):
        if c.get("name") == "ADB":
            c["attach_resource_path"] = ["./resource_adb"]
    local_iface = OUT / "_iface_final.json"
    local_iface.write_text(json.dumps(iface, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    (ROOT / "assets/interface.json").write_text(
        json.dumps(iface, ensure_ascii=False, indent=4) + "\n", encoding="utf-8"
    )
    print(adb(cfg, "push", str(local_iface), f"{WW_PI}/interface.json").stdout)
    print(adb(cfg, "push", str(ROOT / "assets/locales/zh_cn.json"), f"{WW_PI}/locales/zh_cn.json").stdout)
    print(adb(cfg, "push", str(ROOT / "assets/locales/en_us.json"), f"{WW_PI}/locales/en_us.json").stdout)
    print(adb(cfg, "push", str(ROOT / "assets/tasks"), f"{WW_PI}/tasks").stdout)

    print("WW resource:", adb(cfg, "shell", "ls", "-la", f"{WW_PI}/resource").stdout)
    print("WW resource_adb:", adb(cfg, "shell", "ls", "-la", f"{WW_PI}/resource_adb").stdout)
    print("WW pipelines:", adb(cfg, "shell", "ls", f"{WW_PI}/resource_adb/pipeline").stdout)

    adb(cfg, "logcat", "-c")
    adb(cfg, "shell", "monkey", "-p", WW, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(2)
    tap_text(cfg, "任务", y_min=900, wait=1.2)
    tap_text(cfg, "快捷选项", wait=1.0)
    tap_text(cfg, "重新加载项目", wait=3.0)
    tap_text(cfg, "开始任务", wait=4.0)
    snap(cfg, "model-start")
    tap_text(cfg, "日志", wait=1.5)
    snap(cfg, "model-log")
    nodes = dump(cfg)
    print("log:", [n["text"] for n in nodes if n["text"]][:80])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
