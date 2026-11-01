#!/usr/bin/env python3
"""Poll StartupLoadingBar template score every 10s, N times."""
from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture import capture_png, ensure_device  # noqa: E402
from common import load_config  # noqa: E402


def main() -> int:
    n = 5
    interval = 10
    thr = 0.65
    roi_xywh = (40, 610, 1200, 100)

    cfg = load_config()
    adb, serial = cfg["adb_path"], cfg["serial"]
    ensure_device(adb, serial)
    templ = cv2.imread(
        str(Path(__file__).resolve().parents[2] / "assets/resource_adb/image/Title/StartupLoadingBar.png"),
        cv2.IMREAD_COLOR,
    )
    if templ is None:
        raise SystemExit("template missing")

    outdir = cfg["inbox_dir"] / "_loading_bar_poll"
    outdir.mkdir(exist_ok=True)
    x, y, w, h = roi_xywh
    print(f"thr={thr} interval={interval}s n={n}", flush=True)
    print("t\tscore\tresult", flush=True)
    scores: list[float] = []
    for i in range(n):
        stamp = datetime.now().strftime("%H:%M:%S")
        dest = outdir / f"poll5_{i:02d}.png"
        capture_png(adb, serial, dest, cfg)
        screen = cv2.cvtColor(np.array(Image.open(dest).convert("RGB")), cv2.COLOR_RGB2BGR)
        roi = screen[y : y + h, x : x + w]
        score = float(cv2.minMaxLoc(cv2.matchTemplate(roi, templ, cv2.TM_CCOEFF_NORMED))[1])
        scores.append(score)
        hit = "HIT" if score >= thr else "MISS"
        print(f"{stamp}\t{score:.4f}\t{hit}", flush=True)
        if i < n - 1:
            time.sleep(interval)
    print(
        f"min={min(scores):.4f} max={max(scores):.4f} "
        f"avg={sum(scores)/len(scores):.4f} hit={sum(1 for s in scores if s >= thr)}/{n}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
