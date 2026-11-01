#!/usr/bin/env python3
"""Derive row geometry from Index1-3; synthesize Index4 template/node; document scroll plan."""
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[2]
cards = {
    1: json.loads((root / "review/cards/20261031-204447-tacetgoindex1/card.json").read_text(encoding="utf-8")),
    2: json.loads((root / "review/cards/20261031-204735-tacetgoindex2/card.json").read_text(encoding="utf-8")),
    3: json.loads((root / "review/cards/20261031-204819-tacetgoindex3/card.json").read_text(encoding="utf-8")),
}

ys = [cards[i]["click"][1] for i in (1, 2, 3)]
xs = [cards[i]["click"][0] for i in (1, 2, 3)]
pitches = [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
pitch = int(round(sum(pitches) / len(pitches)))
x_click = int(round(sum(xs) / len(xs)))
print("click_ys", ys, "pitch", pitch, "pitches", pitches, "x", x_click)

# Prefer exported Index4 if present
idx4_dir = root / "review/cards/20261031-2049-placeholder"
exported4 = None
for d in (root / "review/cards").glob("*tacetgoindex4*"):
    cj = d / "card.json"
    if cj.is_file():
        exported4 = json.loads(cj.read_text(encoding="utf-8"))
        print("found exported Index4", d.name, exported4["click"])
        break

screen = Image.open(root / cards[1]["files"]["screen"]).convert("RGB")
img_dir = root / "assets/resource_adb/image/Guidebook"

# Use Index2's tight button crop size as template size for synth rows
tw, th = 157, 42

def make_row(n: int, cy: int, cx: int | None = None):
    cx = x_click if cx is None else cx
    x1 = max(0, cx - tw // 2)
    y1 = max(0, cy - th // 2)
    x2 = min(1280, x1 + tw)
    y2 = min(720, y1 + th)
    roi = [x1, y1, x2 - x1, y2 - y1]
    out = img_dir / f"TacetGoIndex{n}.png"
    screen.crop((x1, y1, x2, y2)).save(out)
    return {
        "desc": f"无音区列表第{n}行「直接挑战」。由 Index1-3 行距外推（pitch≈{pitch}）。配置序号={n}。",
        "recognition": "TemplateMatch",
        "roi": roi,
        "template": f"Guidebook/TacetGoIndex{n}.png",
        "threshold": 0.7,
        "action": "Click",
        "target": [cx, cy],
        "post_wait_freezes": {"time": 400, "target": 0.95, "timeout": 8000},
        "next": ["TacetStartChallenge", "InTacetCombat"],
    }, out, roi, [cx, cy]

pipe_path = root / "assets/resource_adb/pipeline/Tacet.json"
pipe = json.loads(pipe_path.read_text(encoding="utf-8"))

# Ensure 1-3 from cards (already wired); synth 4 if needed
if exported4:
    rx, ry, rw, rh = exported4["roi"]
    cx, cy = exported4["click"]
    out = img_dir / "TacetGoIndex4.png"
    Image.open(root / exported4["files"]["screen"]).convert("RGB").crop((rx, ry, rx + rw, ry + rh)).save(out)
    node = {
        "desc": f"无音区列表第4行「直接挑战」。审查卡 {exported4['id']}。配置序号=4。",
        "recognition": "TemplateMatch",
        "roi": [rx, ry, rw, rh],
        "template": "Guidebook/TacetGoIndex4.png",
        "threshold": 0.7,
        "action": "Click",
        "target": [cx, cy],
        "post_wait_freezes": {"time": 400, "target": 0.95, "timeout": 8000},
        "next": ["TacetStartChallenge", "InTacetCombat"],
    }
    print("Index4 from export", [cx, cy], [rx, ry, rw, rh])
else:
    cy4 = ys[-1] + pitch
    node, out, roi, click = make_row(4, cy4)
    print("Index4 synthesized", click, roi, "->", out)

pipe["TacetGoIndex4"] = node

# Scroll helper placeholder: swipe list upward to reveal next page of rows
pipe["TacetListSwipeUp"] = {
    "desc": (
        "无音区列表上划一页（露出第5行及以后）。左列为副本名、右列为「直接挑战」。"
        "后续按序号/OCR 名称点对应行；复杂滚动对齐 ok-ww click_on_book_target，宜进 Go。"
    ),
    "recognition": "DirectHit",
    "action": "Swipe",
    "begin": [640, 560],
    "end": [640, 280],
    "duration": 400,
    "next": ["TacetGoIndex1", "TacetGoIndex2", "TacetGoIndex3", "TacetGoIndex4", "TacetNeedMoreRows"],
}
pipe["TacetNeedMoreRows"] = {
    "desc": "占位：第5行起需滚动后按名称 OCR 或继续 IndexN 标定。ok-ww structure=[4,5,5,7]。",
    "recognition": "DirectHit",
    "action": "DoNothing",
    "next": [],
}

def ensure(lst, name, after=None):
    if name in lst:
        return
    if after and after in lst:
        lst.insert(lst.index(after) + 1, name)
    else:
        lst.append(name)

ensure(pipe["GuidebookTacetTab"]["next"], "TacetGoIndex4", "TacetGoIndex3")
ensure(pipe["TacetMain"]["next"], "TacetGoIndex4", "TacetGoIndex3")
ensure(pipe["TacetMain"]["next"], "TacetListSwipeUp")
ensure(pipe["TacetMain"]["next"], "TacetNeedMoreRows")

pipe["TacetMain"]["desc"] = (
    "无音区：手册→选行(Index1-4 首屏可模板；5+ 上划后按名/序号)→开启挑战→战斗→结算。"
    "行结构：左副本名，右「直接挑战」。行距由 Index1-3 标定约 "
    f"{pitch}px。"
)

pipe_path.write_text(json.dumps(pipe, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")

# geometry note for later Go
geo = {
    "row_pitch_px": pitch,
    "click_x": x_click,
    "index_click_y": {str(i): cards[i]["click"][1] for i in (1, 2, 3)},
    "index4_click_y": node["target"][1],
    "first_screen_rows": 4,
    "ok_ww_structure": [4, 5, 5, 7],
    "layout": "left=name, right=直接挑战",
    "scroll": "Swipe up on list to reveal more; then match Go button / OCR name",
}
(root / "docs/zh_cn/tacet-row-geometry.json").write_text(
    json.dumps(geo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print("geometry", geo)
