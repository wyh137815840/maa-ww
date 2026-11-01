#!/usr/bin/env python3
"""Pull latest maafw.log and summarize Startup pad-switch path."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from common import load_config


def main() -> int:
    cfg = load_config()
    adb, serial = cfg["adb_path"], cfg["serial"]
    local = cfg["inbox_dir"] / "_maafw_padfail.log"
    subprocess.run(
        [adb, "-s", serial, "pull", "/sdcard/Android/data/com.aliothmoon.maafw.maaww/files/log/maafw.log", str(local)],
        capture_output=True,
    )
    lines = local.read_text(encoding="utf-8", errors="ignore").splitlines()
    print("lines", len(lines), "size", local.stat().st_size)

    idxs = [i for i, l in enumerate(lines) if "reco hit" in l and "StartupMain" in l]
    print("StartupMain hits", idxs[-5:] if idxs else None)
    start = idxs[-1] if idxs else max(0, len(lines) - 8000)

    out: list[str] = []
    for i, l in enumerate(lines[start:], start):
        if "AgentClient" in l:
            continue
        tm = re.search(r"\[(2026[^\]]+)\]", l)
        t = tm.group(1) if tm else ""

        m = re.search(r"analyze\(\)\] (\w+) \[all_results_=(\[[^\]]*\])", l)
        if m and "TemplateMatcher" in l:
            out.append(f"{t} MATCH {m.group(1)} {m.group(2)[:180]}")
            continue

        m = re.search(r"OCRer::analyze\(\)\] (\w+) .*?filtered_results_=(\[[^\]]*\])", l)
        if m:
            out.append(f"{t} OCR {m.group(1)} filtered={m.group(2)[:120]}")
            continue

        if "templ size is too large" in l:
            out.append(f"{t} ERR_TEMPL {l[l.find('templ'):][:100]}")
            continue

        m = re.search(r"reco hit \[result\.name=([^\]]+)\]", l)
        if m:
            out.append(f"{t} HIT {m.group(1)}")
            continue

        m = re.search(r"direct_hit\(.*?\)\] (\w+)", l)
        if m:
            out.append(f"{t} DHIT {m.group(1)}")
            continue

        if "ClickKey" in l and ("action" in l or "Actuator" in l or "TaskBase" in l):
            nm = re.search(r"pipeline_data\.name=(\w+)", l)
            out.append(f"{t} CLICKKEY {nm.group(1) if nm else '?'}")
            continue

        if "Node.Action.Succeeded" in l:
            nm = re.search(r'"name"\s*:\s*"(\w+)"', l)
            if nm:
                out.append(f"{t} ACT_OK {nm.group(1)}")
            continue

        if "Node.NextList.Failed" in l:
            nm = re.search(r'"name"\s*:\s*"(\w+)"', l)
            out.append(f"{t} NEXT_FAIL {nm.group(1) if nm else '?'}")
            continue

        if "Node.PipelineNode.Succeeded" in l:
            nm = re.search(r'"name"\s*:\s*"(\w+)"', l)
            if nm:
                out.append(f"{t} NODE_OK {nm.group(1)}")
            continue

        if "Task.PipelineTask.Failed" in l or "Task.PipelineTask.Succeeded" in l:
            out.append(f"{t} TASK {l[l.find('Task.Pipeline'):l.find('Task.Pipeline')+40]}")

    summary = cfg["inbox_dir"] / "_padfail_summary.txt"
    summary.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("summary", summary, "rows", len(out))
    for row in out[-150:]:
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
