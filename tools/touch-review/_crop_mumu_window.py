#!/usr/bin/env python3
"""Crop MuMu window chrome from a Windows screenshot, normalize to 1280x720."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from brief import write_brief
from common import load_config

src = Path(__file__).resolve().parents[2] / "review/inbox/20261031-192600-guidebook-tacet-user.png"
im = Image.open(src).convert("RGB")
w, h = im.size
print("raw", w, h)

# Heuristic: MuMu title bar is a dark strip at top; find first row that is not near-title-bar gray/black chrome.
# Sample left-middle column for a bright-ish content transition.
px = im.load()


def row_mean_y(y: int) -> float:
    s = 0
    for x in range(0, w, max(1, w // 40)):
        r, g, b = px[x, y]
        s += r + g + b
    return s / (3 * (len(range(0, w, max(1, w // 40)))))


# title bar usually ~32-48px on high DPI; scan first 12% height
limit = max(20, h // 8)
top = 0
for y in range(limit):
    m = row_mean_y(y)
    # game UI is brighter/more colorful than dark chrome
    if m > 55:
        top = y
        break

# side borders often 0-2px; bottom status rare. Keep full width minus tiny margin if needed.
left, right, bottom = 0, w, h
# If right edge is pure black border
for x in range(w - 1, w - 8, -1):
    r, g, b = px[x, h // 2]
    if r + g + b > 30:
        right = x + 1
        break

crop = im.crop((left, top, right, bottom))
print("crop_box", (left, top, right, bottom), "crop_size", crop.size)

cfg = load_config()
tw, th = cfg["target_size"]
out = crop.resize((tw, th), Image.Resampling.LANCZOS)
dest = Path(__file__).resolve().parents[2] / "review/inbox/20261031-192700-guidebook-tacet-tab.png"
out.save(dest)
print("saved", dest, out.size)

write_brief(
    dest,
    title="无音区 · 第2步：导能手册「无音清剿」页签",
    goal="在左侧分类栏标出「无音清剿」。导出 GuidebookTacetTab。",
    steps=[
        "左侧找到「无音清剿」（当前多半已高亮选中）。",
        "框住该行图标+文字为 ROI（不要框到右侧列表）。",
        "点该行中心为点击点。",
        "导出后说「已导出」；下一张标某个「前往」。",
    ],
    suggested_label="GuidebookTacetTab",
    suggested_expected_next="TacetGoButton",
    suggested_note="来源：你提供的窗口截图，已裁掉 MuMu 标题栏并缩到 1280x720。ADB screencap 在安卓15鸣潮上会截到桌面，暂用手动截图。",
    do_not=["不要点右侧前往", "不要点返回/体力"],
)
print("brief ok")
