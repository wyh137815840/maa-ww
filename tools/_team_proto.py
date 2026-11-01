"""Prototype for HUD team portrait perception (1280x720)."""
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
alive = cv2.imread(str(ROOT / "review/cards/20261101-185827-nestcombathud/screen.png"))
dead = cv2.imread(str(ROOT / "review/inbox/20261101-200023-snap.png"))
CEN = [(1172, 153), (1172, 238), (1172, 326)]
H = 14  # template half size


def gray(im):
    return cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)


tpl = {}
for name, (cx, cy) in zip(["hiyuki", "lucilla", "suisui"], CEN):
    tpl[name] = gray(alive)[cy - H : cy + H, cx - H : cx + H]

for tag, im in (("alive", alive), ("dead", dead)):
    g = gray(im)
    for i, (cx, cy) in enumerate(CEN):
        win = g[cy - H - 10 : cy + H + 10, cx - H - 10 : cx + H + 10]
        scores = {}
        for n, t in tpl.items():
            r = cv2.matchTemplate(win, t, cv2.TM_CCOEFF_NORMED)
            scores[n] = round(float(r.max()), 3)
        # badge: blue saturated pixels right of portrait
        hsv = cv2.cvtColor(im[cy - 4 : cy + 20, cx + 8 : cx + 34], cv2.COLOR_BGR2HSV)
        blue = ((hsv[..., 0] >= 90) & (hsv[..., 0] <= 112) & (hsv[..., 1] > 110) & (hsv[..., 2] > 140)).sum()
        # bar fill: brightest row's bright pixel count in band
        best = 0
        for y in range(cy + 18, cy + 34):
            row = im[y, cx - 28 : cx + 28]
            hs = cv2.cvtColor(row.reshape(1, -1, 3), cv2.COLOR_BGR2HSV)[0]
            c = int(((hs[:, 2] > 190) & (hs[:, 1] < 60)).sum())
            best = max(best, c)
        print(tag, i, scores, "badge_blue", int(blue), "bar_bright", best)
