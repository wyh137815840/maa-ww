#!/usr/bin/env python3
"""Replace naive walk-forward with turn-toward-treasure + walk (Pipeline ROI split, align _ref approachReward)."""
from __future__ import annotations

import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "assets/resource_adb/pipeline/Tacet.json"

TEMPLATES = [
    "Guidebook/TacetTreasure.png",
    "Guidebook/TacetTreasureGlow.png",
    "Guidebook/TacetTreasureFlare.png",
]

# 720p from ref 1080p turn(center=1000,y=550): *1280/1920, *720/1080
# left turn swipe: right→left on look axis; right turn: left→right
TURN_LEFT = {
    "type": "Swipe",
    "param": {"begin": [787, 367], "end": [547, 367], "duration": 280, "end_hold": 30},
}
TURN_RIGHT = {
    "type": "Swipe",
    "param": {"begin": [547, 367], "end": [787, 367], "duration": 280, "end_hold": 30},
}
TURN_SEARCH = {
    "type": "Swipe",
    "param": {"begin": [880, 367], "end": [450, 367], "duration": 320, "end_hold": 30},
}
WALK_FWD = {
    "type": "Swipe",
    "param": {"begin": [200, 600], "end": [200, 360], "duration": 500, "end_hold": 40},
}
WALK_FWD_SHORT = {
    "type": "Swipe",
    "param": {"begin": [200, 600], "end": [200, 420], "duration": 280, "end_hold": 40},
}


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))

    data["TacetApproachTreasure"] = {
        "desc": (
            "领奖前导航：按宝藏标左右分区转向，居中后前进（对齐 _ref TacetRewardTask.approachReward）。"
            "停止条件=出现领取奖励交互。不是盲目断步前进。"
        ),
        "timeout": 180000,
        "next": [
            "TacetClaimReward",
            "TacetClaimRewardByOCR",
            "TacetTreasureCenter",
            "TacetTreasureLeft",
            "TacetTreasureRight",
            "TacetTreasureSearch",
        ],
    }

    data["TacetTreasureLeft"] = {
        "desc": "宝藏标在画面左侧 → 左转对准。",
        "recognition": "TemplateMatch",
        "roi": [40, 60, 500, 520],
        "template": TEMPLATES,
        "threshold": 0.55,
        "action": TURN_LEFT,
        "post_delay": 150,
        "next": [
            "TacetClaimReward",
            "TacetClaimRewardByOCR",
            "TacetApproachTreasure",
        ],
    }

    data["TacetTreasureRight"] = {
        "desc": "宝藏标在画面右侧 → 右转对准。",
        "recognition": "TemplateMatch",
        "roi": [740, 60, 500, 520],
        "template": TEMPLATES,
        "threshold": 0.55,
        "action": TURN_RIGHT,
        "post_delay": 150,
        "next": [
            "TacetClaimReward",
            "TacetClaimRewardByOCR",
            "TacetApproachTreasure",
        ],
    }

    data["TacetTreasureCenter"] = {
        "desc": "宝藏标已在画面中带 → 前进靠近。偏高（更远）用较长前进。",
        "recognition": "TemplateMatch",
        "roi": [480, 60, 320, 480],
        "template": TEMPLATES,
        "threshold": 0.55,
        "action": WALK_FWD,
        "post_delay": 180,
        "next": [
            "TacetClaimReward",
            "TacetClaimRewardByOCR",
            "TacetApproachTreasure",
        ],
    }

    data["TacetTreasureSearch"] = {
        "desc": "未见宝藏标：宽角度搜索转向（同向扫，避免原地来回）。",
        "recognition": "DirectHit",
        "action": TURN_SEARCH,
        "post_delay": 200,
        "next": [
            "TacetClaimReward",
            "TacetClaimRewardByOCR",
            "TacetTreasureCenter",
            "TacetTreasureLeft",
            "TacetTreasureRight",
            "TacetApproachTreasure",
        ],
    }

    # remove obsolete naive forward-only node if present
    data.pop("TacetWalkForward", None)
    data.pop("TacetTreasureMarker", None)

    # keep ChallengeComplete / InTacetCombat wiring
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
    print("ok: turn-toward-treasure approach")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
