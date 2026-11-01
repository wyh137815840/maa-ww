#!/usr/bin/env python3
import re
import subprocess
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/touch-review"))
from common import load_config

cfg = load_config()
local = ROOT / "tools/_shots/maafw_readyrt.log"
subprocess.run(
    [cfg["adb_path"], "-s", cfg["serial"], "pull",
     "/sdcard/Android/data/com.aliothmoon.maafw.maaww/files/log/maafw.log", str(local)],
    capture_output=True,
)
lines = local.read_text(encoding="utf-8", errors="ignore").splitlines()
# focus from last StartupMain
idxs = [i for i, l in enumerate(lines) if "Node.Action.Starting" in l and "StartupMain" in l]
start = idxs[-1] if idxs else max(0, len(lines) - 5000)
seg = lines[start:]
print("from line", start, "n", len(seg))
names = []
for l in seg:
    if "Node.Action.Starting" in l:
        m = re.search(r'"name":"([^"]+)"', l)
        if m:
            names.append(m.group(1))
print("actions:", names)
print("top", Counter(names).most_common(20))
for key in ("Task.Succeeded", "Task.Failed", "PipelineTask", "OpenGuidebook", "StartupPadReadyRT", "InInstanceClaimHint", "WalkToTacetTreasure", "InTacetCombat"):
    hits = [l for l in seg if key in l]
    print(key, len(hits))
    for l in hits[-5:]:
        print(" ", l[:220])
