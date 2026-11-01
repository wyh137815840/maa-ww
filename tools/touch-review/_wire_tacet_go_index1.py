#!/usr/bin/env python3
import json
import shutil
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[2]
card = json.loads((root / "review/cards/20261031-204447-tacetgoindex1/card.json").read_text(encoding="utf-8"))
screen = Image.open(root / card["files"]["screen"]).convert("RGB")
rx, ry, rw, rh = card["roi"]
out = root / "assets/resource_adb/image/Guidebook/TacetGoIndex1.png"
screen.crop((rx, ry, rx + rw, ry + rh)).save(out)
# keep generic go button as alias of index1 for backward compat if needed
shutil.copy2(out, root / "assets/resource_adb/image/Guidebook/TacetGoButton.png")

cx, cy = card["click"]
pipe_path = root / "assets/resource_adb/pipeline/Tacet.json"
pipe = json.loads(pipe_path.read_text(encoding="utf-8"))

pipe["TacetGoIndex1"] = {
    "desc": "无音区列表第1行「直接挑战」。审查卡 20261031-204447。配置序号=1。",
    "recognition": "TemplateMatch",
    "roi": [rx, ry, rw, rh],
    "template": "Guidebook/TacetGoIndex1.png",
    "threshold": 0.7,
    "action": "Click",
    "target": [cx, cy],
    "post_wait_freezes": {"time": 400, "target": 0.95, "timeout": 8000},
    "next": ["TacetStartChallenge", "InTacetCombat"],
}

# Default path uses Index1 until option wiring; keep old node as alias pointing same next
pipe["TacetGoButton"]["desc"] = (
    "兼容别名：等同默认第1行。优先用 TacetGoIndexN；多行标定后按任务选项切换。"
)
pipe["TacetGoButton"]["next"] = ["TacetStartChallenge", "InTacetCombat"]

main = pipe["TacetMain"]["next"]
if "TacetGoIndex1" not in main:
    if "TacetGoButton" in main:
        main.insert(main.index("TacetGoButton") + 1, "TacetGoIndex1")
    else:
        main.append("TacetGoIndex1")
pipe["GuidebookTacetTab"]["next"] = [
    "TacetGoIndex1",
    "TacetGoButton",
    "TacetStartChallenge",
]
pipe["TacetMain"]["desc"] = (
    "无音区：手册→无音清剿→按序号选行直接挑战(Index1起)→开启挑战→战斗→结算链。"
    "多行 Index2+ 待标；跨任务耗尽标志待接。"
)

pipe_path.write_text(json.dumps(pipe, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
print("wired Index1", out, "roi", [rx, ry, rw, rh], "click", [cx, cy])

# Prepare Index2 brief on a fresh inbox copy of the SAME list screen (not reusing exported flag)
inbox = root / "review/inbox"
src_png = inbox / Path(card["source_image"]).name
if not src_png.is_file():
    src_png = root / card["files"]["screen"]
dest = inbox / "20261031-tacet-go-index2.png"
shutil.copy2(src_png, dest)

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from brief import write_brief

write_brief(
    dest,
    title="无音区 · 多副本选行：第2行「直接挑战」",
    goal="标第2行右侧「直接挑战」（炽心域无音区一带）。与第1行错开，勿框到第1/3行。",
    steps=[
        "框住第2行「直接挑战」整颗。",
        "点击点在按钮中心。",
        "label=TacetGoIndex2 → 导出后说「已导出」。",
    ],
    suggested_label="TacetGoIndex2",
    suggested_expected_next="TacetStartChallenge",
    suggested_note="同列表图续标第2行。Index1 已入库 20261031-204447。",
    do_not=["不要标第1行", "不要标第3行及以下"],
)
print("brief", dest)
