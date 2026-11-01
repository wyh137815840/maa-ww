#!/usr/bin/env python3
"""Import user disconnect dialog shot → Common DisconnectConfirm (Click 确认)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image

root = Path(__file__).resolve().parents[2]
src = Path(
    r"C:\Users\Administrator\.cursor\projects\d-git-maa-ww\assets\image-4a617d08-668d-49de-845f-6055dae5a971.png"
)
if not src.is_file():
    raise SystemExit(f"missing {src}")

# Normalize to 1280x720 if needed
img = Image.open(src).convert("RGB")
if img.size != (1280, 720):
    img = img.resize((1280, 720), Image.Resampling.LANCZOS)

inbox = root / "review/inbox"
inbox.mkdir(parents=True, exist_ok=True)
screen_path = inbox / "20261031-disconnect-confirm.png"
img.save(screen_path)

# Confirm button is bottom-right of white dialog (approx from 1280x720 dialog)
# Dialog ~ centered; black 确认 button roughly [700, 420, 160, 55] area — refine from image.
# User shot: button bottom-right of modal. Typical WW dialog confirm ~ (760, 430)-(900, 480)
cx, cy = 790, 455
w, h = 140, 48
x1, y1 = max(0, cx - w // 2), max(0, cy - h // 2)
x2, y2 = min(1280, x1 + w), min(720, y1 + h)
# Also crop title「连接已断开」for recognition alternative
tx1, ty1, tw, th = 470, 250, 200, 40

img_dir = root / "assets/resource_adb/image/Common"
img_dir.mkdir(parents=True, exist_ok=True)
btn = img.crop((x1, y1, x2, y2))
btn_path = img_dir / "DisconnectConfirm.png"
btn.save(btn_path)
title = img.crop((tx1, ty1, tx1 + tw, ty1 + th))
title_path = img_dir / "DisconnectTitle.png"
title.save(title_path)
print("btn", btn_path, [x1, y1, x2 - x1, y2 - y1], "click", [cx, cy])
print("title", title_path)

pipe_path = root / "assets/resource_adb/pipeline/CommonDisconnect.json"
pipe = {
    "DisconnectConfirm": {
        "desc": "「连接已断开」弹窗右下「确认」。点后需重新登录；根因在模拟器/启动器环境，本节点仅恢复流程。",
        "recognition": "TemplateMatch",
        "roi": [x1 - 40, y1 - 40, (x2 - x1) + 80, (y2 - y1) + 80],
        "template": "Common/DisconnectConfirm.png",
        "threshold": 0.75,
        "action": "Click",
        "target": [cx, cy],
        "post_wait_freezes": {"time": 300, "target": 0.95, "timeout": 5000},
        "next": [],
    }
}
# clamp roi
r = pipe["DisconnectConfirm"]["roi"]
r[0] = max(0, r[0])
r[1] = max(0, r[1])
r[2] = min(1280 - r[0], r[2])
r[3] = min(720 - r[1], r[3])
pipe_path.write_text(json.dumps(pipe, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
print("wired", pipe_path)

# Also copy screen into cards-ish for review
card = root / "review/cards/manual-disconnect-confirm"
card.mkdir(parents=True, exist_ok=True)
shutil.copy2(screen_path, card / "screen.png")
btn.save(card / "template.png")
(card / "card.json").write_text(
    json.dumps(
        {
            "id": "manual-disconnect-confirm",
            "label": "DisconnectConfirm",
            "note": "from user shot; Click 确认 only — root cause is env",
            "click": [cx, cy],
            "roi": [x1, y1, x2 - x1, y2 - y1],
        },
        ensure_ascii=False,
        indent=4,
    )
    + "\n",
    encoding="utf-8",
)
