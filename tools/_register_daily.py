#!/usr/bin/env python3
"""One-off: register tasks/Daily.json in interface.json and add zh/en locale strings."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

p = ROOT / "assets/interface.json"
s = p.read_text(encoding="utf-8")
if "tasks/Daily.json" not in s:
    s = s.replace('"tasks/Nest.json",', '"tasks/Nest.json",\n        "tasks/Daily.json",', 1)
    p.write_text(s, encoding="utf-8", newline="")
json.loads(s)


def add(path, extra):
    f = ROOT / path
    j = json.loads(f.read_text(encoding="utf-8"))
    j.update(extra)
    f.write_text(json.dumps(j, ensure_ascii=False, indent=4) + "\n", encoding="utf-8", newline="\n")


add("assets/locales/zh_cn.json", {
    "task.Daily.label": "日常奖励领取",
    "task.Daily.description": "手册→索拉指南→活跃行迹：点一次「领取」领完所有已完成任务，活跃度到 100 时按 Y 领取全部宝箱，关闭奖励弹窗后离开手册。P1，待奥丁联调。",
})
add("assets/locales/en_us.json", {
    "task.Daily.label": "Claim Daily Rewards",
    "task.Daily.description": "Guidebook → Sola Guide → Daily Activity: click Claim once to collect every finished task, press Y for the chests when activity reaches 100, close the reward popup and leave. P1, pending Odin acceptance.",
})
print("ok")
