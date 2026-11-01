#!/usr/bin/env python3
from pathlib import Path
from brief import write_brief
from common import load_config
from PIL import Image

cfg = load_config()
dest = Path(cfg["inbox_dir"]) / "20261031-194016-tacet-list-live.png"
im = Image.open(dest)
print("size", im.size)
write_brief(
    dest,
    title="无音区 · 第3步：列表「直接挑战」",
    goal="标右侧无音区列表第一条的「直接挑战」按钮。导出 TacetGoButton。",
    steps=[
        "确认左侧「无音清剿」已选中，右侧是无音区卡片列表。",
        "只框第一条（沉心域无音区）右侧黑色「直接挑战」按钮为 ROI。",
        "点按钮文字中心为点击点。",
        "导出后说「已导出」；之后可在游戏里点该按钮，停在下一界面再截。",
    ],
    suggested_label="TacetGoButton",
    suggested_expected_next="TacetChallengeConfirm or InWorldNearTacet",
    suggested_note="ADB mumuscreen001 实截 1280x720（桥接 192.168.1.50:5555）。文案是「直接挑战」不是「前往」。",
    do_not=["不要点左侧其它页签", "不要点返回/关闭", "不要点体力+号"],
)
print(dest)
