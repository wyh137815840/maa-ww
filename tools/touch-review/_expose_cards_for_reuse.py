#!/usr/bin/env python3
"""Copy each card screen into inbox so touch-review can browse for reuse."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from brief import write_brief
from common import load_config

cfg = load_config()
root = Path(__file__).resolve().parents[2]
cards_dir = Path(cfg["cards_dir"])
inbox = Path(cfg["inbox_dir"])

# clean previous expose previews
for old in inbox.glob("card-reuse-*.png"):
    old.unlink(missing_ok=True)
for old in inbox.glob("card-reuse-*.brief.json"):
    old.unlink(missing_ok=True)

rows = []
for d in sorted(cards_dir.iterdir(), key=lambda p: p.name):
    if not d.is_dir():
        continue
    cj = d / "card.json"
    scr = d / "screen.png"
    if not cj.is_file() or not scr.is_file():
        continue
    card = json.loads(cj.read_text(encoding="utf-8"))
    label = card.get("label") or d.name
    note = (card.get("note") or "")[:120]
    dest = inbox / f"card-reuse-{d.name}.png"
    shutil.copy2(scr, dest)
    write_brief(
        dest,
        title=f"【已导出卡】{label}",
        goal=f"供复用指认。card id=`{d.name}`。不要重新导出，除非我说要改标。",
        steps=[
            f"label 原值：{label}",
            f"click={card.get('click')} roi={card.get('roi')}",
            f"note：{note}",
            "若这张可用于多副本选行，在聊天告诉我 card id。",
        ],
        suggested_label=label,
        suggested_expected_next=str(card.get("expected_next") or ""),
        suggested_note=f"reuse-catalog; source_card={d.name}",
        do_not=["不要导出（除非明确要改）"],
    )
    # mark as skip/exported-ish so not forced pending? keep as pending yellow so visible
    rows.append((d.name, label, note))

print(f"exposed {len(rows)} cards into inbox as card-reuse-*.png")
for cid, label, note in rows:
    print(f"- {cid}  |  {label}  |  {note[:60]}")
