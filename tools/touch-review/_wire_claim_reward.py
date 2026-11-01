#!/usr/bin/env python3
import json
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[2]
card = json.loads((root / "review/cards/20261031-200221-tacetclaimreward/card.json").read_text(encoding="utf-8"))
screen = Image.open(root / card["files"]["screen"]).convert("RGB")
cx, cy = card["click"]
w, h = 200, 56
x1 = max(0, cx - w // 2)
y1 = max(0, cy - h // 2)
x2 = min(1280, x1 + w)
y2 = min(720, y1 + h)
roi = [x1, y1, x2 - x1, y2 - y1]
out = root / "assets/resource_adb/image/Guidebook/TacetClaimReward.png"
screen.crop((x1, y1, x2, y2)).save(out)
print("template", out, "roi", roi, "click", card["click"])

pipe_path = root / "assets/resource_adb/pipeline/Tacet.json"
pipe = json.loads(pipe_path.read_text(encoding="utf-8"))

# After combat, look for claim reward; keep settle placeholder for stamina dialog
pipe["InTacetCombat"]["next"] = ["TacetClaimReward", "TacetNeedSettle"]
if "TacetChallengeComplete" in pipe.get("TacetMain", {}).get("next", []):
    pass
main_next = pipe["TacetMain"]["next"]
if "TacetClaimReward" not in main_next:
    # insert before TacetNeedSettle
    if "TacetNeedSettle" in main_next:
        i = main_next.index("TacetNeedSettle")
        main_next.insert(i, "TacetClaimReward")
    else:
        main_next.append("TacetClaimReward")
    pipe["TacetMain"]["next"] = main_next

pipe["TacetClaimReward"] = {
    "desc": "无音区清完后宝藏旁「领取奖励」。审查卡 20261031-200221-tacetclaimreward。挑战达成闪屏跳过。",
    "recognition": "TemplateMatch",
    "roi": roi,
    "template": "Guidebook/TacetClaimReward.png",
    "threshold": 0.7,
    "action": "Click",
    "target": card["click"],
    "post_wait_freezes": {"time": 400, "target": 0.95, "timeout": 8000},
    "next": ["TacetNeedSettle"],
}
pipe["TacetNeedSettle"]["desc"] = "占位：体力确认 / 再次挑战 / 离开，待标注。"

pipe_path.write_text(json.dumps(pipe, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
print("wired", pipe_path)
