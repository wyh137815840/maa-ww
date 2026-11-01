#!/usr/bin/env python3
"""Capture + brief for Tacet settle chain (absorb / stamina / continue)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from brief import write_brief  # noqa: E402
from common import load_config  # noqa: E402


def main() -> int:
    cfg = load_config()
    label = "tacet-settle"
    # capture.py writes into inbox with timestamp
    cmd = [sys.executable, str(Path(__file__).with_name("capture.py")), "--label", label]
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=str(ROOT))

    inbox = Path(cfg["inbox_dir"])
    if not inbox.is_absolute():
        inbox = ROOT / inbox
    shots = sorted(inbox.glob(f"*-{label}.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not shots:
        raise SystemExit("no capture found")
    dest = shots[0]

    write_brief(
        dest,
        title="无音区 · 第6步：结算链（按当前画面选一种）",
        goal=(
            "清完残象后的结算相关界面。按你现在这张图只标「当前这一步」："
            "① 屏幕提示「吸收/拾取」→ label=TacetAbsorbEcho；"
            "② 体力消耗确认弹窗 → label=TacetClaimStamina；"
            "③ 底部「再次挑战/离开」类按钮 → 分别标 TacetContinue / TacetExit。"
            "若还在战斗中或登录页，先手动打到结算再截图说「截图」。"
        ),
        steps=[
            "先看画面属于上面哪一种；只标当前这一步，不要一张图标多个阶段。",
            "① 吸声骸：框住「吸收」提示或交互键 F 附近文案；点击点点在确认交互处。",
            "② 耗体力：框住确认/消耗按钮（常见「确认」黑/金按钮）；点击点按按钮中心。",
            "③ 再战/离开：若两按钮同屏，先标右侧「再次挑战」为 TacetContinue；离开另截一张标 TacetExit。",
            "导出后聊天说「已导出」+ label。若画面不对，关卡打完出结算后再说「截图」。",
        ],
        suggested_label="TacetAbsorbEcho",
        suggested_expected_next="TacetClaimStamina",
        suggested_note=(
            "对齐 ok-ww TacetTask：combat_once → walk_to_treasure → pick_f → "
            "has_claim_stamina → use_stamina → continue/exit。"
        ),
        do_not=[
            "不要标技能键/血条",
            "不要在登录弹窗上硬标结算",
            "断线「确认」另议，本卡不标",
        ],
    )
    print(dest)
    print(f"brief -> {dest.with_suffix('.brief.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
