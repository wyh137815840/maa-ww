#!/usr/bin/env python3
"""Capture a MuMu/ADB screenshot into review/inbox at 1280x720."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from PIL import Image

from common import load_config


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, text=True, capture_output=True)


def ensure_device(adb: str, serial: str) -> None:
    run([adb, "connect", serial], check=False)
    out = run([adb, "devices"]).stdout
    online = set()
    for ln in out.splitlines()[1:]:
        parts = ln.split()
        if len(parts) >= 2 and parts[1] == "device":
            online.add(parts[0])
    if serial not in online:
        raise SystemExit(f"device not online: {serial}\n{out}")


def capture_png(adb: str, serial: str, dest: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        remote = "/sdcard/maa_ww_touch_review.png"
        local_raw = Path(tmp) / "raw.png"
        run([adb, "-s", serial, "shell", "screencap", "-p", remote])
        run([adb, "-s", serial, "pull", remote, str(local_raw)])
        run([adb, "-s", serial, "shell", "rm", "-f", remote], check=False)
        img = Image.open(local_raw).convert("RGB")
        tw, th = load_config()["target_size"]
        if img.size != (tw, th):
            img = img.resize((tw, th), Image.Resampling.LANCZOS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest, format="PNG")


def main() -> int:
    cfg = load_config()
    parser = argparse.ArgumentParser(description="Capture ADB screenshot for touch review")
    parser.add_argument("--label", default="", help="optional filename label")
    parser.add_argument("--serial", default=cfg["serial"])
    parser.add_argument("--adb", default=cfg["adb_path"])
    args = parser.parse_args()

    adb = Path(args.adb)
    if not adb.is_file():
        raise SystemExit(f"adb not found: {adb}")

    ensure_device(str(adb), args.serial)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = f"-{args.label}" if args.label else ""
    out = cfg["inbox_dir"] / f"{stamp}{suffix}.png"
    capture_png(str(adb), args.serial, out)
    print(out)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        sys.stderr.write((exc.stderr or exc.stdout or str(exc)) + "\n")
        raise SystemExit(exc.returncode)
