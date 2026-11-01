#!/usr/bin/env python3
import json
import shutil
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[2]
card = json.loads(
    (root / "review/cards/20261031-202345-tacetclaimstaminadouble/card.json").read_text(encoding="utf-8")
)
screen = Image.open(root / card["files"]["screen"]).convert("RGB")
cx, cy = card["click"]
# tight button crop for template match
w, h = 200, 48
x1, y1 = max(0, cx - w // 2), max(0, cy - h // 2)
x2, y2 = min(1280, x1 + w), min(720, y1 + h)
roi = [x1, y1, x2 - x1, y2 - y1]
out = root / "assets/resource_adb/image/Guidebook/TacetClaimStaminaDouble.png"
screen.crop((x1, y1, x2, y2)).save(out)
# also keep card template as backup
shutil.copy2(root / card["files"]["template"], out.with_name("TacetClaimStaminaDouble_card.png"))
print("template", out, "roi", roi, "click", [cx, cy])

pipe_path = root / "assets/resource_adb/pipeline/Tacet.json"
pipe = json.loads(pipe_path.read_text(encoding="utf-8"))

pipe["TacetMain"]["desc"] = (
    "无音区：手册→无音清剿→直接挑战→开启挑战→战斗→挑战达成→领取奖励→"
    "耗体力(优先双倍120白字，否则单倍60；60与120皆红=体力耗尽结束并跳过后续耗体任务)→再战/离开。"
)
main = pipe["TacetMain"]["next"]
for name in ("TacetClaimStaminaDouble", "TacetClaimStamina", "TacetStaminaExhausted"):
    if name not in main:
        if "TacetNeedSettle" in main:
            main.insert(main.index("TacetNeedSettle"), name)
        else:
            main.append(name)
pipe["TacetMain"]["next"] = main

pipe["TacetClaimReward"]["next"] = [
    "TacetClaimStaminaDouble",
    "TacetClaimStamina",
    "TacetStaminaExhausted",
    "TacetNeedSettle",
]
pipe["TacetChallengeComplete"]["next"] = [
    "TacetClaimReward",
    "TacetClaimStaminaDouble",
    "TacetClaimStamina",
    "TacetStaminaExhausted",
]

pipe["TacetClaimStaminaDouble"] = {
    "desc": (
        "领取奖励弹窗右侧「120|双倍领取」（数字白字可点）。审查卡 20261031-202345。"
        "策略：能双倍不单倍。匹配失败再试单倍。"
    ),
    "recognition": "TemplateMatch",
    "roi": roi,
    "template": "Guidebook/TacetClaimStaminaDouble.png",
    "threshold": 0.72,
    "action": "Click",
    "target": [cx, cy],
    "post_wait_freezes": {"time": 400, "target": 0.95, "timeout": 8000},
    "next": ["TacetContinue", "TacetNeedSettle"],
}

pipe["TacetClaimStamina"] = {
    "desc": (
        "领取奖励弹窗左侧「60|单倍领取」（仅当双倍红字不可用）。"
        "审查卡待补；能双倍不单倍。"
    ),
    "recognition": "DirectHit",
    "action": "DoNothing",
    "next": ["TacetContinue", "TacetNeedSettle"],
}

pipe["TacetStaminaExhausted"] = {
    "desc": (
        "占位：领取弹窗上 60 与 120 数字皆为红字=体力不足，无法领取。"
        "应关闭弹窗/退出无音区任务并标记完成；同时置位「体力耗尽」使后续耗体力任务全部跳过。"
        "待热键截双红字画面后补 TemplateMatch；复杂判定可进 Go。"
    ),
    "recognition": "DirectHit",
    "action": "DoNothing",
    "next": [],
}

pipe["TacetContinue"] = {
    "desc": "占位：结算后「再次挑战/继续」。待标注。",
    "recognition": "DirectHit",
    "action": "DoNothing",
    "next": ["TacetNeedSettle"],
}

pipe["TacetNeedSettle"]["desc"] = (
    "占位汇总：单倍卡、双红耗尽识别、再次挑战/离开。策略见 TacetMain.desc。"
)

pipe_path.write_text(json.dumps(pipe, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
print("wired", pipe_path)
