#!/usr/bin/env python3
"""Insert walk-to-treasure step between ChallengeComplete and ClaimReward (ok-ww walk_to_treasure / _ref TacetRewardTask)."""
from __future__ import annotations

import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "assets/resource_adb/pipeline/Tacet.json"

# 720p left-stick forward (scaled from ref 1080p 300,900→300,600)
STICK_FORWARD = {
    "type": "Swipe",
    "param": {
        "begin": [200, 600],
        "end": [200, 380],
        "duration": 450,
        "end_hold": 50,
    },
}


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))

    data["TacetApproachTreasure"] = {
        "desc": (
            "战斗结束→领奖前：走到宝藏旁（对齐 ok-ww walk_to_treasure / _ref approachReward）。"
            "出现「领取奖励」交互即停；否则寻宝藏标记或短步前进。完整转向环绕待 Go。"
        ),
        "timeout": 120000,
        "next": [
            "TacetClaimReward",
            "TacetTreasureMarker",
            "TacetWalkForward",
        ],
    }

    data["TacetTreasureMarker"] = {
        "desc": "通关宝藏标记（黄光）。模板自 _ref_maaww ww_tacet_treasure*。命中则短步前进靠近。",
        "recognition": "TemplateMatch",
        "roi": [200, 80, 880, 480],
        "template": [
            "Guidebook/TacetTreasure.png",
            "Guidebook/TacetTreasureGlow.png",
            "Guidebook/TacetTreasureFlare.png",
        ],
        "threshold": 0.55,
        "action": STICK_FORWARD,
        "post_delay": 200,
        "next": [
            "TacetClaimReward",
            "TacetApproachTreasure",
        ],
    }

    data["TacetWalkForward"] = {
        "desc": "未见领奖交互时左摇杆短步前进，回到 Approach 再认。",
        "recognition": "DirectHit",
        "action": STICK_FORWARD,
        "post_delay": 250,
        "next": [
            "TacetClaimReward",
            "TacetTreasureMarker",
            "TacetApproachTreasure",
        ],
    }

    # After banner: go approach first (claim only when near)
    data["TacetChallengeComplete"]["desc"] = (
        "战斗结束全屏提示「挑战达成」。审查卡 20261031-201111。纯识别；下一步走去领奖点，勿直接当已可贴脸领奖。"
    )
    data["TacetChallengeComplete"]["next"] = [
        "TacetClaimReward",
        "TacetApproachTreasure",
        "TacetChallengeComplete",
    ]
    data["TacetChallengeComplete"]["timeout"] = 30000

    # Combat loop: complete → approach path; still allow claim if already in range
    data["InTacetCombat"]["next"] = [
        "TacetChallengeComplete",
        "TacetClaimReward",
        "TacetApproachTreasure",
        "InTacetCombat",
    ]

    # Main entry include approach
    main_next = data["TacetMain"]["next"]
    if "TacetApproachTreasure" not in main_next:
        # insert after ChallengeComplete
        out = []
        for n in main_next:
            out.append(n)
            if n == "TacetChallengeComplete":
                out.append("TacetApproachTreasure")
        data["TacetMain"]["next"] = out

    data["TacetMain"]["desc"] = (
        "无音区：手册→选行→开启挑战→战斗→挑战达成→**走到宝藏**→领取奖励→结算/退出。"
        "IndexN 调试备用；走宝藏对齐 ok-ww walk_to_treasure。"
    )

    # Claim ROI slightly wider + OCR fallback node
    data["TacetClaimReward"]["roi"] = [700, 200, 400, 280]
    data["TacetClaimRewardByOCR"] = {
        "desc": "领取奖励 OCR 兜底（模板漂移时）。",
        "recognition": "OCR",
        "roi": [600, 180, 560, 360],
        "expected": ["领取奖励"],
        "action": "Click",
        "post_wait_freezes": {"time": 400, "timeout": 8000, "threshold": 0.95},
        "next": [
            "TacetClaimStaminaDouble",
            "TacetClaimStamina",
            "TacetStaminaExhausted",
            "TacetContinue",
            "TacetExit",
        ],
    }
    for key in ("TacetApproachTreasure", "TacetChallengeComplete", "InTacetCombat"):
        nxt = data[key]["next"]
        if "TacetClaimRewardByOCR" not in nxt:
            # after template claim
            if "TacetClaimReward" in nxt:
                i = nxt.index("TacetClaimReward") + 1
                nxt.insert(i, "TacetClaimRewardByOCR")
            else:
                nxt.insert(0, "TacetClaimRewardByOCR")

    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    print("ok: ApproachTreasure wired")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
