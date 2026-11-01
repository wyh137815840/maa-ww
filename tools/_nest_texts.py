#!/usr/bin/env python3
"""Distinct OCR texts of a node over the last Nest run: python _nest_texts.py <Node> [log]"""
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
node = sys.argv[1]
log = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "tools/_shots/maafw_nest.log"
lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
start = max((i for i, l in enumerate(lines) if '"name":"NestMain"' in l), default=0)
cnt, first = Counter(), {}
for l in lines[start:]:
    if re.search(r"OCRer\.cpp.*\] " + node + r" ", l):
        m = re.search(r"all_results_=(\[.*?\]) \[filtered", l)
        k = "|".join(re.findall(r'"text":"([^"]*)"', m.group(1))) if m else ""
        cnt[k] += 1
        first.setdefault(k, l[12:23])
for k, v in cnt.most_common():
    print(v, first[k], repr(k))
