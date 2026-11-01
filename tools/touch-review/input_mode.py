#!/usr/bin/env python3
"""Enter 鸣潮 controller mode once, then stay there.

After the game world is up (not the login screen), press A on the Odin
Xbox device. The game asks 「是否切换至控制器模式」; confirm the right button.
Controller mode still accepts screen taps, so existing Pipeline clicks keep working.
Do not switch back to touch: a screen tap does not raise that prompt.

``adb shell input gamepad keyevent`` does not raise the dialog.
The press has to be written to the ``Xbox Wireless Controller`` evdev node.
"""
from __future__ import annotations

import argparse
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import Image

from common import load_config
from device_geom import BASE_H, BASE_W, adb_run, raw_screen_size, tap720

# BTN_SOUTH / Xbox A. Measured on Odin event node "Xbox Wireless Controller".
_BTN_A = 304
# 1280×720 centers of the mode dialog buttons. From 2026-11-01 in-world capture.
CONFIRM_XY = (787, 453)
DISMISS_XY = (486, 453)
_DIALOG_BOX = (360, 160, 920, 520)
_DIALOG_MEAN = 150.0


def gamepad_event_node(adb: str, serial: str) -> str:
    """Return /dev/input/eventN for the Odin Xbox pad."""
    listing = adb_run(adb, serial, "shell", "getevent", "-lp", check=False).stdout or ""
    node = ""
    for line in listing.splitlines():
        if line.startswith("add device"):
            node = line.split()[-1]
        elif "Xbox Wireless Controller" in line and node:
            return node
    raise RuntimeError("Xbox Wireless Controller not found in getevent -lp")


def press_gamepad_a(adb: str, serial: str, hold_ms: int = 120) -> str:
    """Press A on the Odin gamepad device. Returns the event node used."""
    node = gamepad_event_node(adb, serial)
    hold = max(hold_ms, 1) / 1000
    script = (
        f"sendevent {node} 1 {_BTN_A} 1; "
        f"sendevent {node} 0 0 0; "
        f"sleep {hold:.3f}; "
        f"sendevent {node} 1 {_BTN_A} 0; "
        f"sendevent {node} 0 0 0"
    )
    adb_run(adb, serial, "shell", script, check=False)
    return node


def grab_frame(adb: str, serial: str) -> Image.Image:
    remote = "/sdcard/maaww_input_mode.png"
    adb_run(adb, serial, "shell", "screencap", "-p", remote, check=False)
    with tempfile.TemporaryDirectory() as tmp:
        local = Path(tmp) / "frame.png"
        subprocess.run(
            [adb, "-s", serial, "pull", remote, str(local)],
            check=False,
            capture_output=True,
        )
        im = Image.open(local).convert("RGB")
        if im.size != (BASE_W, BASE_H):
            im = im.resize((BASE_W, BASE_H), Image.Resampling.LANCZOS)
        return im


def mode_dialog_open(frame: Image.Image) -> bool:
    """True when the white 「操作模式切换」 card covers the screen center."""
    crop = frame.crop(_DIALOG_BOX)
    pixels = list(crop.getdata())
    if not pixels:
        return False
    mean = sum(sum(px) for px in pixels) / len(pixels) / 3
    return mean >= _DIALOG_MEAN


def wait_mode_dialog(adb: str, serial: str, timeout: float = 3.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if mode_dialog_open(grab_frame(adb, serial)):
            return True
        time.sleep(0.25)
    return False


def answer_mode_dialog(adb: str, serial: str, confirm: bool = True) -> tuple[int, int]:
    """Tap 确认 or 暂不. Coordinates are 1280×720, mapped onto the device."""
    dw, dh = raw_screen_size(adb, serial)
    xy = CONFIRM_XY if confirm else DISMISS_XY
    return tap720(adb, serial, xy[0], xy[1], dw, dh)


def switch_to_controller(adb: str, serial: str, confirm: bool = True, timeout: float = 3.0) -> bool:
    """Touch mode → press A → confirm the controller-mode prompt.

    Login / title screens ignore the pad; call this only after the game world is up.
    """
    press_gamepad_a(adb, serial)
    if not wait_mode_dialog(adb, serial, timeout=timeout):
        return False
    if confirm:
        time.sleep(0.2)
        answer_mode_dialog(adb, serial, confirm=True)
        time.sleep(0.6)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Enter 鸣潮 controller mode and stay there")
    parser.add_argument("--dismiss", action="store_true", help="press 暂不 instead of 确认")
    args = parser.parse_args()
    cfg = load_config()
    ok = switch_to_controller(cfg["adb_path"], cfg["serial"], confirm=not args.dismiss)
    print("ok" if ok else "dialog not found")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
