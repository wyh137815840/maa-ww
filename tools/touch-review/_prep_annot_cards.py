#!/usr/bin/env python3
"""Unlock Odin, snap world HUD, open Terminal, snap menu — prep touch-review briefs."""
from __future__ import annotations
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
import _local_cfg

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from brief import write_brief  # noqa: E402
from capture import capture_png, ensure_device  # noqa: E402
from common import load_config  # noqa: E402
from device_geom import raw_screen_size, tap720  # noqa: E402


def adb(cfg, *args: str) -> None:
    subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], *args],
        check=False,
        capture_output=True,
    )


def unlock(cfg) -> None:
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_WAKEUP")
    time.sleep(0.4)
    adb(cfg, "shell", "input", "keyevent", "82")
    time.sleep(0.3)
    adb(cfg, "shell", "input", "text", _local_cfg.pin())
    time.sleep(0.2)
    adb(cfg, "shell", "input", "keyevent", "KEYCODE_ENTER")
    time.sleep(0.8)


def focus(cfg) -> str:
    r = subprocess.run(
        [cfg["adb_path"], "-s", cfg["serial"], "shell", "dumpsys", "window"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    for ln in r.stdout.splitlines():
        if "mCurrentFocus" in ln or "mFocusedApp" in ln:
            print(ln.strip())
            return ln
    return ""


def snap(cfg, label: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = cfg["inbox_dir"] / f"{stamp}-{label}.png"
    tag = capture_png(cfg["adb_path"], cfg["serial"], dest, cfg)
    print(f"captured {dest.name} ({tag})")
    return dest


def main() -> int:
    cfg = load_config()
    ensure_device(cfg["adb_path"], cfg["serial"])
    unlock(cfg)
    focus(cfg)

    world = snap(cfg, "annot-world-hud")
    write_brief(
        world,
        title="① 大世界 → Terminal 入口",
        goal="标出打开 Terminal（索拉/指南入口）的正确点击点，并框住可识别 ROI。",
        steps=[
            "框住右上角 Terminal 星标（或你认为应点的入口图标）ROI。",
            "在图标中心点一次点击点。",
            "导出审查卡；label 用 OpenGuidebook。",
        ],
        suggested_label="OpenGuidebook",
        suggested_expected_next="SolaGuidebookTile",
        suggested_note="勿点最右侧三条杠/系统菜单。坐标基准 1280×720。",
        do_not=["点最右三条杠", "点小地图", "点任务追踪"],
    )

    dw, dh = raw_screen_size(cfg["adb_path"], cfg["serial"])
    print(f"device {dw}x{dh}")
    # Best-effort open Terminal with current calib; user will correct if wrong.
    tap720(cfg["adb_path"], cfg["serial"], 1198, 38, dw, dh)
    time.sleep(1.2)
    menu = snap(cfg, "annot-terminal-menu")
    write_brief(
        menu,
        title="② Terminal 菜单 → 索拉指南",
        goal="若已是 Terminal 磁贴页：标「索拉指南」磁贴；若不是，先说明画面是什么，再标正确入口。",
        steps=[
            "确认画面是否为 Terminal 主菜单（多磁贴）。若不是请在 note 写明当前界面名。",
            "框住「索拉指南」整块磁贴 ROI。",
            "在磁贴中心点一次点击点。",
            "导出审查卡；label 用 SolaGuidebookTile。",
        ],
        suggested_label="SolaGuidebookTile",
        suggested_expected_next="GuidebookTacetTab",
        suggested_note="禁止点「活跃行迹 / 周度游历」。坐标基准 1280×720。",
        do_not=["活跃行迹", "周度游历", "点 OCR 漂移框"],
    )

    print("briefs ready:")
    print(" ", world.name)
    print(" ", menu.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
