#!/usr/bin/env python3
"""Restore full PI interface (Startup+Tacet+SkipDialog) + sync Official resource on device."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
from common import load_config

WW = "com.aliothmoon.maafw.maaww"
PI = f"/storage/emulated/0/Android/data/{WW}/files/pi"


def adb(cfg, *a):
    return subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *a],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )


def main() -> int:
    # 1) local sync resource_adb → resource
    r = subprocess.run([sys.executable, str(ROOT / "tools/sync_resource_from_adb.py")], cwd=ROOT)
    if r.returncode not in (0, 1):
        return r.returncode

    cfg = load_config()
    iface = json.loads((ROOT / "assets/interface.json").read_text(encoding="utf-8"))
    imports = iface.get("import") or []
    inline = [t["name"] for t in iface.get("task", [])]
    print("iface import:", imports, "inline tasks:", inline)
    has_tacet = "Tacet" in inline or any("Tacet" in str(p) for p in imports)
    if not has_tacet:
        print("ERROR: repo interface missing Tacet (inline or import)", file=sys.stderr)
        return 2

    # 2) push interface + locales + tasks
    adb(cfg, "push", str(ROOT / "assets/interface.json"), f"{PI}/interface.json")
    adb(cfg, "push", str(ROOT / "assets/locales/zh_cn.json"), f"{PI}/locales/zh_cn.json")
    adb(cfg, "push", str(ROOT / "assets/locales/en_us.json"), f"{PI}/locales/en_us.json")
    for f in (ROOT / "assets/tasks").glob("*.json"):
        adb(cfg, "push", str(f), f"{PI}/tasks/{f.name}")

    # 3) replace Official resource pipeline+image (keep model)
    adb(cfg, "shell", "rm", "-rf", f"{PI}/resource/pipeline", f"{PI}/resource/image")
    adb(cfg, "shell", "mkdir", "-p", f"{PI}/resource/pipeline", f"{PI}/resource/image")
    for f in (ROOT / "assets/resource/pipeline").glob("*.json"):
        adb(cfg, "push", str(f), f"{PI}/resource/pipeline/{f.name}")
    # push image tree via tar for speed
    img = ROOT / "assets/resource/image"
    if img.is_dir():
        tar = ROOT / "review/inbox/_res_image.tar"
        subprocess.run(
            ["tar", "-cf", str(tar), "-C", str(img), "."],
            check=False,
            capture_output=True,
        )
        if tar.exists() and tar.stat().st_size > 0:
            adb(cfg, "push", str(tar), "/sdcard/_res_image.tar")
            adb(
                cfg,
                "shell",
                f"mkdir -p {PI}/resource/image && tar -xf /sdcard/_res_image.tar -C {PI}/resource/image && chmod -R 0777 {PI}/resource",
            )
        else:
            # fallback: push each png
            for png in img.rglob("*.png"):
                rel = png.relative_to(img).as_posix()
                remote_dir = f"{PI}/resource/image/{png.parent.relative_to(img).as_posix()}"
                adb(cfg, "shell", "mkdir", "-p", remote_dir)
                adb(cfg, "push", str(png), f"{PI}/resource/image/{rel}")

    dp = ROOT / "assets/resource/default_pipeline.json"
    if dp.is_file():
        adb(cfg, "push", str(dp), f"{PI}/resource/default_pipeline.json")
    adb(cfg, "shell", "chmod", "-R", "0777", f"{PI}/resource")

    # verify remote listing
    print("remote pipeline:", adb(cfg, "shell", "ls", f"{PI}/resource/pipeline").stdout)
    print("remote tasks:", adb(cfg, "shell", "ls", f"{PI}/tasks").stdout)
    print(
        "remote iface task names:",
        adb(cfg, "shell", f"grep -o '\"name\": \"[^\"]*\"' {PI}/interface.json | head -20").stdout,
    )

    # force-stop so App reloads PI + native resource
    adb(cfg, "shell", "am", "force-stop", WW)
    time.sleep(0.5)
    print("restored full iface+resource; App force-stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
