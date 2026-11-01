#!/usr/bin/env python3
import json
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[2]
card = json.loads(
    (root / "review/cards/20261031-203550-tacetstaminaexhausted/card.json").read_text(encoding="utf-8")
)
screen = Image.open(root / card["files"]["screen"]).convert("RGB")
# use card roi for tight X template
rx, ry, rw, rh = card["roi"]
out = root / "assets/resource_adb/image/Guidebook/TacetStaminaExhausted.png"
screen.crop((rx, ry, rx + rw, ry + rh)).save(out)
cx, cy = card["click"]
roi = [max(0, rx - 20), max(0, ry - 20), min(1280 - max(0, rx - 20), rw + 40), min(720 - max(0, ry - 20), rh + 40)]

pipe_path = root / "assets/resource_adb/pipeline/Tacet.json"
pipe = json.loads(pipe_path.read_text(encoding="utf-8"))
pipe["TacetStaminaExhausted"] = {
    "desc": (
        "领取弹窗 60+120 皆红（体力不足）：点右上角关闭 X。审查卡 20261031-203550。"
        "关闭后结束无音区并标记完成；应置位「体力耗尽」使后续耗体力任务全部跳过（Interface/Go 待接）。"
    ),
    "recognition": "TemplateMatch",
    "roi": roi,
    "template": "Guidebook/TacetStaminaExhausted.png",
    "threshold": 0.75,
    "action": "Click",
    "target": [cx, cy],
    "post_wait_freezes": {"time": 300, "target": 0.95, "timeout": 5000},
    "next": [],
}
# After claim reward prompt, exhaustion closes dialog — order: double → single → exhausted
pipe["TacetClaimReward"]["next"] = [
    "TacetClaimStaminaDouble",
    "TacetClaimStamina",
    "TacetStaminaExhausted",
    "TacetContinue",
    "TacetExit",
]
pipe["TacetNeedSettle"]["desc"] = "结算链已齐；跨任务跳过耗体待 Interface/Go 接「体力耗尽」标志。"
pipe["TacetMain"]["desc"] = (
    "无音区：手册→挑战→战斗→达成→领奖→双倍优先/单倍回退/双红关窗耗尽→重新挑战或退出。"
    "双红耗尽后跳过后续耗体任务（全局标志待接）。多副本选行待补。"
)

pipe_path.write_text(json.dumps(pipe, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
print("template", out, "roi", roi, "click", [cx, cy])
print("wired", pipe_path)
