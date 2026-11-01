#!/usr/bin/env python3
import json
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[2]
card_dir = root / "review/cards/20261031-201111-tacetchallengecomplete"
card = json.loads((card_dir / "card.json").read_text(encoding="utf-8"))

out = root / "assets/resource_adb/image/Guidebook/TacetChallengeComplete.png"
src = root / card["files"]["template"]
shutil.copy2(src, out)
roi = card["roi"]
print("template", out, "roi", roi)

pipe_path = root / "assets/resource_adb/pipeline/Tacet.json"
pipe = json.loads(pipe_path.read_text(encoding="utf-8"))

pipe["TacetChallengeComplete"] = {
    "desc": "战斗结束全屏提示「挑战达成」。审查卡 20261031-201111。纯识别、不点击。",
    "recognition": "TemplateMatch",
    "roi": roi,
    "template": "Guidebook/TacetChallengeComplete.png",
    "threshold": 0.7,
    "action": "DoNothing",
    "next": ["TacetClaimReward", "TacetNeedSettle"],
}

# combat → complete → claim
pipe["InTacetCombat"]["next"] = [
    "TacetChallengeComplete",
    "TacetClaimReward",
    "TacetNeedSettle",
]
pipe["TacetStartChallenge"]["next"] = [
    "InTacetCombat",
    "TacetChallengeComplete",
    "TacetClaimReward",
]

main = pipe["TacetMain"]["next"]
if "TacetChallengeComplete" not in main:
    if "TacetClaimReward" in main:
        main.insert(main.index("TacetClaimReward"), "TacetChallengeComplete")
    else:
        main.append("TacetChallengeComplete")
    pipe["TacetMain"]["next"] = main

pipe["TacetMain"]["desc"] = (
    "无音区：手册 → 无音清剿 → 直接挑战 → 开启挑战 → 战斗中 → 挑战达成(识别) → 领取奖励 →（待标）体力/再战。"
)
pipe["TacetClaimReward"]["desc"] = (
    "无音区清完后宝藏旁「领取奖励」。审查卡 20261031-200221-tacetclaimreward。"
)

pipe_path.write_text(json.dumps(pipe, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
print("wired", pipe_path)
