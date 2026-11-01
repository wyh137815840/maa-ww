#!/usr/bin/env python3
"""Read latest Tacet failure logs. No taps."""
from __future__ import annotations

import json
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


runs = [x for x in sh("shell", f"ls -t {base}/log/run").stdout.split() if x.endswith(".jsonl")]
print("latest runs:", runs[:5])
for name in runs[:3]:
    sh("pull", f"{base}/log/run/{name}", str(OUT / f"_{name}"))
    text = (OUT / f"_{name}").read_text(encoding="utf-8", errors="ignore")
    print(f"\n===== {name} =====")
    print(text)

keys = (
    "Tacet|InTacet|ChallengeComplete|ClaimReward|ClaimStamina|TacetExit|TacetContinue|"
    "Task.Failed|Task.Succeeded|NextList.Failed|Recognition.Failed|Recognition.Succeeded|"
    "all_results|reco hit|timeout|PipelineNode"
)
g = sh("shell", f"grep -nE '{keys}' {base}/log/maafw.log | tail -150")
(OUT / "_tacet_fail_grep.txt").write_text(g.stdout or "", encoding="utf-8")
print("\n===== maafw grep tail =====")
print((g.stdout or "")[-8000:])
