#!/usr/bin/env python3
"""Capture or reuse tacet list for multi-row Go button annotation."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from brief import write_brief
from common import load_config

cfg = load_config()
inbox = Path(cfg["inbox_dir"])
if not inbox.is_absolute():
    inbox = ROOT / inbox

# Prefer a fresh capture; fall back to known good list shot
try:
    subprocess.check_call(
        [sys.executable, str(Path(__file__).with_name("capture.py")), "--label", "tacet-rows"],
        cwd=str(ROOT),
    )
    dest = sorted(inbox.glob("*-tacet-rows.png"), key=lambda p: p.stat().st_mtime, reverse=True)[0]
except Exception as exc:
    print("capture failed, reuse list shot:", exc)
    src = inbox / "20261031-194016-tacet-list-live.png"
    if not src.is_file():
        # may be gitignored from disk still present
        card = ROOT / "review/cards/20261031-194119-tacetgobutton/screen.png"
        dest = inbox / "20261031-tacet-rows-fallback.png"
        shutil.copy2(card, dest)
    else:
        dest = inbox / "20261031-tacet-rows-reuse.png"
        shutil.copy2(src, dest)

write_brief(
    dest,
    title="无音区 · 多副本选行：第1行「直接挑战」",
    goal=(
        "列表可见多行「直接挑战」。先只标第1行（最上一条副本，约「沉心域无音区」右侧按钮）。"
        "序号从1起，对齐 ok-ww Which Tacet Suppression。"
    ),
    steps=[
        "框住第1行右侧「直接挑战」按钮为 ROI（不要框到第2行）。",
        "点击点点在该按钮中心。",
        "label=TacetGoIndex1。导出后说「已导出」。",
        "接着会依次标 Index2/3/4；更后面的需滚动，另做。",
    ],
    suggested_label="TacetGoIndex1",
    suggested_expected_next="TacetStartChallenge",
    suggested_note=(
        "多副本选行第1步。ok-ww structure=[4,5,5,7] 分区；首屏约4行可直接点。"
        "现有 TacetGoButton 无区分行，将改为按配置序号走 IndexN。"
    ),
    do_not=["不要标第2行及以下", "不要标左侧页签", "不要标合鸣筛选"],
)
print(dest)
