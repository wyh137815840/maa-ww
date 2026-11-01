#!/usr/bin/env python3
"""Odin snap service: Ctrl+Alt+Space → inbox *-snap.png + auto annotation card (brief).

- Captures the Odin's *current* screen (default `screencap -p`, follows rotation).
  Set `display_id` in config.json only if you need a specific display.
- Every snap gets a `<name>.brief.json` so it shows up as 「待标注」 in the
  annotator (serve.py). The brief text comes from `review/snap_session.json`
  (the agent updates it for each scene), so you always see what to mark.
- Starts the annotator (serve.py, http://127.0.0.1:8765/) if it is not running,
  and opens the browser once on the first snap.

Usage:
    python tools/touch-review/snap_service.py          # hotkey service (keep running)
    python tools/touch-review/snap_service.py --once   # capture one now (no hotkey), for testing
"""

from __future__ import annotations

import argparse
import ctypes
import json
import socket
import subprocess
import sys
import threading
import time
import webbrowser
import winsound
from ctypes import wintypes
from datetime import datetime
from pathlib import Path

from PIL import Image

from brief import write_brief
from capture import ensure_device, run
from common import ROOT, load_config

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000
VK_SPACE = 0x20
WM_HOTKEY = 0x0312
HOTKEY_ID = 0x4D414153  # 'MAAS'

user32 = ctypes.windll.user32

SESSION_PATH = ROOT / "review" / "snap_session.json"
DEFAULT_SESSION = {
    "title": "待标注截图",
    "goal": "框出要识别的 ROI，再点点击点（如需）；核对右侧字段后导出审查卡。",
    "steps": ["先框 ROI", "再点点击点（若是纯识别则可不点）", "核对 label / note 后导出审查卡"],
    "suggested_label": "",
    "suggested_expected_next": "",
    "suggested_note": "",
    "do_not": [],
}


def port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.4):
            return True
    except OSError:
        return False


def load_session() -> dict:
    """Current scene description written by the agent. Missing/broken → defaults."""
    try:
        data = json.loads(SESSION_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {**DEFAULT_SESSION, **data}
    except (OSError, json.JSONDecodeError):
        pass
    return dict(DEFAULT_SESSION)


class Snapper:
    def __init__(self) -> None:
        self.cfg = load_config()
        self.adb = str(Path(self.cfg["adb_path"]))
        self.serial = str(self.cfg["serial"])
        # Only an explicit config display; never auto-pick (MuMu-era heuristic).
        self.display_id: str | None = str(self.cfg["display_id"]) if self.cfg.get("display_id") else None
        self._busy = threading.Lock()
        self._last_ok = 0.0
        self._opened_browser = False
        self._seq_session = ""
        self._seq = 0
        self._serve_proc: subprocess.Popen | None = None

    # ---- annotator -------------------------------------------------
    def ensure_annotator(self) -> None:
        host = str(self.cfg.get("host", "127.0.0.1"))
        port = int(self.cfg.get("port", 8765))
        if port_open(host, port):
            return
        script = Path(__file__).resolve().parent / "serve.py"
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self._serve_proc = subprocess.Popen(
            [sys.executable, str(script), "--no-browser"],
            cwd=str(ROOT),
            creationflags=flags,
        )
        for _ in range(20):
            if port_open(host, port):
                break
            time.sleep(0.15)
        print(f"[snap] annotator started http://{host}:{port}/", flush=True)

    def open_browser_once(self) -> None:
        if self._opened_browser:
            return
        self._opened_browser = True
        host = str(self.cfg.get("host", "127.0.0.1"))
        port = int(self.cfg.get("port", 8765))
        try:
            webbrowser.open(f"http://{host}:{port}/")
        except Exception:  # noqa: BLE001
            pass

    # ---- capture ---------------------------------------------------
    def warm(self) -> None:
        ensure_device(self.adb, self.serial)
        print(f"[snap] device={self.serial} display_id={self.display_id or 'default'}", flush=True)

    def capture_fast(self, dest: Path) -> tuple[str, tuple[int, int]]:
        """Screencap → dest at target size. Returns (tag, raw_size)."""
        tw, th = self.cfg["target_size"]
        cmds: list[list[str]] = []
        if self.display_id:
            cmds.append([self.adb, "-s", self.serial, "exec-out", "screencap", "-d", self.display_id, "-p"])
        cmds.append([self.adb, "-s", self.serial, "exec-out", "screencap", "-p"])

        last_err = ""
        for cmd in cmds:
            try:
                r = subprocess.run(cmd, check=False, capture_output=True, timeout=10)
            except subprocess.TimeoutExpired:
                last_err = "timeout"
                continue
            data = r.stdout or b""
            if r.returncode != 0 or len(data) < 1000:
                last_err = (r.stderr or b"").decode("utf-8", "ignore")[:200]
                continue
            sig = data.find(b"\x89PNG")
            if sig < 0:
                last_err = "no png signature"
                continue
            data = data[sig:]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            try:
                img = Image.open(dest).convert("RGB")
            except Exception as exc:  # noqa: BLE001
                last_err = f"bad png: {exc}"
                continue
            raw = img.size
            if img.size != (tw, th):
                img = img.resize((tw, th), Image.Resampling.LANCZOS)
                img.save(dest, format="PNG")
            return ("exec-out:" + (self.display_id or "default"), raw)

        raise RuntimeError(f"capture failed ({last_err})")

    # ---- brief -----------------------------------------------------
    def write_card_brief(self, dest: Path, raw: tuple[int, int]) -> None:
        sess = load_session()
        key = json.dumps(sess, ensure_ascii=False, sort_keys=True)
        if key != self._seq_session:
            self._seq_session = key
            self._seq = 0
        self._seq += 1
        title = str(sess["title"])
        if self._seq > 1:
            title = f"{title} #{self._seq}"
        note = str(sess.get("suggested_note") or "")
        if raw[0] < raw[1]:
            note = (note + " " if note else "") + (
                f"⚠ 原图是竖屏 {raw[0]}x{raw[1]}（可能截到了 MaaWW 应用而不是游戏横屏），确认后再标。"
            )
        write_brief(
            dest,
            title=title,
            goal=str(sess["goal"]),
            steps=list(sess.get("steps") or []),
            suggested_label=str(sess.get("suggested_label") or ""),
            suggested_expected_next=str(sess.get("suggested_expected_next") or ""),
            suggested_note=note,
            do_not=list(sess.get("do_not") or []),
        )

    # ---- one snap --------------------------------------------------
    def snap(self) -> Path:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        dest = Path(self.cfg["inbox_dir"]) / f"{stamp}-snap.png"
        try:
            tag, raw = self.capture_fast(dest)
        except Exception:
            ensure_device(self.adb, self.serial)  # reconnect once
            tag, raw = self.capture_fast(dest)
        with Image.open(dest) as im:
            extrema = im.convert("L").getextrema()
        if extrema[1] < 12:
            dest.unlink(missing_ok=True)
            raise RuntimeError(
                "截到全黑：奥丁屏幕已息屏，或游戏在 MaaWW 虚拟显示上（screencap 截不到）。"
                "请亮屏，并让游戏在主屏前台（先停掉 MaaWW 任务/虚拟显示）。"
            )
        self.write_card_brief(dest, raw)
        print(f"[snap] OK {dest.name} ({tag}; raw={raw[0]}x{raw[1]})", flush=True)
        return dest

    def on_hotkey(self) -> None:
        if not self._busy.acquire(blocking=False):
            print("[snap] busy, skip", flush=True)
            winsound.Beep(400, 80)
            return
        try:
            now = time.time()
            if now - self._last_ok < 0.35:
                return
            t0 = time.perf_counter()
            try:
                self.ensure_annotator()
                self.snap()
            except Exception as exc:  # noqa: BLE001
                print(f"[snap] FAIL {exc}", flush=True)
                winsound.Beep(350, 280)
                return
            self._last_ok = time.time()
            print(f"[snap] {int((time.perf_counter() - t0) * 1000)}ms", flush=True)
            winsound.Beep(1000, 90)
            self.open_browser_once()
        finally:
            self._busy.release()


def message_loop(snapper: Snapper) -> int:
    if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, VK_SPACE):
        err = ctypes.get_last_error()
        print(f"[snap] RegisterHotKey failed (err={err}). Is Ctrl+Alt+Space already used / service already running?", flush=True)
        return 1
    print("[snap] hotkey = Ctrl+Alt+Space", flush=True)
    print("[snap] inbox =", snapper.cfg["inbox_dir"], flush=True)
    print("[snap] scene text from", SESSION_PATH, flush=True)
    print("[snap] keep this window open. Ctrl+C to quit.", flush=True)

    msg = wintypes.MSG()
    try:
        while True:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret == 0 or ret == -1:
                break
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="capture one snap now (no hotkey) and exit")
    args = ap.parse_args()

    snapper = Snapper()
    try:
        snapper.warm()
    except SystemExit as exc:
        print(exc, flush=True)
        print("[snap] waiting for device; will retry on first hotkey", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"[snap] warm failed: {exc}", flush=True)

    if args.once:
        snapper.ensure_annotator()
        print(snapper.snap())
        return 0
    snapper.ensure_annotator()
    return message_loop(snapper)


if __name__ == "__main__":
    raise SystemExit(main())
