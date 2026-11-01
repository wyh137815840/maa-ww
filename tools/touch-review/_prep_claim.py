#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from brief import write_brief
from common import load_config

cfg = load_config()
subprocess.check_call(
    [sys.executable, str(Path(__file__).with_name("capture.py")), "--label", "tacet-claim"],
    cwd=str(ROOT),
)
inbox = Path(cfg["inbox_dir"])
if not inbox.is_absolute():
    inbox = ROOT / inbox
dest = sorted(inbox.glob("*-tacet-claim.png"), key=lambda p: p.stat().st_mtime, reverse=True)[0]
write_brief(
    dest,
    title="无音区 · 领奖 / 耗体力",
    goal="当前在领取奖励位置。标主确认按钮（确认/领取/消耗体力）。跳过短暂的「挑战达成」。",
    steps=[
        "框住主确认/领取/消耗按钮为 ROI（尽量只含按钮）。",
        "点击点点在按钮中心。",
        "label 用 TacetClaimStamina；若其实是「吸收」提示则改 TacetAbsorbEcho。",
        "同屏若还有离开/再次挑战，本张只标领奖确认。导出后说「已导出」。",
    ],
    suggested_label="TacetClaimStamina",
    suggested_expected_next="TacetContinue",
    suggested_note="用户指定：挑战达成太短先不做；先标领奖界面。",
    do_not=["不要标挑战达成大字", "不要标技能键", "不要先标离开"],
)
print(dest)
