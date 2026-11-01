#!/usr/bin/env python3
"""Push full Official PI to device. No UI taps. Force-stop App so native resource reloads."""
from __future__ import annotations

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


def adb(cfg, *a, timeout=180):
    return subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *a],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=timeout,
    )


def main() -> int:
    cfg = load_config()
    # storage gate
    r = adb(cfg, "shell", "ls", "/storage/emulated/0/Android/data")
    if r.returncode != 0 or "No such" in (r.stderr or "") + (r.stdout or ""):
        print("FAIL: external storage not ready")
        print(r.stdout, r.stderr)
        print(adb(cfg, "shell", "sm", "list-volumes").stdout)
        return 2

    # ensure app external dir exists (launch once if needed, then stop — no taps)
    adb(cfg, "shell", "mkdir", "-p", f"{PI}/resource/pipeline", f"{PI}/resource/image", f"{PI}/tasks", f"{PI}/locales")
    if "No such" in adb(cfg, "shell", "ls", PI).stderr:
        print("creating external files via brief start…")
        adb(cfg, "shell", "am", "start", "-n", f"{WW}/com.aliothmoon.maafw.MainActivity")
        time.sleep(2.5)
        adb(cfg, "shell", "am", "force-stop", WW)
        time.sleep(0.5)
        adb(cfg, "shell", "mkdir", "-p", f"{PI}/resource/pipeline", f"{PI}/resource/image", f"{PI}/tasks", f"{PI}/locales")

    # sync local Official from resource_adb
    subprocess.run([sys.executable, str(ROOT / "tools/sync_resource_from_adb.py")], cwd=ROOT)

    # interface + locales + tasks
    for src, dst in [
        (ROOT / "assets/interface.json", f"{PI}/interface.json"),
        (ROOT / "assets/locales/zh_cn.json", f"{PI}/locales/zh_cn.json"),
        (ROOT / "assets/locales/en_us.json", f"{PI}/locales/en_us.json"),
    ]:
        rr = adb(cfg, "push", str(src), dst)
        print("push", src.name, "ok" if rr.returncode == 0 else rr.stderr)

    for f in sorted((ROOT / "assets/tasks").glob("*.json")):
        rr = adb(cfg, "push", str(f), f"{PI}/tasks/{f.name}")
        print("push tasks/", f.name, "ok" if rr.returncode == 0 else rr.stderr)

    # pipelines
    adb(cfg, "shell", "rm", "-rf", f"{PI}/resource/pipeline")
    adb(cfg, "shell", "mkdir", "-p", f"{PI}/resource/pipeline")
    for f in sorted((ROOT / "assets/resource/pipeline").glob("*.json")):
        rr = adb(cfg, "push", str(f), f"{PI}/resource/pipeline/{f.name}")
        print("push pipeline/", f.name, "ok" if rr.returncode == 0 else rr.stderr)

    # images (recursive adb push)
    adb(cfg, "shell", "rm", "-rf", f"{PI}/resource/image")
    img = ROOT / "assets/resource/image"
    rr = adb(cfg, "push", str(img), f"{PI}/resource/image")
    print("push image/", "ok" if rr.returncode == 0 else rr.stderr, (rr.stdout or "")[-200:])

    dp = ROOT / "assets/resource/default_pipeline.json"
    if dp.is_file():
        adb(cfg, "push", str(dp), f"{PI}/resource/default_pipeline.json")

    # model from MaaEnd if missing
    if "rec.onnx" not in adb(cfg, "shell", "ls", f"{PI}/resource/model/ocr").stdout:
        print("copy OCR model from MaaEnd…")
        adb(
            cfg,
            "shell",
            f"cp -R {END_PI}/resource/model {PI}/resource/model && chmod -R 0777 {PI}/resource/model",
        )

    adb(cfg, "shell", "chmod", "-R", "0777", PI)

    # verify
    print("--- verify ---")
    print("import:", adb(cfg, "shell", f"grep -A5 '\"import\"' {PI}/interface.json").stdout)
    print("pipeline:", adb(cfg, "shell", "ls", f"{PI}/resource/pipeline").stdout)
    print("Startup head:", adb(cfg, "shell", f"head -c 220 {PI}/resource/pipeline/Startup.json").stdout)
    print("images:", adb(cfg, "shell", f"find {PI}/resource/image -name '*.png' | wc -l").stdout.strip())
    print("model:", adb(cfg, "shell", "ls", f"{PI}/resource/model/ocr/rec.onnx").stdout.strip())
    print("tasks:", adb(cfg, "shell", "ls", f"{PI}/tasks").stdout)

    need = ["Startup.json", "Tacet.json", "TacetSelect.json"]
    pipes = adb(cfg, "shell", "ls", f"{PI}/resource/pipeline").stdout
    if not all(n in pipes for n in need):
        print("FAIL: missing pipeline files")
        return 1
    if "ExploreHUD" not in adb(cfg, "shell", f"grep -o ExploreHUD {PI}/resource/pipeline/Startup.json").stdout:
        print("FAIL: Startup.json missing ExploreHUD boundary")
        return 1
    if "rec.onnx" not in adb(cfg, "shell", "ls", f"{PI}/resource/model/ocr").stdout:
        print("FAIL: OCR model missing")
        return 1

    adb(cfg, "shell", "am", "force-stop", WW)
    print("PASS: PI pushed; App force-stopped — open App and reload project if needed, then verify Startup")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
