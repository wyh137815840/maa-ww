import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
imgs = {
    "alive": ROOT / "review/cards/20261101-185827-nestcombathud/screen.png",
    "dead": ROOT / "review/inbox/20261101-200023-snap.png",
}
centers = [(1175, 152), (1175, 240), (1175, 325)]
tiles = []
for name, p in imgs.items():
    im = cv2.imread(str(p))
    row = []
    for i, (cx, cy) in enumerate(centers):
        c = im[cy - 34 : cy + 40, cx - 40 : cx + 40]
        big = cv2.resize(c, None, fx=6, fy=6, interpolation=cv2.INTER_NEAREST)
        # grid lines every 10 px (60 px big) to read coordinates
        for k in range(0, 80, 10):
            cv2.line(big, (k * 6, 0), (k * 6, big.shape[0]), (0, 255, 255), 1)
        for k in range(0, 74, 10):
            cv2.line(big, (0, k * 6), (big.shape[1], k * 6), (0, 255, 255), 1)
        row.append(big)
    tiles.append(np.hstack(row))
cv2.imwrite(str(ROOT / "tools/_shots/pt_grid2.png"), np.vstack(tiles))
