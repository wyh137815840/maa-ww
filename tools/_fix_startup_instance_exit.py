#!/usr/bin/env python3
"""Startup: detect in-instance (top-left exit door) and leave before world-ready."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPE = ROOT / "assets/resource_adb/pipeline/Startup.json"
IMG_SRC = ROOT / "assets/resource_adb/image/Explore"
IMG_DST = ROOT / "assets/resource/image/Explore"

WORLD_NEXT = [
    "InInstanceExitIcon",
    "ConfirmLeaveInstance",
    "ExploreWorldReady",
    "ExploreHUD",
    "StartUpGameWait",
]


def main() -> None:
    data = json.loads(PIPE.read_text(encoding="utf-8"))

    data["StartupMain"]["desc"] = (
        "启动进游戏边界：冷/软拉起 → 标题/登录 → 等读条 → "
        "**若在副本（左上门图标）先退出** → 大世界确认（Terminal / 小地图）。"
        "未确认大世界前不得结束。"
    )

    data["StartUpGameWait"]["desc"] = (
        "加载期循环：副本退出 / 大世界确认 / 标题点连接 / 登录确认。"
        "上次在副本退出会回到副本——须先点左上门图标再确认离开。"
    )
    data["StartUpGameWait"]["next"] = [
        "InInstanceExitIcon",
        "ConfirmLeaveInstance",
        "ExploreWorldReady",
        "ExploreHUD",
        "TitleClickConnect",
        "StartupLoginConfirm",
    ]

    data["TitleClickConnect"]["next"] = [
        "InInstanceExitIcon",
        "ConfirmLeaveInstance",
        "ExploreWorldReady",
        "ExploreHUD",
        "StartupLoginConfirm",
        "StartUpGameWait",
    ]
    data["StartupLoginConfirm"]["next"] = list(WORLD_NEXT)

    data["InInstanceExitIcon"] = {
        "desc": (
            "副本内标志：左上角「出门」图标（门+箭头）。"
            "出现即不在大世界；点击打开「确认离开」。实截 20261101 instance_hud。"
        ),
        "recognition": "TemplateMatch",
        "roi": [0, 0, 100, 100],
        "template": "Explore/InstanceExitIcon.png",
        "threshold": 0.72,
        "action": "Click",
        "target": [32, 31],
        "post_wait_freezes": {"time": 400, "timeout": 8000, "threshold": 0.95},
        "next": [
            "ConfirmLeaveInstance",
            "InInstanceExitIcon",
            "StartUpGameWait",
        ],
    }

    data["ConfirmLeaveInstance"] = {
        "desc": (
            "离开副本弹窗右侧「确认」（左侧是「重新挑战」，禁止点左）。"
            "点确认后等读条回到大世界。"
        ),
        "recognition": "TemplateMatch",
        "roi": [640, 380, 260, 100],
        "template": "Explore/ConfirmLeaveInstance.png",
        "threshold": 0.7,
        "action": "Click",
        "target": [760, 435],
        "post_wait_freezes": {"time": 800, "timeout": 60000, "threshold": 0.95},
        "next": [
            "ExploreWorldReady",
            "ExploreHUD",
            "InInstanceExitIcon",
            "StartUpGameWait",
        ],
    }

    # OCR fallback if confirm template drifts
    data["ConfirmLeaveInstanceByOCR"] = {
        "desc": "离开弹窗「确认」OCR 兜底；ROI 偏右，避免点到「重新挑战」。",
        "recognition": "OCR",
        "roi": [640, 380, 260, 100],
        "expected": ["确认"],
        "action": "Click",
        "post_wait_freezes": {"time": 800, "timeout": 60000, "threshold": 0.95},
        "next": [
            "ExploreWorldReady",
            "ExploreHUD",
            "InInstanceExitIcon",
            "StartUpGameWait",
        ],
    }
    data["InInstanceExitIcon"]["next"] = [
        "ConfirmLeaveInstance",
        "ConfirmLeaveInstanceByOCR",
        "InInstanceExitIcon",
        "StartUpGameWait",
    ]
    data["StartUpGameWait"]["next"] = [
        "InInstanceExitIcon",
        "ConfirmLeaveInstance",
        "ConfirmLeaveInstanceByOCR",
        "ExploreWorldReady",
        "ExploreHUD",
        "TitleClickConnect",
        "StartupLoginConfirm",
    ]

    data["ExploreWorldReady"]["desc"] = (
        "大世界确认（优先）：顶栏 Terminal/OpenGuidebook。"
        "副本内也可能有类似顶栏——须先处理 InInstanceExitIcon，不得单独作为进本态成功。"
    )
    data["ExploreHUD"]["desc"] = (
        "大世界确认（次选）：左上小地图。副本内也有小地图，"
        "仅在无出门图标时作为大世界证据。"
    )

    PIPE.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")

    IMG_DST.mkdir(parents=True, exist_ok=True)
    for name in ("InstanceExitIcon.png", "ConfirmLeaveInstance.png"):
        src = IMG_SRC / name
        if src.is_file():
            shutil.copy2(src, IMG_DST / name)
            print("image", name)
    print("ok: Startup instance-exit gate")


if __name__ == "__main__":
    main()
