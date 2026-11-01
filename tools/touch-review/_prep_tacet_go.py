#!/usr/bin/env python3
from pathlib import Path
import shutil
from brief import write_brief
from common import load_config

cfg = load_config()
inbox = Path(cfg["inbox_dir"])
# reuse normalized card screen (already 1280x720 game UI)
src = Path(cfg["cards_dir"]) / "20261031-192736-guidebooktacettab" / "screen.png"
dest = inbox / "20261031-192800-tacet-go-button.png"
shutil.copy2(src, dest)
write_brief(
    dest,
    title="无音区 · 第3步：列表「前往」",
    goal="标右侧无音区列表中某一条的「前往」按钮（先标第一条即可）。导出 TacetGoButton。",
    steps=[
        "右侧列表里找到第一条带「前往」的无音区（如炽心域无音区）。",
        "只框「前往」按钮本身为 ROI（不要框整行）。",
        "点「前往」文字中心为点击点。",
        "导出后说「已导出」；导出后可在游戏里点「前往」，停在传送确认/进战前界面等下一张。",
    ],
    suggested_label="TacetGoButton",
    suggested_expected_next="TacetTravelConfirm or InWorldNearTacet",
    suggested_note="同一手册画面复用。优先第一条「前往」，后续可用索引配置换目标。",
    do_not=["不要点左侧其它页签", "不要点返回", "不要点体力恢复"],
)
print(dest)
