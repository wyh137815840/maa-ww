#!/usr/bin/env python3
import json
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[2]
card = json.loads((root / "review/cards/20261031-203103-tacetexit/card.json").read_text(encoding="utf-8"))
screen = Image.open(root / card["files"]["screen"]).convert("RGB")
cx, cy = card["click"]
w, h = 200, 48
x1, y1 = max(0, cx - w // 2), max(0, cy - h // 2)
x2, y2 = min(1280, x1 + w), min(720, y1 + h)
roi = [x1, y1, x2 - x1, y2 - y1]
out = root / "assets/resource_adb/image/Guidebook/TacetExit.png"
screen.crop((x1, y1, x2, y2)).save(out)

pipe_path = root / "assets/resource_adb/pipeline/Tacet.json"
pipe = json.loads(pipe_path.read_text(encoding="utf-8"))
pipe["TacetExit"] = {
    "desc": "结算页左侧「退出副本」。审查卡 20261031-203103。收工/不续刷时点。",
    "recognition": "TemplateMatch",
    "roi": roi,
    "template": "Guidebook/TacetExit.png",
    "threshold": 0.7,
    "action": "Click",
    "target": [cx, cy],
    "post_wait_freezes": {"time": 400, "target": 0.95, "timeout": 10000},
    "next": [],
}
# Prefer continue when farming; exit also reachable after claim
for key in ("TacetClaimStaminaDouble", "TacetClaimStamina", "TacetContinue"):
    if key in pipe and "TacetExit" not in pipe[key].get("next", []):
        nxt = pipe[key].setdefault("next", [])
        if "TacetExit" not in nxt:
            nxt.append("TacetExit")

main = pipe["TacetMain"]["next"]
if "TacetExit" not in main:
    main.append("TacetExit")
pipe["TacetMain"]["desc"] = (
    "无音区：手册→直接挑战→战斗→挑战达成→领取奖励→"
    "双倍优先/单倍回退→重新挑战或退出副本。"
    "双红体力耗尽待补；多副本选行待补。"
)
pipe["TacetNeedSettle"]["desc"] = "占位：双红体力耗尽（TacetStaminaExhausted）待截图。"
pipe["TacetContinue"]["next"] = [
    "InTacetCombat",
    "TacetChallengeComplete",
    "TacetClaimReward",
    "TacetExit",
]

pipe_path.write_text(json.dumps(pipe, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
print("template", out, "roi", roi, "click", [cx, cy])
print("wired", pipe_path)
