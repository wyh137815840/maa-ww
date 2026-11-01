#!/usr/bin/env python3
import re
from pathlib import Path

text = Path(r"D:\git\maa-ww\tools\_shots\maafw_combat.log").read_text(encoding="utf-8", errors="ignore")
idx = text.rfind('"entry":"TacetMain"')
print("last tacet idx", idx, "len", len(text))
chunk = text[idx:] if idx >= 0 else text[-300000:]
out = []
for ln in chunk.splitlines():
    interesting = any(
        s in ln
        for s in (
            "TacetCombat",
            "InTacetCombat",
            "maaww_pad",
            "Tasker.Task",
            "PipelineNode.Failed",
            "bad next",
            "Shell",
        )
    )
    if not interesting:
        continue
    if "TemplateMatcher" in ln and "filtered_results_=[]" in ln:
        continue
    ts = ln[1:20] if ln.startswith("[") else ""
    if "Action.Succeeded" in ln:
        msg = "ACT"
    elif "PipelineNode.Succeeded" in ln:
        msg = "NODE"
    elif "PipelineNode.Failed" in ln or "bad next" in ln:
        msg = "FAIL"
    elif "Tasker.Task" in ln:
        msg = "TASK"
    elif "Shell" in ln or "maaww_pad" in ln:
        msg = "SHELL"
    elif "filtered_results_=[" in ln and "filtered_results_=[]" not in ln:
        msg = "HIT"
    else:
        continue
    m = re.search(r'"name":"([^"]+)"', ln)
    name = m.group(1) if m else ""
    if not name:
        m2 = re.search(r"analyze\(\)\] (\S+)", ln)
        name = m2.group(1) if m2 else ln[30:160]
    out.append(f"{ts} {msg:5} {name[:100]}")

prev = ""
n = 0
shown = 0
for row in out:
    key = row[20:]
    if key == prev:
        n += 1
        continue
    if n:
        print(f"  x{n}")
    print(row)
    shown += 1
    prev = key
    n = 0
    if shown > 80:
        break
print("rows", len(out))
