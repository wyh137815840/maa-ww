#!/usr/bin/env python3
"""Keep Index4 on first-screen geometry; Index5-7 from scrolled shot only."""
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[2]
pipe_path = root / "assets/resource_adb/pipeline/Tacet.json"
pipe = json.loads(pipe_path.read_text(encoding="utf-8"))
img_dir = root / "assets/resource_adb/image/Guidebook"

# Restore Index4 from first-screen list (card Index1 screen)
screen1 = Image.open(root / "review/cards/20261031-204447-tacetgoindex1/screen.png").convert("RGB")
# pitch-based from Index1-3
cy4, cx4 = 541, 1146
tw, th = 157, 42
x1, y1 = max(0, cx4 - tw // 2), max(0, cy4 - th // 2)
x2, y2 = min(1280, x1 + tw), min(720, y1 + th)
roi4 = [x1, y1, x2 - x1, y2 - y1]
screen1.crop((x1, y1, x2, y2)).save(img_dir / "TacetGoIndex4.png")
pipe["TacetGoIndex4"] = {
    "desc": "无音区列表第4行「直接挑战」（首屏末行，约玄幽东岳）。由 Index1-3 行距外推。序号=4。未滚动时用此节点。",
    "recognition": "TemplateMatch",
    "roi": roi4,
    "template": "Guidebook/TacetGoIndex4.png",
    "threshold": 0.7,
    "action": "Click",
    "target": [cx4, cy4],
    "post_wait_freezes": {"time": 400, "target": 0.95, "timeout": 8000},
    "next": ["TacetStartChallenge", "InTacetCombat"],
}
print("restored Index4", roi4, [cx4, cy4])

# Index5-7 already set from scroll; tighten their desc
for n, name in [(5, "落日堤屿"), (6, "冰原运输港"), (7, "加拉尔冠阶")]:
    if f"TacetGoIndex{n}" in pipe:
        pipe[f"TacetGoIndex{n}"]["desc"] = (
            f"无音区列表第{n}行「直接挑战」（约{name}无音区）。"
            f"需先上划露出第二页；审查来源 20261031-205201-snap。序号={n}。"
        )

pipe["TacetListSwipeUp"]["next"] = [
    "TacetGoIndex5",
    "TacetGoIndex6",
    "TacetGoIndex7",
    "TacetNeedMoreRows",
]
pipe["TacetNeedMoreRows"]["desc"] = (
    "占位：第8行起（截图底部已露隐喙深腹）。继续上划截图或 Go+OCR 副本名。"
)

pipe_path.write_text(json.dumps(pipe, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
print("ok", pipe_path)
