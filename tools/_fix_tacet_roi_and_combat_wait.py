#!/usr/bin/env python3
"""Expand TemplateMatch ROIs that are <= template size; fix InTacetCombat wait loop for manual combat."""
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "assets/resource_adb/pipeline/Tacet.json"
IMG = ROOT / "assets/resource_adb/image"
W, H = 1280, 720
PAD = 24  # expand each side


def expand_roi(roi: list[int], tw: int, th: int) -> list[int]:
    x, y, rw, rh = roi
    need_w = tw + PAD * 2
    need_h = th + PAD * 2
    cx = x + rw // 2
    cy = y + rh // 2
    nw = max(rw, need_w)
    nh = max(rh, need_h)
    nx = max(0, min(cx - nw // 2, W - nw))
    ny = max(0, min(cy - nh // 2, H - nh))
    # clamp size if near edges
    nw = min(nw, W - nx)
    nh = min(nh, H - ny)
    return [nx, ny, nw, nh]


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    fixed = []
    for name, node in data.items():
        if node.get("recognition") != "TemplateMatch":
            continue
        tpl = node.get("template")
        roi = node.get("roi")
        if not tpl or not isinstance(roi, list) or len(roi) < 4:
            continue
        path = IMG / tpl
        if not path.is_file():
            continue
        tw, th = Image.open(path).size
        if tw < roi[2] and th < roi[3]:
            continue
        new_roi = expand_roi(roi, tw, th)
        if new_roi != roi:
            node["roi"] = new_roi
            fixed.append(f"{name}: {roi} -> {new_roi} (tpl {tw}x{th})")

    # Manual combat: stay in InTacetCombat until settle UI appears; never DirectHit-exit mid-fight
    combat = data["InTacetCombat"]
    combat["desc"] = (
        "无音区内战斗中（左侧目标条）。审查卡 20261031-194638。"
        "只识别不点击；战斗由人工完成。命中后自循环等待结算 UI。"
    )
    combat["next"] = [
        "TacetChallengeComplete",
        "TacetClaimReward",
        "TacetClaimStaminaDouble",
        "TacetClaimStamina",
        "InTacetCombat",
    ]

    # Remove DirectHit stub from main entry next (would steal flow)
    main_next = data["TacetMain"]["next"]
    data["TacetMain"]["next"] = [n for n in main_next if n != "TacetNeedSettle"]
    data["TacetNeedSettle"]["enabled"] = False
    data["TacetNeedSettle"]["desc"] = (
        "占位已禁用：勿用 DirectHit 提前结束。结算走 ChallengeComplete/Claim* / Exit。"
    )

    # ChallengeComplete: after banner, wait for claim buttons (self not needed)
    data["TacetChallengeComplete"]["next"] = [
        "TacetClaimReward",
        "TacetClaimStaminaDouble",
        "TacetClaimStamina",
        "TacetStaminaExhausted",
        "TacetChallengeComplete",
    ]

    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    print("roi fixed", len(fixed))
    for line in fixed:
        print(" ", line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
