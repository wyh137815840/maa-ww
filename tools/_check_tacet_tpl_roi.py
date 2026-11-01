#!/usr/bin/env python3
"""Flag TemplateMatch nodes where template size >= ROI (OpenCV empty match)."""
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
pipe = json.loads((ROOT / "assets/resource_adb/pipeline/Tacet.json").read_text(encoding="utf-8"))
img_root = ROOT / "assets/resource_adb/image"

for name, node in pipe.items():
    if node.get("recognition") != "TemplateMatch":
        continue
    tpl = node.get("template")
    roi = node.get("roi")
    if not tpl or not roi or len(roi) < 4:
        continue
    path = img_root / tpl
    if not path.is_file():
        print(f"MISSING {name}: {tpl}")
        continue
    w, h = Image.open(path).size
    rw, rh = roi[2], roi[3]
    bad = w >= rw or h >= rh
    mark = "BAD" if bad else "ok"
    print(f"{mark:3} {name}: tpl={w}x{h} roi={rw}x{rh} thr={node.get('threshold')}")
