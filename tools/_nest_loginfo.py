#!/usr/bin/env python3
"""Summarise OCR/recognition results for given node names from tools/_shots/maafw_nest.log."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
lines = (ROOT / "tools/_shots/maafw_nest.log").read_text(encoding="utf-8", errors="ignore").splitlines()
names = sys.argv[1:] or ["NestInCombat", "NestClearedOCR"]
last_run = max((i for i, l in enumerate(lines) if '"name":"NestMain"' in l), default=0)
for n in names:
    hits = [l for l in lines[last_run:] if re.search(r"(OCRer|TemplateMatcher)\.cpp.*\] " + n + r" ", l)]
    print(f"== {n}: {len(hits)} analyses since last NestMain")
    for l in (hits[:3] + ["..."] + hits[-3:]) if len(hits) > 6 else hits:
        if l == "...":
            print("...")
            continue
        t = l[:23]
        m = re.search(r"all_results_=(\[.*?\]) \[filtered", l)
        print(t, (m.group(1) if m else l[-200:])[:300])
print("== timeline (since last NestMain)")
for l in lines[last_run:]:
    if "Node.Action.Starting" in l or "PipelineNode.Failed" in l or "Task.Failed" in l or "Task.Succeeded" in l:
        m = re.search(r'"name":"([^"]+)"', l)
        print(l[:23], ("F " if "Failed" in l else "") + (m.group(1) if m else "task"))
