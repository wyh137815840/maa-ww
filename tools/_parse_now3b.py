#!/usr/bin/env python3
from pathlib import Path
import sys

paths = [Path(r"D:\git\maa-ww\tools\_shots\maafw_now3.log")]
if len(sys.argv) > 1:
    paths = [Path(sys.argv[1])]

want = (
    "WalkToTacetTreasure",
    "Shell is not supported",
    "PostShell",
    "pulseStick",
    "WriteFile failed",
    "CombatLoop",
    "TacetWalkToTreasure",
    "TacetClaimReward",
    "TacetChallengeComplete",
    "InTacetCombat",
    "TacetTreasureDist",
    "maaww_stick",
)

for p in paths:
    print("===", p)
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    for k in want:
        hits = [l for l in lines if k in l]
        print(f"{k}: {len(hits)}")
        for l in hits[-8:]:
            # shorten
            if "details=" in l:
                i = l.find("name")
                print(" ", l[l.find("[2026"):60] if False else l[:220])
            else:
                print(" ", l[:220])
    # node names that succeeded
    names = []
    for l in lines:
        if "Node.Action.Succeeded" in l and '"name":"' in l:
            # parse name
            import re

            m = re.search(r'"name":"([^"]+)"', l)
            if m:
                names.append(m.group(1))
    from collections import Counter

    c = Counter(names)
    print("top action nodes:")
    for n, cnt in c.most_common(25):
        print(f"  {cnt:4d} {n}")
