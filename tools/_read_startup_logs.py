#!/usr/bin/env python3
"""Pull latest run + maafw log around Startup/ExploreHUD. No taps."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "review/inbox"
c = json.loads((ROOT / "tools/touch-review/config.json").read_text(encoding="utf-8"))
adb, s = c["adb_path"], c["serial"]
WW = "com.aliothmoon.maafw.maaww"
base = f"/storage/emulated/0/Android/data/{WW}/files"


def sh(*a, timeout=60):
    return subprocess.run(
        [adb, "-s", s, *a],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=timeout,
    )


# latest run jsonl
runs = sh("shell", f"ls -t {base}/log/run").stdout.split()
print("runs:", runs[:5])
if runs:
    latest = runs[0]
    sh("pull", f"{base}/log/run/{latest}", str(OUT / "_run_latest.jsonl"))
    print("=== run", latest, "===")
    print((OUT / "_run_latest.jsonl").read_text(encoding="utf-8", errors="ignore"))

# grepped maafw log
keys = (
    "ExploreHUD|TitleClickConnect|StartupLogin|StartUpGame|StartupMain|"
    "TemplateMatch|reco hit|task not found|资源加载|Task.Succeeded|Task.Failed|"
    "Node.Recognition|threshold|score|parse_"
)
g = sh(
    "shell",
    f"grep -nE '{keys}' {base}/log/maafw.log | tail -120",
)
(OUT / "_startup_maafw_grep.txt").write_text(g.stdout or "", encoding="utf-8")
print("=== maafw grep (tail) ===")
print((g.stdout or "")[-6000:])

# app log tail
sh("pull", f"{base}/log/app.log", str(OUT / "_app.log"))
app = (OUT / "_app.log").read_text(encoding="utf-8", errors="ignore")
print("=== app.log tail ===")
print(app[-2500:])

# screenshot current screen for HUD check
from datetime import datetime
import sys

sys.path.insert(0, str(ROOT / "tools/touch-review"))
from capture import capture_png
from common import load_config

cfg = load_config()
p = OUT / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-n-world-check.png"
print(capture_png(cfg["adb_path"], cfg["serial"], p, cfg), p.name)
