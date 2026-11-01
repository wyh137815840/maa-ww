#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
msg = root / "tools/touch-review/_commit_msg.txt"
# Ensure message file exists
if not msg.is_file():
    msg.write_text(
        "feat: wire Tacet pipeline from guidebook through settle\n\n"
        "Add ADB templates and nodes for challenge complete, claim reward, "
        "double/single stamina, continue/exit, and stamina exhausted; "
        "document prefer-double policy and hotkey snap service for short-lived UI.\n",
        encoding="utf-8",
    )

# Prefer Windows git that supports modern options if needed; avoid injected argv.
git = "git"
r = subprocess.run([git, "commit", "-F", str(msg)], cwd=str(root))
msg.unlink(missing_ok=True)
if r.returncode != 0:
    sys.exit(r.returncode)
subprocess.run([git, "log", "-1", "--oneline"], cwd=str(root), check=False)
subprocess.run([git, "status", "--short"], cwd=str(root), check=False)
