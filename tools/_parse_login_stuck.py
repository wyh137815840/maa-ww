#!/usr/bin/env python3
import re
from collections import Counter
from pathlib import Path

lines = Path(r"D:\git\maa-ww\tools\_shots\maafw_stuck_login.log").read_text(
    encoding="utf-8", errors="ignore"
).splitlines()
# last StartupMain
idxs = [i for i, l in enumerate(lines) if "Node.Action.Starting" in l and '"name":"StartupMain"' in l]
start = idxs[-1] if idxs else max(0, len(lines) - 6000)
seg = lines[start:]
print("from", start, "lines", len(seg))
names = []
for l in seg:
    if "Node.Action.Starting" in l:
        m = re.search(r'"name":"([^"]+)"', l)
        if m:
            names.append(m.group(1))
print("actions:", names[-60:])
print("top:", Counter(names).most_common(20))
for k in (
    "InInstancePadMenu",
    "LeaveInstanceMenuOCR",
    "ConfirmLeaveInstance",
    "StartupPadReadyRT",
    "StartupPadReady",
    "OpenGuidebook",
    "TacetMain",
    "Task.Failed",
    "Task.Succeeded",
    "bad next",
    "invalid node",
):
    print(k, sum(1 for l in seg if k in l))
# last HIT / ACT
for l in seg[-200:]:
    if "reco hit" in l or "CLICKKEY" in l or "bad next" in l or "Task." in l:
        print(l[:240])
