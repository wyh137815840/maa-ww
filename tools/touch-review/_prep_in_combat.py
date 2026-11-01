#!/usr/bin/env python3
from pathlib import Path
from brief import write_brief
from common import load_config

cfg = load_config()
dest = Path(cfg["inbox_dir"]) / "20261031-194504-tacet-in-combat.png"
write_brief(
    dest,
    title="无音区 · 第5步：战斗中 HUD（识别）",
    goal="标一个稳定的「在无音区战斗中」特征（只识别不点）。建议：左中目标条「清理无音区…」或顶中倒计时区域。",
    steps=[
        "优先框左侧任务目标「清理无音区中涌现的残象」整行（含 0/4）为 ROI。",
        "点击点可随便点在 ROI 中心（节点动作为 DoNothing，不会点）。",
        "label 用 InTacetCombat。导出后说「已导出」。",
        "右下技能键、小地图本次不要标。",
    ],
    suggested_label="InTacetCombat",
    suggested_expected_next="TacetClear or TacetSettle",
    suggested_note="ADB mumuscreen001。进本后战斗界面；用于判断已在无音区战斗中。",
    do_not=["不要标攻击/闪避键", "不要标角色头像换人"],
)
print(dest)
