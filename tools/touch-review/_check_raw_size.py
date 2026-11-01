#!/usr/bin/env python3
"""Pull one raw screencap (no resize) to verify Odin landscape size."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from common import load_config


def main() -> int:
    cfg = load_config()
    adb, serial = cfg["adb_path"], cfg["serial"]
    with tempfile.TemporaryDirectory() as tmp:
        local = Path(tmp) / "raw.png"
        remote = "/data/local/tmp/maa_ww_raw.png"
        subprocess.run([adb, "-s", serial, "shell", "rm", "-f", remote], check=False)
        subprocess.run([adb, "-s", serial, "shell", "screencap", "-p", remote], check=True)
        subprocess.run([adb, "-s", serial, "pull", remote, str(local)], check=True)
        im = Image.open(local)
        print("raw_size", im.size)
        print("target_size", tuple(cfg["target_size"]))
        tw, th = cfg["target_size"]
        if im.size[0] < im.size[1]:
            print("WARN: portrait capture; game may not be landscape-focused")
        scale = (tw / im.size[0], th / im.size[1])
        print("scale_to_720p", scale)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
