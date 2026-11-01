#!/usr/bin/env python3
"""Poll maafw.log / go-service.log: print the node sequence since the last start."""
from __future__ import annotations

import _local_cfg
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
from common import load_config

PKG = "com.aliothmoon.maafw.maaww"
LOG = f"/sdcard/Android/data/{PKG}/files/log/maafw.log"
GO = f"/sdcard/Android/data/{PKG}/files/pi/debug/go-service.log"
OUT = ROOT / "tools/_shots"
SER = _local_cfg.serial()


def pull(cfg, remote, local):
    subprocess.run(
        f'cmd /c ""{cfg["adb_path"]}" -s {SER} exec-out cat {remote} > "{local}""',
        shell=True,
    )
    return Path(local).read_text(encoding="utf-8", errors="ignore").splitlines()


def main():
    cfg = load_config()
    secs = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    every = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    t0 = time.time()
    seen = 0
    while time.time() - t0 < secs:
        lines = pull(cfg, LOG, OUT / "maafw_nest.log")
        names = []
        for i, l in enumerate(lines):
            if "Node.Action.Starting" in l or "Node.PipelineNode.Failed" in l or "Task.Failed" in l or "Task.Succeeded" in l or "Task.Starting" in l:
                m = re.search(r'"name":"([^"]+)"', l)
                tag = ("F:" if "Failed" in l else "") + (m.group(1) if m else l[-60:])
                names.append((i, tag))
        new = [n for n in names if n[0] >= seen]
        if new:
            print(f"[{int(time.time()-t0):>3}s] " + " > ".join(n[1] for n in new[-40:]))
            seen = len(lines)
        time.sleep(every)
    go = pull(cfg, GO, OUT / "go_nest.log")
    print("--- go-service tail ---")
    for l in go[-25:]:
        print(l[-220:])


if __name__ == "__main__":
    main()
