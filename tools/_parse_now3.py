#!/usr/bin/env python3
from pathlib import Path

p = Path(r"D:\git\maa-ww\tools\_shots\maafw_now3.log")
t = p.read_text(encoding="utf-8", errors="ignore").splitlines()
keys = (
    "WalkToTacetTreasure",
    "pulseStick",
    "WriteFile",
    "PostShell",
    "Shell is not supported",
    "maaww_stick",
    "ClaimReward",
    "TacetTreasureDist",
    "CombatLoop",
    "TacetChallengeComplete",
    "TacetSettle",
    "TacetWalk",
    "Node.Action",
    "CustomAction",
)
hits = [l for l in t if any(k in l for k in keys)]
# drop noisy recognition spam unless action-ish
keep = []
for l in hits:
    if "Recognition" in l and "WalkToTacetTreasure" not in l and "CombatLoop" not in l:
        continue
    if "NextList" in l:
        continue
    keep.append(l)
print("hits", len(keep), "of", len(hits))
for l in keep[-100:]:
    print(l[:300])
