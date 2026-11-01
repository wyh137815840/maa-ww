#!/usr/bin/env python3
import json
import shutil
import sys
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from brief import write_brief

card = json.loads((root / "review/cards/20261031-204819-tacetgoindex3/card.json").read_text(encoding="utf-8"))
screen = Image.open(root / card["files"]["screen"]).convert("RGB")
rx, ry, rw, rh = card["roi"]
out = root / "assets/resource_adb/image/Guidebook/TacetGoIndex3.png"
screen.crop((rx, ry, rx + rw, ry + rh)).save(out)
cx, cy = card["click"]

pipe_path = root / "assets/resource_adb/pipeline/Tacet.json"
pipe = json.loads(pipe_path.read_text(encoding="utf-8"))
pipe["TacetGoIndex3"] = {
    "desc": "无音区列表第3行「直接挑战」。审查卡 20261031-204819。配置序号=3。",
    "recognition": "TemplateMatch",
    "roi": [rx, ry, rw, rh],
    "template": "Guidebook/TacetGoIndex3.png",
    "threshold": 0.7,
    "action": "Click",
    "target": [cx, cy],
    "post_wait_freezes": {"time": 400, "target": 0.95, "timeout": 8000},
    "next": ["TacetStartChallenge", "InTacetCombat"],
}

def insert_after(lst, after, name):
    if name in lst:
        return lst
    if after in lst:
        lst.insert(lst.index(after) + 1, name)
    else:
        lst.append(name)
    return lst

pipe["GuidebookTacetTab"]["next"] = insert_after(pipe["GuidebookTacetTab"]["next"], "TacetGoIndex2", "TacetGoIndex3")
pipe["TacetMain"]["next"] = insert_after(pipe["TacetMain"]["next"], "TacetGoIndex2", "TacetGoIndex3")
pipe_path.write_text(json.dumps(pipe, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
print("wired Index3", out, "roi", [rx, ry, rw, rh], "click", [cx, cy])

src = root / "review/inbox" / Path(card["source_image"]).name
if not src.is_file():
    src = root / card["files"]["screen"]
dest = root / "review/inbox/20261031-tacet-go-index4.png"
shutil.copy2(src, dest)
write_brief(
    dest,
    title="无音区 · 多副本选行：第4行「直接挑战」",
    goal="标第4行右侧「直接挑战」（玄幽东岳无音区一带，首屏最后一行）。勿框到第3行。",
    steps=[
        "框住第4行「直接挑战」整颗。",
        "点击点在按钮中心。",
        "label=TacetGoIndex4 → 导出后说「已导出」。",
        "第5行及以后需滚动，首屏4行标完再议。",
    ],
    suggested_label="TacetGoIndex4",
    suggested_expected_next="TacetStartChallenge",
    suggested_note="同列表图。Index y≈235/338/439，第4行约540。",
    do_not=["不要标第3行", "不要标滚动条"],
)
print("brief", dest)
