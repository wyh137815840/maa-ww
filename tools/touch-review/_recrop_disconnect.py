#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import json

root = Path(__file__).resolve().parents[2]
src = Path(
    r"C:\Users\Administrator\.cursor\projects\d-git-maa-ww\assets\image-4a617d08-668d-49de-845f-6055dae5a971.png"
)
img = Image.open(src).convert("RGB")
if img.size != (1280, 720):
    img = img.resize((1280, 720), Image.Resampling.LANCZOS)

# From the dialog layout in user shot (centered white modal):
# Title top-left of modal ~ (490, 255)-(700, 295)
# Confirm black button bottom-right ~ (720, 430)-(880, 485)
title_box = (500, 255, 680, 300)
btn_box = (720, 430, 880, 485)
click = [800, 458]

out_dir = root / "assets/resource_adb/image/Common"
out_dir.mkdir(parents=True, exist_ok=True)
img.crop(title_box).save(out_dir / "DisconnectTitle.png")
img.crop(btn_box).save(out_dir / "DisconnectConfirm.png")
print("title", title_box)
print("btn", btn_box, "click", click)

# also save annotated preview for sanity
prev = img.copy()
prev.save(root / "review/inbox/20261031-disconnect-confirm.png")

pipe_path = root / "assets/resource_adb/pipeline/CommonDisconnect.json"
roi = [btn_box[0] - 20, btn_box[1] - 20, (btn_box[2] - btn_box[0]) + 40, (btn_box[3] - btn_box[1]) + 40]
roi[0] = max(0, roi[0])
roi[1] = max(0, roi[1])
roi[2] = min(1280 - roi[0], roi[2])
roi[3] = min(720 - roi[1], roi[3])
pipe = {
    "DisconnectConfirm": {
        "desc": "「连接已断开」弹窗「确认」。点后需重登；根因多为 PC 启动器/模拟器机型，本节点仅清弹窗。",
        "recognition": "TemplateMatch",
        "roi": roi,
        "template": "Common/DisconnectConfirm.png",
        "threshold": 0.75,
        "action": "Click",
        "target": click,
        "post_wait_freezes": {"time": 300, "target": 0.95, "timeout": 5000},
        "next": [],
    },
    "DisconnectTitle": {
        "desc": "「连接已断开」标题（仅识别）。",
        "recognition": "TemplateMatch",
        "roi": [title_box[0] - 30, title_box[1] - 20, (title_box[2] - title_box[0]) + 60, (title_box[3] - title_box[1]) + 40],
        "template": "Common/DisconnectTitle.png",
        "threshold": 0.7,
        "action": "DoNothing",
        "next": ["DisconnectConfirm"],
    },
}
pipe_path.write_text(json.dumps(pipe, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
print("rewrote", pipe_path)
