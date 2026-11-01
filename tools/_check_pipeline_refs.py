#!/usr/bin/env python3
"""Validate every next/on_error/exit_nodes reference resolves to a node in resource_adb/pipeline."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPE = ROOT / "assets/resource_adb/pipeline"

nodes = {}
for f in sorted(PIPE.glob("*.json")):
    for k, v in json.loads(f.read_text(encoding="utf-8")).items():
        if k in nodes:
            print(f"DUP {k} in {f.name}")
        nodes[k] = (f.name, v)


def refs(node):
    for key in ("next", "on_error"):
        for n in node.get(key, []) or []:
            yield key, n.replace("[JumpBack]", "").replace("[Anchor]", "")
    act = node.get("action")
    if isinstance(act, dict):
        p = act.get("param", {}) or {}
        cp = p.get("custom_action_param") or {}
        if isinstance(cp, dict):
            for n in cp.get("exit_nodes", []) or []:
                yield "exit_nodes", n
            if cp.get("hud_node"):
                yield "hud_node", cp["hud_node"]


bad = 0
for name, (fn, node) in nodes.items():
    for kind, ref in refs(node):
        if ref not in nodes:
            bad += 1
            print(f"MISSING {fn}:{name}.{kind} -> {ref}")

for f in ROOT.glob("assets/tasks/*.json"):
    j = json.loads(f.read_text(encoding="utf-8"))
    for t in j.get("task", []):
        if t["entry"] not in nodes:
            bad += 1
            print(f"MISSING entry {f.name}:{t['entry']}")
    for o in j.get("option", {}).values():
        for c in o.get("cases", []):
            for n in c.get("pipeline_override", {}):
                if n not in nodes:
                    bad += 1
                    print(f"MISSING override {f.name}:{n}")

print("nodes:", len(nodes), "bad:", bad)
sys.exit(1 if bad else 0)
