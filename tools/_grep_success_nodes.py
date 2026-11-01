#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
c = json.loads((ROOT / "tools/touch-review/config.json").read_text(encoding="utf-8"))
log = "/storage/emulated/0/Android/data/com.aliothmoon.maafw.maaww/files/log/maafw.log"
cmd = (
    "grep -E '01:4[0-3].*(TacetChallengeComplete|TacetClaimReward|InTacetCombat).*Succeeded|"
    "01:4[0-3].*TacetChallengeComplete \\[all_results_.*0\\.[6-9]|"
    "01:4[0-3].*PipelineNode.Succeeded.*Tacet|"
    "01:4[0-3].*Task timeout' "
    f"{log} | tail -60"
)
r = subprocess.run(
    [c["adb_path"], "-s", c["serial"], "shell", cmd],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="ignore",
)
print(r.stdout or r.stderr)
