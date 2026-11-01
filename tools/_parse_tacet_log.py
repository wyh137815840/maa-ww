#!/usr/bin/env python3
"""Print recent Tacet node transitions from a pulled maafw.log."""
from __future__ import annotations

import re
from pathlib import Path

LOG = Path(r"D:\git\maa-ww\tools\_shots\maafw_now.log")
text = LOG.read_text(encoding="utf-8", errors="ignore")
NAME = re.compile(r'"name"\s*:\s*"([^"]+)"')
CUR = re.compile(r"cur_node_=([A-Za-z0-9_]+)")
HIT = re.compile(r"analyze\(\)\]\s+(\S+)\s+.*?filtered_results_=(\[[^\]]{0,120})")

out: list[tuple[str, str, str]] = []
for ln in text.splitlines():
    if "2026-11-01 0" not in ln[:24]:
        continue
    ts = ln[1:23]
    if "Node.Action.Succeeded" in ln:
        m = NAME.search(ln)
        out.append((ts, "ACT", m.group(1) if m else "?"))
    elif "Node.PipelineNode.Succeeded" in ln:
        m = NAME.search(ln)
        out.append((ts, "NODE", m.group(1) if m else "?"))
    elif "Node.PipelineNode.Failed" in ln or "invalid node id" in ln or "PipelineTask bad next" in ln:
        m = NAME.search(ln) or CUR.search(ln) or re.search(r"node\.name=(\S+)", ln)
        out.append((ts, "FAIL", m.group(1) if m else ln[-140:]))
    elif "Tasker.Task.Failed" in ln or "Tasker.Task.Succeeded" in ln:
        kind = "TASK_OK" if "Succeeded" in ln else "TASK_FAIL"
        m = re.search(r'"entry"\s*:\s*"([^"]+)"', ln)
        out.append((ts, kind, m.group(1) if m else ""))
    elif "TemplateMatcher.cpp" in ln and "filtered_results_=[]" not in ln and "filtered_results_=[" in ln:
        m = HIT.search(ln)
        if m and m.group(2) not in ("[]", ""):
            out.append((ts, "HIT", f"{m.group(1)} {m.group(2)[:90]}"))

dedup: list[tuple[str, str, str]] = []
for row in out:
    if not dedup or dedup[-1][1:] != row[1:]:
        dedup.append(row)

# last task start
starts = [i for i, row in enumerate(dedup) if row[1] == "ACT" and row[2] in ("TacetMain", "StartupMain")]
begin = starts[-1] if starts else max(0, len(dedup) - 80)
for ts, kind, name in dedup[begin:]:
    print(f"{ts} {kind:8} {name}")
print(f"shown={len(dedup) - begin} total={len(dedup)}")
