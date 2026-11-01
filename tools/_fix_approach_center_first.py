#!/usr/bin/env python3
"""Approach treasure: locate → yaw until centered → then walk. Never walk while off-center."""
from __future__ import annotations

import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "assets/resource_adb/pipeline/Tacet.json"

TEMPLATES = [
    "Guidebook/TacetTreasure.png",
    "Guidebook/TacetTreasureGlow.png",
    "Guidebook/TacetTreasureFlare.png",
]

# Look axis @720p (from ref 1080p center≈1000,y≈550)
TURN_LEFT_FINE = {
    "type": "Swipe",
    "param": {"begin": [720, 367], "end": [600, 367], "duration": 160, "end_hold": 20},
}
TURN_LEFT_COARSE = {
    "type": "Swipe",
    "param": {"begin": [820, 367], "end": [520, 367], "duration": 280, "end_hold": 30},
}
TURN_RIGHT_FINE = {
    "type": "Swipe",
    "param": {"begin": [560, 367], "end": [680, 367], "duration": 160, "end_hold": 20},
}
TURN_RIGHT_COARSE = {
    "type": "Swipe",
    "param": {"begin": [460, 367], "end": [760, 367], "duration": 280, "end_hold": 30},
}
TURN_SEARCH = {
    "type": "Swipe",
    "param": {"begin": [900, 367], "end": [420, 367], "duration": 340, "end_hold": 30},
}
WALK_FWD = {
    "type": "Swipe",
    "param": {"begin": [200, 600], "end": [200, 360], "duration": 450, "end_hold": 40},
}


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))

    # Wait node: claim first; then LEFT/RIGHT turn before CENTER walk; then search
    data["TacetApproachTreasure"] = {
        "desc": (
            "领奖导航（强制顺序）：1) 定位宝藏标 2) 左右调整视角直到标进入屏幕中央带 "
            "3) 仅居中后才前进。对齐用户约定 / _ref approachReward。"
        ),
        "timeout": 180000,
        "next": [
            "TacetClaimReward",
            "TacetClaimRewardByOCR",
            "TacetTreasureLeftFar",
            "TacetTreasureRightFar",
            "TacetTreasureLeftNear",
            "TacetTreasureRightNear",
            "TacetTreasureCentered",
            "TacetTreasureSearch",
        ],
    }

    # Far left / right: coarse turn (mark clearly off-center)
    data["TacetTreasureLeftFar"] = {
        "desc": "宝藏在左半屏外侧 → 粗左转，直到靠近中央。禁止前进。",
        "recognition": "TemplateMatch",
        "roi": [20, 50, 420, 540],
        "template": TEMPLATES,
        "threshold": 0.55,
        "action": TURN_LEFT_COARSE,
        "post_delay": 120,
        "next": ["TacetClaimReward", "TacetClaimRewardByOCR", "TacetApproachTreasure"],
    }
    data["TacetTreasureRightFar"] = {
        "desc": "宝藏在右半屏外侧 → 粗右转。禁止前进。",
        "recognition": "TemplateMatch",
        "roi": [840, 50, 420, 540],
        "template": TEMPLATES,
        "threshold": 0.55,
        "action": TURN_RIGHT_COARSE,
        "post_delay": 120,
        "next": ["TacetClaimReward", "TacetClaimRewardByOCR", "TacetApproachTreasure"],
    }

    # Near left / right: fine yaw into center band (still no walk)
    data["TacetTreasureLeftNear"] = {
        "desc": "宝藏偏左（未进中央带）→ 微调左转。禁止前进。",
        "recognition": "TemplateMatch",
        "roi": [400, 50, 180, 540],
        "template": TEMPLATES,
        "threshold": 0.55,
        "action": TURN_LEFT_FINE,
        "post_delay": 100,
        "next": ["TacetClaimReward", "TacetClaimRewardByOCR", "TacetApproachTreasure"],
    }
    data["TacetTreasureRightNear"] = {
        "desc": "宝藏偏右（未进中央带）→ 微调右转。禁止前进。",
        "recognition": "TemplateMatch",
        "roi": [700, 50, 180, 540],
        "template": TEMPLATES,
        "threshold": 0.55,
        "action": TURN_RIGHT_FINE,
        "post_delay": 100,
        "next": ["TacetClaimReward", "TacetClaimRewardByOCR", "TacetApproachTreasure"],
    }

    # Only when marker is in narrow center band → walk
    data["TacetTreasureCentered"] = {
        "desc": "宝藏已在屏幕中央竖带 → 才允许前进靠近领奖点。",
        "recognition": "TemplateMatch",
        "roi": [560, 50, 160, 500],
        "template": TEMPLATES,
        "threshold": 0.55,
        "action": WALK_FWD,
        "post_delay": 160,
        "next": ["TacetClaimReward", "TacetClaimRewardByOCR", "TacetApproachTreasure"],
    }

    data["TacetTreasureSearch"] = {
        "desc": "未定位到宝藏标 → 搜索转向，再重新定位。禁止盲目前进。",
        "recognition": "DirectHit",
        "action": TURN_SEARCH,
        "post_delay": 180,
        "next": [
            "TacetClaimReward",
            "TacetClaimRewardByOCR",
            "TacetTreasureLeftFar",
            "TacetTreasureRightFar",
            "TacetTreasureLeftNear",
            "TacetTreasureRightNear",
            "TacetTreasureCentered",
            "TacetApproachTreasure",
        ],
    }

    # drop old names if any
    for k in (
        "TacetTreasureLeft",
        "TacetTreasureRight",
        "TacetTreasureCenter",
        "TacetTreasureMarker",
        "TacetWalkForward",
    ):
        data.pop(k, None)

    data["TacetChallengeComplete"]["next"] = [
        "TacetClaimReward",
        "TacetClaimRewardByOCR",
        "TacetApproachTreasure",
        "TacetChallengeComplete",
    ]
    data["InTacetCombat"]["next"] = [
        "TacetChallengeComplete",
        "TacetClaimReward",
        "TacetClaimRewardByOCR",
        "TacetApproachTreasure",
        "InTacetCombat",
    ]

    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    print("ok: locate → center view → then walk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
