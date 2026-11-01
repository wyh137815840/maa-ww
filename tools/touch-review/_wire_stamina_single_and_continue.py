#!/usr/bin/env python3
import json
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[2]
img_dir = root / "assets/resource_adb/image/Guidebook"
img_dir.mkdir(parents=True, exist_ok=True)


def crop_btn(card_id: str, out_name: str, tw: int = 200, th: int = 48):
    card = json.loads((root / f"review/cards/{card_id}/card.json").read_text(encoding="utf-8"))
    screen = Image.open(root / card["files"]["screen"]).convert("RGB")
    cx, cy = card["click"]
    x1 = max(0, cx - tw // 2)
    y1 = max(0, cy - th // 2)
    x2 = min(1280, x1 + tw)
    y2 = min(720, y1 + th)
    roi = [x1, y1, x2 - x1, y2 - y1]
    out = img_dir / out_name
    screen.crop((x1, y1, x2, y2)).save(out)
    print(out_name, "roi", roi, "click", [cx, cy])
    return card, roi, [cx, cy]


pipe_path = root / "assets/resource_adb/pipeline/Tacet.json"
pipe = json.loads(pipe_path.read_text(encoding="utf-8"))

single, s_roi, s_click = crop_btn(
    "20261031-202836-tacetclaimstamina", "TacetClaimStamina.png", 200, 52
)
cont, c_roi, c_click = crop_btn(
    "20261031-202743-tacetcontinue", "TacetContinue.png", 200, 48
)

pipe["TacetClaimStamina"] = {
    "desc": (
        "领取弹窗左侧「60|单倍领取」（60白/120红时回退）。审查卡 20261031-202836。"
        "仅当双倍不可用；能双倍不单倍。"
    ),
    "recognition": "TemplateMatch",
    "roi": s_roi,
    "template": "Guidebook/TacetClaimStamina.png",
    "threshold": 0.72,
    "action": "Click",
    "target": s_click,
    "post_wait_freezes": {"time": 400, "target": 0.95, "timeout": 8000},
    "next": ["TacetContinue", "TacetExit", "TacetNeedSettle"],
}

pipe["TacetContinue"] = {
    "desc": "结算页右侧「重新挑战」。审查卡 20261031-202743。续刷入口。",
    "recognition": "TemplateMatch",
    "roi": c_roi,
    "template": "Guidebook/TacetContinue.png",
    "threshold": 0.7,
    "action": "Click",
    "target": c_click,
    "post_wait_freezes": {"time": 500, "target": 0.95, "timeout": 15000},
    "next": ["InTacetCombat", "TacetChallengeComplete", "TacetClaimReward"],
}

pipe["TacetClaimStaminaDouble"]["next"] = [
    "TacetContinue",
    "TacetExit",
    "TacetNeedSettle",
]
pipe["TacetClaimReward"]["next"] = [
    "TacetClaimStaminaDouble",
    "TacetClaimStamina",
    "TacetStaminaExhausted",
    "TacetContinue",
    "TacetExit",
]

pipe["TacetExit"] = {
    "desc": "占位：结算页左侧「退出副本」。待标注审查卡。",
    "recognition": "DirectHit",
    "action": "DoNothing",
    "next": [],
}

pipe["TacetNeedSettle"]["desc"] = (
    "占位：双红体力耗尽识别、退出副本。单倍/双倍/重新挑战已入库。"
)

pipe_path.write_text(json.dumps(pipe, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
print("wired", pipe_path)
