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

# Probe a few title boxes; pick the one with most dark pixels (text)
candidates = [
    (480, 270, 700, 320),
    (470, 280, 720, 330),
    (450, 260, 720, 340),
    (500, 290, 680, 335),
]
best = None
best_score = -1
for box in candidates:
    crop = img.crop(box).convert("L")
    # score: darker pixels (text on white)
    dark = sum(1 for p in crop.getdata() if p < 80)
    if dark > best_score:
        best_score = dark
        best = box

assert best is not None
out = root / "assets/resource_adb/image/Common/DisconnectTitle.png"
img.crop(best).save(out)
print("title", best, "dark_px", best_score, "->", out)

pipe_path = root / "assets/resource_adb/pipeline/CommonDisconnect.json"
pipe = json.loads(pipe_path.read_text(encoding="utf-8"))
x1, y1, x2, y2 = best
pipe["DisconnectTitle"]["roi"] = [
    max(0, x1 - 30),
    max(0, y1 - 20),
    min(1280, x2 + 30) - max(0, x1 - 30),
    min(720, y2 + 20) - max(0, y1 - 20),
]
pipe_path.write_text(json.dumps(pipe, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
