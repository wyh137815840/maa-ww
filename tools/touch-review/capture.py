#!/usr/bin/env python3
"""Capture a MuMu/ADB screenshot into review/inbox at 1280x720.

On MuMu Android 15, default screencap often hits the launcher display.
Game content is usually on a virtual display named mumuscreen001 — we
prefer that (or config display_id / display_name).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from PIL import Image

from common import load_config


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(cmd, check=check, capture_output=True)


def run_text(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, capture_output=True, text=True, encoding="utf-8", errors="ignore")


def ensure_device(adb: str, serial: str) -> None:
    run([adb, "connect", serial], check=False)
    out = run_text([adb, "devices"]).stdout
    online = set()
    for ln in out.splitlines()[1:]:
        parts = ln.split()
        if len(parts) >= 2 and parts[1] == "device":
            online.add(parts[0])
    if serial not in online:
        raise SystemExit(f"device not online: {serial}\n{out}")


def list_display_ids(adb: str, serial: str) -> list[tuple[str, str]]:
    """Return [(display_id, name), ...] from SurfaceFlinger."""
    r = run([adb, "-s", serial, "shell", "dumpsys", "SurfaceFlinger", "--display-id"], check=False)
    text = (r.stdout or b"").decode("utf-8", "ignore")
    found: list[tuple[str, str]] = []
    for m in re.finditer(
        r"Display\s+(\d+)\s*\(HWC display\s+\d+\):.*?displayName=\"([^\"]+)\"",
        text,
        flags=re.S,
    ):
        found.append((m.group(1), m.group(2)))
    if not found:
        # fallback: bare ids
        for did in re.findall(r"Display\s+(\d{10,})", text):
            found.append((did, ""))
    return found


def pick_display_id(adb: str, serial: str, cfg: dict) -> str | None:
    if cfg.get("display_id"):
        return str(cfg["display_id"])
    prefer = str(cfg.get("display_name") or "mumuscreen001").lower()
    displays = list_display_ids(adb, serial)
    for did, name in displays:
        if prefer and prefer in name.lower():
            return did
    # Prefer any mumuscreen00N that is not 000 (000 often mirrors launcher)
    for did, name in displays:
        n = name.lower()
        if "mumuscreen" in n and not n.endswith("000"):
            return did
    return displays[0][0] if displays else None


def _score_image(path: Path) -> tuple[int, float]:
    """Higher is better: reject near-black / flat wallpaper-ish frames."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    samples = [
        im.getpixel((w // 2, h // 2)),
        im.getpixel((w // 4, h // 4)),
        im.getpixel((3 * w // 4, 3 * h // 4)),
        im.getpixel((w // 5, 4 * h // 5)),
        im.getpixel((4 * w // 5, h // 5)),
    ]
    means = [sum(p) / 3 for p in samples]
    mean = sum(means) / len(means)
    var = sum((m - mean) ** 2 for m in means) / len(means)
    # near-black → bad
    if mean < 5 and var < 5:
        return (0, mean)
    return (int(var * 10 + mean), mean)


def capture_png(adb: str, serial: str, dest: Path, cfg: dict) -> str:
    """Capture and save; return which display strategy was used."""
    display_id = pick_display_id(adb, serial, cfg)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)
        candidates: list[tuple[str, Path]] = []

        if display_id:
            remote = "/data/local/tmp/maa_ww_touch_review.png"
            run([adb, "-s", serial, "shell", "rm", "-f", remote], check=False)
            r = run(
                [adb, "-s", serial, "shell", "screencap", "-d", display_id, "-p", remote],
                check=False,
            )
            local = tmp_p / "picked.png"
            run([adb, "-s", serial, "pull", remote, str(local)], check=False)
            if local.is_file() and local.stat().st_size > 1000:
                candidates.append((f"display:{display_id}", local))

        # Always also try -a as fallback / verification
        run([adb, "-s", serial, "shell", "rm", "-f", "/data/local/tmp/maa_ww_all*.png"], check=False)
        run(
            [adb, "-s", serial, "shell", "screencap", "-a", "-p", "/data/local/tmp/maa_ww_all.png"],
            check=False,
        )
        ls = run_text([adb, "-s", serial, "shell", "ls", "/data/local/tmp/maa_ww_all*.png"], check=False)
        for ln in ls.stdout.splitlines():
            name = Path(ln.strip().split()[-1]).name if ln.strip() else ""
            if not name.startswith("maa_ww_all"):
                # ls -1 style
                name = Path(ln.strip()).name
            if not name.endswith(".png"):
                continue
            remote = f"/data/local/tmp/{name}"
            local = tmp_p / name
            run([adb, "-s", serial, "pull", remote, str(local)], check=False)
            if local.is_file() and local.stat().st_size > 1000:
                candidates.append((f"all:{name}", local))

        if not candidates:
            # last resort default screencap
            remote = "/data/local/tmp/maa_ww_touch_review.png"
            local = tmp_p / "default.png"
            run([adb, "-s", serial, "shell", "rm", "-f", remote], check=False)
            run([adb, "-s", serial, "shell", "screencap", "-p", remote])
            run([adb, "-s", serial, "pull", remote, str(local)])
            candidates.append(("default", local))

        # Prefer the explicitly resolved display capture when it has real content.
        # Scoring across -a can wrongly pick launcher wallpaper when the game
        # display is dim, or when the user is mid-transition.
        preferred: list[tuple[str, Path, int]] = []
        others: list[tuple[str, Path, int]] = []
        for tag, path in candidates:
            try:
                score, _ = _score_image(path)
            except Exception:
                continue
            row = (tag, path, score)
            if tag.startswith("display:") and score > 0:
                preferred.append(row)
            else:
                others.append(row)

        pool = preferred or [r for r in others if r[2] > 0] or others
        if not pool:
            raise RuntimeError("no usable screencap candidates")
        best_tag, best_path, best_score = max(pool, key=lambda r: r[2])

        img = Image.open(best_path).convert("RGB")
        tw, th = cfg["target_size"]
        if img.size != (tw, th):
            img = img.resize((tw, th), Image.Resampling.LANCZOS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest, format="PNG")
        return f"{best_tag};score={best_score}"


def main() -> int:
    cfg = load_config()
    parser = argparse.ArgumentParser(description="Capture ADB screenshot for touch review")
    parser.add_argument("--label", default="", help="optional filename label")
    parser.add_argument("--serial", default=cfg["serial"])
    parser.add_argument("--adb", default=cfg["adb_path"])
    parser.add_argument("--display-id", default="", help="override SurfaceFlinger display id")
    parser.add_argument("--display-name", default="", help="prefer displayName substring")
    args = parser.parse_args()

    adb = Path(args.adb)
    if not adb.is_file():
        raise SystemExit(f"adb not found: {adb}")

    if args.display_id:
        cfg = {**cfg, "display_id": args.display_id}
    if args.display_name:
        cfg = {**cfg, "display_name": args.display_name}

    ensure_device(str(adb), args.serial)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = f"-{args.label}" if args.label else ""
    out = Path(cfg["inbox_dir"]) / f"{stamp}{suffix}.png"
    tag = capture_png(str(adb), args.serial, out, cfg)
    print(out)
    print(f"source={tag}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        err = exc.stderr or exc.stdout or b""
        if isinstance(err, bytes):
            err = err.decode("utf-8", "ignore")
        sys.stderr.write(str(err) + "\n")
        raise SystemExit(exc.returncode)
