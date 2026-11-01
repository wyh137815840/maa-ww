#!/usr/bin/env python3
"""Fix Tacet: wait combat end before approach; distinguish 60/120 claim by red digits."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPE = ROOT / "assets/resource_adb/pipeline/Tacet.json"

# HSV ColorMatch (method 40): coral/red cost digits when stamina insufficient.
RED_RANGES_LOWER = [[0, 40, 100], [155, 40, 100]]
RED_RANGES_UPPER = [[25, 255, 255], [180, 255, 255]]
ROI_120_DIGITS = [742, 428, 45, 30]  # "120" on double button
ROI_60_DIGITS = [345, 428, 40, 30]  # "60" on single button


def main() -> None:
    data = json.loads(PIPE.read_text(encoding="utf-8"))

    # --- 1) Combat must not jump to DirectHit ApproachTreasure ---
    data["TacetMain"]["desc"] = (
        "无音区：手册→选行→开启挑战→**等战斗/挑战达成**→走到宝藏→领取→按体力白/红字选 60/120→结算/退出。"
        "ApproachTreasure 是 DirectHit，禁止出现在 Main/战斗 next。"
    )
    data["TacetMain"]["next"] = [
        "OpenGuidebook",
        "SolaGuidebookTile",
        "GuidebookTacetTab",
        "SelectTacetRow",
        "TacetStartChallenge",
        "InTacetCombat",
        "TacetChallengeComplete",
        "TacetClaimReward",
        "TacetClaimStaminaDoubleBlocked",
        "TacetClaimStaminaDouble",
        "TacetClaimStamina",
        "TacetStaminaExhausted",
        "TacetExit",
        "TacetListSwipeUp",
        "TacetNeedMoreRows",
    ]

    data["TacetStartChallenge"]["next"] = [
        "InTacetCombat",
        "TacetChallengeComplete",
    ]

    data["InTacetCombat"]["desc"] = (
        "无音区内战斗中（左侧目标条）。只识别不点击；人工/自动战斗均可。"
        "next 仅挑战达成 + 自环——禁止挂 ApproachTreasure（DirectHit 会立刻跳走）。"
    )
    data["InTacetCombat"]["next"] = [
        "TacetChallengeComplete",
        "InTacetCombat",
    ]
    data["InTacetCombat"]["timeout"] = 600000

    data["TacetChallengeComplete"]["desc"] = (
        "战斗结束全屏「挑战达成」。纯识别；命中后才进入走近宝藏。"
        "勿在战斗 next 里挂 Approach。"
    )
    data["TacetChallengeComplete"]["next"] = [
        "TacetApproachTreasure",
        "TacetClaimReward",
        "TacetClaimRewardByOCR",
        "TacetChallengeComplete",
    ]
    data["TacetChallengeComplete"]["timeout"] = 120000

    if "TacetContinue" in data:
        data["TacetContinue"]["next"] = [
            "InTacetCombat",
            "TacetChallengeComplete",
            "TacetExit",
        ]

    # --- 2) Stamina claim: red "120" → single; white "120" → double ---
    claim_after = [
        "TacetStaminaExhausted",
        "TacetClaimStaminaDoubleBlocked",
        "TacetClaimStaminaDouble",
        "TacetClaimStamina",
        "TacetContinue",
        "TacetExit",
    ]
    data["TacetClaimReward"]["next"] = list(claim_after)
    if "TacetClaimRewardByOCR" in data:
        data["TacetClaimRewardByOCR"]["next"] = list(claim_after)

    data["TacetClaimStaminaDoubleBlocked"] = {
        "desc": (
            "领取弹窗右侧「120」为红字=双倍不可用（体力不足 120）。"
            "ColorMatch 红字命中后改走单倍/耗尽；勿点双倍。"
        ),
        "recognition": "ColorMatch",
        "roi": ROI_120_DIGITS,
        "method": 40,
        "lower": RED_RANGES_LOWER,
        "upper": RED_RANGES_UPPER,
        "count": 40,
        "action": "DoNothing",
        "next": [
            "TacetClaimStamina",
            "TacetStaminaExhausted",
            "TacetContinue",
            "TacetExit",
        ],
        "timeout": 8000,
    }

    data["TacetClaimStaminaDouble"]["desc"] = (
        "右侧「120|双倍领取」且 120 非红（Blocked 未命中）。"
        "仅在体力足够双倍时点击；否则应由 DoubleBlocked→单倍。"
    )
    data["TacetClaimStaminaDouble"]["threshold"] = 0.85
    data["TacetClaimStaminaDouble"]["method"] = 10001
    data["TacetClaimStaminaDouble"]["next"] = [
        "TacetContinue",
        "TacetExit",
    ]

    data["TacetClaimStamina"]["desc"] = (
        "左侧「60|单倍领取」。双倍红字不可用或策略回退时点；"
        "60 亦红则走 StaminaExhausted。"
    )
    data["TacetClaimStamina"]["threshold"] = 0.85
    data["TacetClaimStamina"]["method"] = 10001
    # If 60 is also red, prefer exhausted over clicking dead button.
    data["TacetClaimStamina"]["next"] = [
        "TacetContinue",
        "TacetExit",
    ]

    # Gate single click: if 60 digits red, don't click single — close as exhausted.
    data["TacetClaimStaminaBlocked"] = {
        "desc": "左侧「60」红字=单倍也不可用。转关闭弹窗。",
        "recognition": "ColorMatch",
        "roi": ROI_60_DIGITS,
        "method": 40,
        "lower": RED_RANGES_LOWER,
        "upper": RED_RANGES_UPPER,
        "count": 40,
        "action": "DoNothing",
        "next": [
            "TacetStaminaExhausted",
            "TacetExit",
        ],
        "timeout": 5000,
    }

    # When DoubleBlocked fires, check 60-red before clicking single.
    data["TacetClaimStaminaDoubleBlocked"]["next"] = [
        "TacetClaimStaminaBlocked",
        "TacetClaimStamina",
        "TacetStaminaExhausted",
        "TacetContinue",
        "TacetExit",
    ]

    # Also insert 60-red gate into ClaimReward next before single.
    data["TacetClaimReward"]["next"] = [
        "TacetStaminaExhausted",
        "TacetClaimStaminaDoubleBlocked",
        "TacetClaimStaminaDouble",
        "TacetClaimStaminaBlocked",
        "TacetClaimStamina",
        "TacetContinue",
        "TacetExit",
    ]
    data["TacetClaimRewardByOCR"]["next"] = list(data["TacetClaimReward"]["next"])

    PIPE.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    print("ok: combat wait + stamina 60/120 red-digit gate")


if __name__ == "__main__":
    main()
