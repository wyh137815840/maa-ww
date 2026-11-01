#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PIL import Image

from brief import write_brief
from common import load_config

cfg = load_config()
inbox = Path(cfg["inbox_dir"])
src = inbox / "20261031-192600-guidebook-tacet-user.png"
# also accept the assets copy name if needed
if not src.is_file():
    raise SystemExit(f"missing {src}")

im = Image.open(src).convert("RGB")
tw, th = cfg["target_size"]
if im.size != (tw, th):
    im = im.resize((tw, th), Image.Resampling.LANCZOS)
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
dest = inbox / f"{stamp}-guidebook-tacet-tab.png"
im.save(dest, format="PNG")

write_brief(
    dest,
    title="无音区 · 第2步：导能手册「无音清剿」页签",
    goal="在左侧分类栏标出「无音清剿」入口（当前画面多半已选中）。导出后用于 GuidebookTacetTab。",
    steps=[
        "确认是「素材获取」手册，左侧有模拟领域/凝素/讨伐/战歌/无音清剿/残象聚落。",
        "框住左侧「无音清剿」这一整行图标+文字作为 ROI（尽量紧，不要框到右边列表）。",
        "再点「无音清剿」文字/图标中心作为点击点。",
        "导出审查卡后聊天说「已导出」。",
        "下一张再标列表里某个无音区的「前往」。",
    ],
    suggested_label="GuidebookTacetTab",
    suggested_expected_next="TacetList or TacetGoButton",
    suggested_note="画面来自 Windows 截图（ADB screencap 在安卓15+鸣潮上会截到桌面层）。右侧已是无音区列表可作对照。",
    do_not=[
        "不要点右侧「前往」。",
        "不要点顶部体力/货币。",
        "不要点左上角返回，除非任务要求。",
    ],
)
print(dest)
print("size", im.size)
