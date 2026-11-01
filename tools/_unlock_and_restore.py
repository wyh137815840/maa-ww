#!/usr/bin/env python3
"""Unlock FBE → wait for emulated storage → restore full PI with Tacet."""
from __future__ import annotations
import _local_cfg

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
from common import load_config

WW = "com.aliothmoon.maafw.maaww"
END = "com.aliothmoon.maafw.maaend"
PI = f"/storage/emulated/0/Android/data/{WW}/files/pi"
END_PI = f"/storage/emulated/0/Android/data/{END}/files/pi"


def adb(cfg, *a, timeout=120):
    return subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *a],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=timeout,
    )


def unlock(cfg):
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_WAKEUP")
    time.sleep(0.5)
    adb(cfg, "shell", "input", "keyevent", "82")
    time.sleep(0.4)
    adb(cfg, "shell", "input", "text", _local_cfg.pin())
    time.sleep(0.2)
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_ENTER")
    time.sleep(1.0)


def wait_storage(cfg, sec=30) -> bool:
    for i in range(sec):
        r = adb(cfg, "shell", "ls", "/storage/emulated/0/Android")
        if r.returncode == 0 and "data" in (r.stdout or ""):
            print("storage ok at", i)
            return True
        if i % 5 == 0:
            print("wait storage", i, (r.stderr or r.stdout or "")[:120])
            unlock(cfg)
        time.sleep(1)
    return False


def push_tree(cfg, local: Path, remote: str):
    """Push directory via adb push (recursive)."""
    adb(cfg, "shell", "mkdir", "-p", remote)
    r = adb(cfg, "push", str(local), remote)
    if r.returncode != 0:
        print("push fail", local, r.stderr or r.stdout)
    return r.returncode == 0


def main() -> int:
    cfg = load_config()
    unlock(cfg)
    if not wait_storage(cfg):
        print("FAIL: emulated storage still unavailable after unlock")
        # diagnostics
        print(adb(cfg, "shell", "dumpsys", "user").stdout[:800])
        return 1

    # launch app so it creates external files dir
    adb(cfg, "shell", "monkey", "-p", WW, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(2.5)
    adb(cfg, "shell", "mkdir", "-p", f"{PI}/resource/pipeline", f"{PI}/resource/image", f"{PI}/tasks", f"{PI}/locales")

    # sync local Official first
    subprocess.run([sys.executable, str(ROOT / "tools/sync_resource_from_adb.py")], cwd=ROOT)

    # interface + imports
    adb(cfg, "push", str(ROOT / "assets/interface.json"), f"{PI}/interface.json")
    for f in (ROOT / "assets/locales").glob("*.json"):
        adb(cfg, "push", str(f), f"{PI}/locales/{f.name}")
    for f in (ROOT / "assets/tasks").glob("*.json"):
        adb(cfg, "push", str(f), f"{PI}/tasks/{f.name}")

    # pipeline + images + default_pipeline
    for f in (ROOT / "assets/resource/pipeline").glob("*.json"):
        adb(cfg, "push", str(f), f"{PI}/resource/pipeline/{f.name}")
    push_tree(cfg, ROOT / "assets/resource/image", f"{PI}/resource/image")
    dp = ROOT / "assets/resource/default_pipeline.json"
    if dp.is_file():
        adb(cfg, "push", str(dp), f"{PI}/resource/default_pipeline.json")

    # OCR model from MaaEnd if missing
    if "rec.onnx" not in adb(cfg, "shell", "ls", f"{PI}/resource/model/ocr").stdout:
        print("copy model from MaaEnd")
        adb(
            cfg,
            "shell",
            f"rm -rf {PI}/resource/model; cp -R {END_PI}/resource/model {PI}/resource/model; chmod -R 0777 {PI}/resource/model",
        )

    adb(cfg, "shell", "chmod", "-R", "0777", PI)
    print("pipeline", adb(cfg, "shell", "ls", f"{PI}/resource/pipeline").stdout)
    print("images", adb(cfg, "shell", f"find {PI}/resource/image -name '*.png' | wc -l").stdout)
    print("tasks", adb(cfg, "shell", "ls", f"{PI}/tasks").stdout)
    print("iface imports", adb(cfg, "shell", f"grep import -A6 {PI}/interface.json").stdout)
    print("model", adb(cfg, "shell", "ls", f"{PI}/resource/model/ocr/rec.onnx").stdout)

    adb(cfg, "shell", "am", "force-stop", WW)
    time.sleep(0.5)
    print("OK: full PI restored with Tacet import")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
