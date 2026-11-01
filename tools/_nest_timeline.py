#!/usr/bin/env python3
"""Deduplicated node timeline from tools/_shots/maafw_nest.log since a given HH:MM:SS (default: last 'Nest' task start)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
lines = (ROOT / "tools/_shots/maafw_nest.log").read_text(encoding="utf-8", errors="ignore").splitlines()
since = sys.argv[1] if len(sys.argv) > 1 else None
prev = None
for l in lines:
    if since and l[12:20] < since:
        continue
    if "Node.Action.Starting" in l or "PipelineNode.Failed" in l or "Task.Failed" in l or "Task.Succeeded" in l:
        m = re.search(r'"name":"(Nest[^"]*|Tacet[^"]*|Startup[^"]*)"', l)
        if not m:
            continue
        tag = ("F " if "Failed" in l else "") + m.group(1)
        if tag != prev:
            print(l[12:23], tag)
            prev = tag
