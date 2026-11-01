#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


def main() -> int:
    lines = Path(__file__).resolve().parents[2].joinpath(
        "review/inbox/_maafw_padfail.log"
    ).read_text(encoding="utf-8", errors="ignore").splitlines()

    idxs = [i for i, l in enumerate(lines) if "reco hit" in l and "StartupMain" in l]
    start = idxs[-1] if idxs else 0
    print("start", start, "time", lines[start][1:24] if start < len(lines) else "")

    for i, l in enumerate(lines[start:], start):
        if "AgentClient" in l:
            continue
        tm = re.search(r"\[(2026[^\]]+)\]", l)
        t = tm.group(1) if tm else ""

        m = re.search(r"reco hit \[result\.name=(\w+)", l)
        if m:
            print(f"{t} HIT {m.group(1)}")
            continue

        if "ClickKey" in l and "pipeline_data.name=" in l:
            m = re.search(r"pipeline_data\.name=(\w+)", l)
            print(f"{t} CLICKKEY {m.group(1) if m else '?'}")
            continue

        if "Node.Action.Succeeded" in l:
            m = re.search(r'"name"\s*:\s*"(\w+)"', l)
            if m and m.group(1).startswith("Startup"):
                print(f"{t} ACT {m.group(1)}")
            continue

        if "Node.NextList.Failed" in l:
            m = re.search(r'"name"\s*:\s*"(\w+)"', l)
            name = m.group(1) if m else "?"
            if name.startswith("Startup") or name in ("StartUpGameWait", "TitleClickConnect"):
                print(f"{t} FAILNEXT {name}")
            continue

        if "Task.PipelineTask.Failed" in l or "Task.PipelineTask.Succeeded" in l:
            print(f"{t} TASK {l[-100:]}")
            continue

        if "analyze()] Startup" in l and "TemplateMatcher" in l:
            m = re.search(
                r"analyze\(\)\] (\w+) \[all_results_=(\[[^\]]*\])\] \[filtered_results_=(\[[^\]]*\])\]",
                l,
            )
            if not m:
                continue
            name, allr, filtr = m.group(1), m.group(2), m.group(3)
            if name in (
                "StartupWorldLoadingBar",
                "StartupPadReady",
                "StartupWorldHUD",
                "StartupWorldReady",
                "StartupLoadingBar",
            ):
                if filtr != "[]" or (allr != "[]" and "score" in allr):
                    # only print meaningful
                    score = re.search(r'"score":([0-9.]+)', allr)
                    sc = score.group(1) if score else "-"
                    hit = "PASS" if filtr != "[]" else "fail"
                    print(f"{t} MATCH {name} score={sc} {hit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
