#!/usr/bin/env python3
"""Always-on MuMu snap service: Ctrl+Alt+Space → inbox *-snap.png (game display).

Uses a fast single-display ADB path (no multi-display scoring) so short-lived
UI like「挑战达成」is more likely to be caught.
"""

from __future__ import annotations

import ctypes
import subprocess
import sys
import threading
import time
import winsound
from ctypes import wintypes
from datetime import datetime
from pathlib import Path

from PIL import Image

from capture import ensure_device, pick_display_id, run, run_text
from common import load_config

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000
VK_SPACE = 0x20
WM_HOTKEY = 0x0312
HOTKEY_ID = 0x4D414153  # 'MAAS'

user32 = ctypes.windll.user32


class Snapper:
    def __init__(self) -> None:
        self.cfg = load_config()
        self.adb = str(Path(self.cfg["adb_path"]))
        self.serial = str(self.cfg["serial"])
        self.display_id: str | None = None
        self._busy = threading.Lock()
        self._last_ok = 0.0

    def warm(self) -> None:
        ensure_device(self.adb, self.serial)
        self.display_id = pick_display_id(self.adb, self.serial, self.cfg)
        print(f"[snap] device={self.serial} display_id={self.display_id}", flush=True)

    def refresh_display(self) -> None:
        try:
            self.display_id = pick_display_id(self.adb, self.serial, self.cfg)
        except Exception as exc:
            print(f"[snap] refresh display failed: {exc}", flush=True)

    def capture_fast(self, dest: Path) -> str:
        """One-shot screencap of preferred display → dest. Prefer exec-out."""
        if not self.display_id:
            self.refresh_display()
        did = self.display_id
        tw, th = self.cfg["target_size"]

        # Fast path: stream PNG over exec-out (single round-trip).
        cmds: list[list[str]] = []
        if did:
            cmds.append([self.adb, "-s", self.serial, "exec-out", "screencap", "-d", did, "-p"])
        cmds.append([self.adb, "-s", self.serial, "exec-out", "screencap", "-p"])

        last_err = ""
        for cmd in cmds:
            try:
                r = subprocess.run(cmd, check=False, capture_output=True, timeout=8)
            except subprocess.TimeoutExpired:
                last_err = "timeout"
                continue
            data = r.stdout or b""
            if r.returncode != 0 or len(data) < 1000:
                last_err = (r.stderr or b"").decode("utf-8", "ignore")[:200]
                continue
            # Some adb builds prefix junk; find PNG signature.
            sig = data.find(b"\x89PNG")
            if sig < 0:
                last_err = "no png signature"
                continue
            if sig > 0:
                data = data[sig:]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            try:
                img = Image.open(dest).convert("RGB")
            except Exception as exc:
                last_err = f"bad png: {exc}"
                continue
            if img.size != (tw, th):
                img = img.resize((tw, th), Image.Resampling.LANCZOS)
                img.save(dest, format="PNG")
            tag = f"exec-out:{did or 'default'}"
            return tag

        # Fallback: shell file + pull (same as capture.py preferred display only)
        if did:
            remote = "/data/local/tmp/maa_ww_snap_fast.png"
            run([self.adb, "-s", self.serial, "shell", "rm", "-f", remote], check=False)
            r = run(
                [self.adb, "-s", self.serial, "shell", "screencap", "-d", did, "-p", remote],
                check=False,
            )
            if r.returncode == 0:
                run([self.adb, "-s", self.serial, "pull", remote, str(dest)], check=False)
                if dest.is_file() and dest.stat().st_size > 1000:
                    img = Image.open(dest).convert("RGB")
                    if img.size != (tw, th):
                        img = img.resize((tw, th), Image.Resampling.LANCZOS)
                        img.save(dest, format="PNG")
                    return f"pull:{did}"

        raise RuntimeError(f"fast capture failed ({last_err})")

    def on_hotkey(self) -> None:
        if not self._busy.acquire(blocking=False):
            print("[snap] busy, skip", flush=True)
            winsound.Beep(400, 80)
            return
        try:
            # debounce accidental double-fire
            now = time.time()
            if now - self._last_ok < 0.35:
                return
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            dest = Path(self.cfg["inbox_dir"]) / f"{stamp}-snap.png"
            t0 = time.perf_counter()
            try:
                tag = self.capture_fast(dest)
            except Exception:
                # reconnect + rediscover display once
                try:
                    ensure_device(self.adb, self.serial)
                    self.refresh_display()
                    tag = self.capture_fast(dest)
                except Exception as exc:
                    print(f"[snap] FAIL {exc}", flush=True)
                    winsound.Beep(350, 280)
                    return
            ms = int((time.perf_counter() - t0) * 1000)
            self._last_ok = time.time()
            print(f"[snap] OK {ms}ms {dest.name} ({tag})", flush=True)
            winsound.Beep(1000, 90)
        finally:
            self._busy.release()


def message_loop(snapper: Snapper) -> int:
    if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, VK_SPACE):
        err = ctypes.get_last_error()
        print(f"[snap] RegisterHotKey failed (err={err}). Is Ctrl+Alt+Space already used?", flush=True)
        return 1
    print("[snap] hotkey = Ctrl+Alt+Space", flush=True)
    print("[snap] inbox =", snapper.cfg["inbox_dir"], flush=True)
    print("[snap] keep this window open. Ctrl+C to quit.", flush=True)

    msg = wintypes.MSG()
    try:
        while True:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret == 0:  # WM_QUIT
                break
            if ret == -1:
                break
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                # Run capture off the message thread so GetMessage stays snappy.
                threading.Thread(target=snapper.on_hotkey, daemon=True).start()
            else:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
    except KeyboardInterrupt:
        print("[snap] quit", flush=True)
    finally:
        user32.UnregisterHotKey(None, HOTKEY_ID)
    return 0


def main() -> int:
    snapper = Snapper()
    try:
        snapper.warm()
    except SystemExit as exc:
        print(exc, flush=True)
        print("[snap] waiting for device; will retry on first hotkey", flush=True)
    except Exception as exc:
        print(f"[snap] warm failed: {exc}", flush=True)
    return message_loop(snapper)


if __name__ == "__main__":
    raise SystemExit(main())
