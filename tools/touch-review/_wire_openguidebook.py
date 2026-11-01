#!/usr/bin/env python3
"""Crop a tight OpenGuidebook template from the review card click point."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[2]
card_dir = root / "review/cards/20261031-182324-openguidebook"
card = json.loads((card_dir / "card.json").read_text(encoding="utf-8"))
cx, cy = card["click"]
# Tight crop around guidebook icon (~56x56), keep inside 1280x720
half_w, half_h = 28, 28
x1 = max(0, cx - half_w)
y1 = max(0, cy - half_h)
x2 = min(1280, cx + half_w)
y2 = min(720, cy + half_h)
roi = [x1, y1, x2 - x1, y2 - y1]

screen = Image.open(card_dir / "screen.png").convert("RGB")
tmpl = screen.crop((x1, y1, x2, y2))
out_dir = root / "assets/resource_adb/image/Guidebook"
out_dir.mkdir(parents=True, exist_ok=True)
tmpl_path = out_dir / "OpenGuidebook.png"
tmpl.save(tmpl_path)

# Also save a debug preview in the card folder
prev = screen.copy()
draw = ImageDraw.Draw(prev)
draw.rectangle([x1, y1, x2 - 1, y2 - 1], outline=(0, 255, 0), width=2)
draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(255, 0, 0))
prev.save(card_dir / "tight_preview.png")

meta = {"click": [cx, cy], "roi": roi, "template": "Guidebook/OpenGuidebook.png"}
print(json.dumps(meta, ensure_ascii=False))
