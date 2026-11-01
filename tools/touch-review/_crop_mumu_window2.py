#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
from brief import write_brief
from common import load_config

src = Path(r"D:\git\maa-ww\review\inbox\20261031-192600-guidebook-tacet-user.png")
im = Image.open(src).convert("RGB")
w, h = im.size
# MuMu window chrome: top title ~36px at this capture scale; no side border in this shot
top = 36
crop = im.crop((0, top, w, h))
print("raw", w, h, "after", crop.size, "aspect", crop.size[0] / crop.size[1])
tw, th = load_config()["target_size"]
out = crop.resize((tw, th), Image.Resampling.LANCZOS)
dest = Path(r"D:\git\maa-ww\review\inbox\20261031-192720-guidebook-tacet-tab.png")
out.save(dest)
write_brief(
    dest,
    title="无音区 · 第2步：导能手册「无音清剿」页签",
    goal="在左侧分类栏标出「无音清剿」。导出 GuidebookTacetTab。",
    steps=[
        "左侧找到「无音清剿」（当前多半已高亮）。",
        "框住该行图标+文字为 ROI（不要框右侧列表）。",
        "点该行中心为点击点。",
        "导出后说「已导出」。",
    ],
    suggested_label="GuidebookTacetTab",
    suggested_expected_next="TacetGoButton",
    suggested_note="Windows 窗口截图已裁标题栏并缩到 1280x720。ADB screencap 暂不可用（截到桌面）。",
    do_not=["不要点右侧前往", "不要点返回/体力"],
)
print(dest)
