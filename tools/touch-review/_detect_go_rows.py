#!/usr/bin/env python3
"""Detect right-side 直接挑战 buttons on scrolled tacet list; wire Index4-7."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

root = Path(__file__).resolve().parents[2]
# Prefer the clearer full-row shot
candidates = [
    root / "review/inbox/20261031-205201-snap.png",
    root / "review/inbox/20261031-205216-snap.png",
]
src = next(p for p in candidates if p.is_file())
im = Image.open(src).convert("RGB")
w, h = im.size
print("source", src.name, w, h)

# Scan right column for dark horizontal buttons
x0, x1 = 1040, 1220
dark = []
for y in range(120, 680):
    count = 0
    for x in range(x0, x1):
        r, g, b = im.getpixel((x, y))
        if r < 45 and g < 45 and b < 45:
            count += 1
    if count > 80:
        dark.append(y)

# Cluster into bands
bands = []
if dark:
    start = prev = dark[0]
    for y in dark[1:]:
        if y - prev > 3:
            bands.append((start, prev))
            start = y
        prev = y
    bands.append((start, prev))

# Filter button-like height ~20-55px
btns = []
for y_a, y_b in bands:
    bh = y_b - y_a + 1
    if 18 <= bh <= 60:
        cy = (y_a + y_b) // 2
        # refine click x: center of dark run at cy
        xs = [x for x in range(x0, x1) if sum(im.getpixel((x, cy))) < 120]
        if not xs:
            continue
        cx = (min(xs) + max(xs)) // 2
        btns.append((cx, cy, y_a, y_b, min(xs), max(xs)))

print("detected buttons:")
for i, (cx, cy, ya, yb, xa, xb) in enumerate(btns, 1):
    print(f"  vis#{i} click=[{cx},{cy}] y={ya}-{yb} x={xa}-{xb}")

# Map: after scroll, first full button is global index 4
# User said image contains rows 4-7; if 5 buttons, last may be partial row 8 — keep first 4
if len(btns) < 4:
    raise SystemExit(f"need >=4 buttons, got {len(btns)}")

use = btns[:4]  # Index4..Index7
img_dir = root / "assets/resource_adb/image/Guidebook"
img_dir.mkdir(parents=True, exist_ok=True)

pipe_path = root / "assets/resource_adb/pipeline/Tacet.json"
pipe = json.loads(pipe_path.read_text(encoding="utf-8"))

# Also save this screen into a review card-ish folder for provenance
prov = root / "review/cards/manual-tacet-rows-4to7"
prov.mkdir(parents=True, exist_ok=True)
im.save(prov / "screen.png")

names_guess = [
    "玄幽东岳无音区",
    "落日堤屿无音区",
    "冰原运输港无音区",
    "加拉尔冠阶无音区",
]

for i, (cx, cy, ya, yb, xa, xb) in enumerate(use):
    idx = 4 + i
    pad = 6
    x1b, y1b = max(0, xa - pad), max(0, ya - pad)
    x2b, y2b = min(w, xb + pad), min(h, yb + pad)
    roi = [x1b, y1b, x2b - x1b, y2b - y1b]
    out = img_dir / f"TacetGoIndex{idx}.png"
    im.crop((x1b, y1b, x2b, y2b)).save(out)
    node = {
        "desc": (
            f"无音区列表第{idx}行「直接挑战」（约{names_guess[i]}）。"
            f"来源滚动截图 {src.name}。配置序号={idx}。"
        ),
        "recognition": "TemplateMatch",
        "roi": roi,
        "template": f"Guidebook/TacetGoIndex{idx}.png",
        "threshold": 0.7,
        "action": "Click",
        "target": [cx, cy],
        "post_wait_freezes": {"time": 400, "target": 0.95, "timeout": 8000},
        "next": ["TacetStartChallenge", "InTacetCombat"],
    }
    pipe[f"TacetGoIndex{idx}"] = node
    print(f"Index{idx}", roi, [cx, cy], "->", out.name)

# Update next lists
keys = [f"TacetGoIndex{n}" for n in range(1, 8)]

def merge_go(lst: list) -> list:
    out = []
    seen = set()
    # put Index1..7 first among go nodes
    for k in keys:
        if k not in seen:
            out.append(k)
            seen.add(k)
    for x in lst:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out

pipe["GuidebookTacetTab"]["next"] = merge_go(
    [x for x in pipe["GuidebookTacetTab"]["next"] if not str(x).startswith("TacetGoIndex")]
    + keys
    + ["TacetGoButton", "TacetStartChallenge"]
)
main = pipe["TacetMain"]["next"]
# ensure all index keys present near front after tab
for k in keys:
    if k not in main:
        if "TacetGoButton" in main:
            main.insert(main.index("TacetGoButton"), k)
        else:
            main.append(k)
pipe["TacetMain"]["next"] = main
pipe["TacetMain"]["desc"] = (
    "无音区：手册→按序号选行(Index1-7 已有模板；区间头会打断行距，滚动后以各 Index 模板为准)"
    "→开启挑战→战斗→结算。左名右「直接挑战」。更多行继续上划截图标定或 Go+OCR。"
)
pipe["TacetNeedMoreRows"]["desc"] = (
    "占位：第8行起。再上划截图后继续 IndexN，或 Go 按副本名 OCR。"
)

pipe_path.write_text(json.dumps(pipe, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")

geo_path = root / "docs/zh_cn/tacet-row-geometry.json"
geo = {}
if geo_path.is_file():
    geo = json.loads(geo_path.read_text(encoding="utf-8"))
geo["scrolled_4_to_7_source"] = str(src.relative_to(root)).replace("\\", "/")
geo["index_4_to_7"] = {
    str(4 + i): {"click": [use[i][0], use[i][1]], "name_guess": names_guess[i]} for i in range(4)
}
geo["note_region_headers"] = "分区标题会插入列表，滚动后不能用固定 pitch 外推，需逐行检测或 OCR。"
geo_path.write_text(json.dumps(geo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("updated", pipe_path)
print("geometry", geo_path)
