#!/usr/bin/env python3
import json
import shutil
import sys
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from brief import write_brief

card = json.loads((root / "review/cards/20261031-204735-tacetgoindex2/card.json").read_text(encoding="utf-8"))
screen = Image.open(root / card["files"]["screen"]).convert("RGB")
rx, ry, rw, rh = card["roi"]
out = root / "assets/resource_adb/image/Guidebook/TacetGoIndex2.png"
screen.crop((rx, ry, rx + rw, ry + rh)).save(out)
cx, cy = card["click"]

pipe_path = root / "assets/resource_adb/pipeline/Tacet.json"
pipe = json.loads(pipe_path.read_text(encoding="utf-8"))
pipe["TacetGoIndex2"] = {
    "desc": "无音区列表第2行「直接挑战」。审查卡 20261031-204735。配置序号=2。",
    "recognition": "TemplateMatch",
    "roi": [rx, ry, rw, rh],
    "template": "Guidebook/TacetGoIndex2.png",
    "threshold": 0.7,
    "action": "Click",
    "target": [cx, cy],
    "post_wait_freezes": {"time": 400, "target": 0.95, "timeout": 8000},
    "next": ["TacetStartChallenge", "InTacetCombat"],
}
tab_next = pipe["GuidebookTacetTab"]["next"]
if "TacetGoIndex2" not in tab_next:
    # keep Index1 first for default; Index2 available as sibling
    if "TacetGoIndex1" in tab_next:
        tab_next.insert(tab_next.index("TacetGoIndex1") + 1, "TacetGoIndex2")
    else:
        tab_next.insert(0, "TacetGoIndex2")
    pipe["GuidebookTacetTab"]["next"] = tab_next
main = pipe["TacetMain"]["next"]
if "TacetGoIndex2" not in main:
    if "TacetGoIndex1" in main:
        main.insert(main.index("TacetGoIndex1") + 1, "TacetGoIndex2")
    else:
        main.append("TacetGoIndex2")
pipe_path.write_text(json.dumps(pipe, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
print("wired Index2", out, "roi", [rx, ry, rw, rh], "click", [cx, cy])

# Index3 inbox copy
src = root / "review/inbox" / Path(card["source_image"]).name
if not src.is_file():
    src = root / card["files"]["screen"]
dest = root / "review/inbox/20261031-tacet-go-index3.png"
shutil.copy2(src, dest)
write_brief(
    dest,
    title="无音区 · 多副本选行：第3行「直接挑战」",
    goal="标第3行右侧「直接挑战」（方掌西峰无音区一带）。勿框到第2/4行。",
    steps=[
        "框住第3行「直接挑战」整颗。",
        "点击点在按钮中心。",
        "label=TacetGoIndex3 → 导出后说「已导出」。",
    ],
    suggested_label="TacetGoIndex3",
    suggested_expected_next="TacetStartChallenge",
    suggested_note="同列表图。Index1/2 已入库。行距约 103px（235→338）。",
    do_not=["不要标第2行", "不要标第4行"],
)
print("brief", dest)
