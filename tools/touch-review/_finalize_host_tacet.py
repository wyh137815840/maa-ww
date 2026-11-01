#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
from brief import write_brief
from common import load_config

src = Path(r"D:\git\maa-ww\review\inbox\20261031-193021-after-tacet-tab-host.png")
im = Image.open(src).convert("RGB")
w, h = im.size
# MuMu client often includes ~48-70px in-window toolbar under OS chrome already excluded by PrintWindow client
# Probe: find first row with substantial non-dark UI after dark toolbar
px = im.load()
top = 0
for y in range(min(120, h // 5)):
    # sample across middle band
    bright = 0
    n = 0
    for x in range(w // 4, 3 * w // 4, 8):
        r, g, b = px[x, y]
        if r + g + b > 90:
            bright += 1
        n += 1
    if n and bright / n > 0.15 and y > 20:
        top = y
        break
# fallback fixed crop if heuristic weak
if top < 28:
    top = 52
crop = im.crop((0, top, w, h))
print("raw", w, h, "top", top, "crop", crop.size)
tw, th = load_config()["target_size"]
out = crop.resize((tw, th), Image.Resampling.LANCZOS)
dest = Path(r"D:\git\maa-ww\review\inbox\20261031-193040-tacet-go-live.png")
out.save(dest)
write_brief(
    dest,
    title="无音区 · 第3步：列表前往/挑战（实机点击后）",
    goal="在你点过「无音清剿」后的真实列表上，标第一条右侧操作按钮（「前往」或「直接挑战」，以画面为准）。",
    steps=[
        "确认右侧已是无音区列表（沉心域/炽心域等）。",
        "只框第一条右侧按钮为 ROI。",
        "点按钮中心。",
        "导出后说「已导出」。",
    ],
    suggested_label="TacetGoButton",
    suggested_expected_next="TacetTravelConfirm or ChallengeConfirm",
    suggested_note="宿主 PrintWindow 截取 MuMu安卓设备-1，已裁顶栏。勿用旧复用图。",
    do_not=["不要用 inbox 里作废的旧 tacet-go-button", "不要点左侧其它页签"],
)
print(dest)
