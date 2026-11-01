#!/usr/bin/env python3
"""Aim the chest by swiping from screen center to the icon box.

Stroke length is the live x/y offset, not a fixed left/right flick.
Walk only after the icon sits in a small center window.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPE = ROOT / "assets/resource_adb/pipeline/Tacet.json"
TEMPLATES = [
    "Guidebook/TacetTreasure.png",
    "Guidebook/TacetTreasureGlow.png",
    "Guidebook/TacetTreasureFlare.png",
]
DROP = {
    "TacetTreasureLeftFar",
    "TacetTreasureRightFar",
    "TacetTreasureLeftNear",
    "TacetTreasureRightNear",
}


def main() -> None:
    data = json.loads(PIPE.read_text(encoding="utf-8"))
    for name in list(data):
        if name in DROP or name.startswith("TacetAimX"):
            data.pop(name, None)

    data["TacetTreasureAim"] = {
        "desc": (
            "宝箱不在中心窗：从屏幕中心滑向本次识别框。"
            "行程=图标相对中心的实际偏移，左右和上下一起调。禁止前进。"
        ),
        "recognition": "TemplateMatch",
        "roi": [16, 24, 1248, 640],
        "template": TEMPLATES,
        "threshold": 0.55,
        "action": {
            "type": "Swipe",
            "param": {
                "begin": [640, 360],
                "end": True,
                "duration": 200,
                "end_hold": 30,
            },
        },
        "post_delay": 120,
        "next": [
            "TacetClaimReward",
            "TacetClaimRewardByOCR",
            "TacetApproachTreasure",
        ],
    }

    data["TacetTreasureCentered"] = {
        "desc": "宝箱图标中心已落在屏幕中心小窗（左右、上下都进窗）才推左摇杆前进。",
        "recognition": "TemplateMatch",
        "roi": [590, 318, 100, 84],
        "template": TEMPLATES,
        "threshold": 0.55,
        "action": {
            "type": "Swipe",
            "param": {
                "begin": [220, 560],
                "end": [220, 400],
                "duration": 280,
                "end_hold": 30,
            },
        },
        "post_delay": 120,
        "next": [
            "TacetClaimReward",
            "TacetClaimRewardByOCR",
            "TacetApproachTreasure",
        ],
    }

    search = data["TacetTreasureSearch"]
    search["desc"] = "画面内没有宝箱标 → 小幅左转再找。找到后按实际偏移调视角，禁止盲目前进。"
    search["action"]["param"] = {
        "begin": [860, 360],
        "end": [560, 360],
        "duration": 220,
        "end_hold": 20,
    }
    search["next"] = [
        "TacetClaimReward",
        "TacetClaimRewardByOCR",
        "TacetTreasureCentered",
        "TacetTreasureAim",
        "TacetApproachTreasure",
    ]

    data["TacetApproachTreasure"]["desc"] = (
        "领奖导航：定位宝箱标 → 滑向它的实际位置（左右+上下，行程随偏移变）"
        "→ 图标进入屏幕中心小窗后才前进。"
    )
    data["TacetApproachTreasure"]["next"] = [
        "TacetClaimReward",
        "TacetClaimRewardByOCR",
        "TacetTreasureCentered",
        "TacetTreasureAim",
        "TacetTreasureSearch",
    ]

    PIPE.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    print("ok: aim swipe end=icon box (x and y)")


if __name__ == "__main__":
    main()
