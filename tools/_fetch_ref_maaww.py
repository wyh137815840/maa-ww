#!/usr/bin/env python3
"""Clone/fetch verified maaww from local Gitea and locate launch-game code."""
from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

BASE = "http://192.168.1.4:8929"
OWNER = "wyh"
REPO = "maaww"
DEST = Path(r"D:\git\_ref_maaww")


def get(url: str):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read()


def main() -> int:
    # Probe APIs
    for path in (
        f"/api/v1/repos/{OWNER}/{REPO}",
        f"/api/v1/repos/{OWNER}/{REPO}/contents",
        f"/api/v1/repos/{OWNER}/{REPO}/git/trees/master?recursive=1",
        f"/api/v1/repos/{OWNER}/{REPO}/git/trees/main?recursive=1",
    ):
        url = BASE + path
        try:
            data = get(url)
            print("OK", path, "len", len(data))
            text = data.decode("utf-8", "ignore")
            print(text[:1500])
            print("---")
        except Exception as e:
            print("FAIL", path, e)

    # Prefer git clone
    if DEST.exists():
        print("DEST exists", DEST)
        subprocess.run(["git", "-C", str(DEST), "fetch", "--all"], check=False)
        subprocess.run(["git", "-C", str(DEST), "pull", "--ff-only"], check=False)
    else:
        url = f"{BASE}/{OWNER}/{REPO}.git"
        print("cloning", url)
        r = subprocess.run(["git", "clone", "--depth", "1", url, str(DEST)])
        if r.returncode != 0:
            # try without .git
            url2 = f"{BASE}/{OWNER}/{REPO}"
            print("retry clone", url2)
            subprocess.run(["git", "clone", "--depth", "1", url2, str(DEST)], check=False)

    if DEST.exists():
        # search launch-related
        for pat in ("启动", "开启", "Launch", "Startup", "monkey", "am start", "mingchao", "Wuthering"):
            print("=== ripgrep", pat)
            subprocess.run(
                ["rg", "-n", "-i", pat, str(DEST), "-g", "!*.png", "-g", "!*.jpg"],
                check=False,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
