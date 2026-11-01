#!/usr/bin/env python3
"""One-off: register tasks/Nest.json in interface.json and add zh/en locale strings."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

p = ROOT / "assets/interface.json"
s = p.read_text(encoding="utf-8")
if "tasks/Nest.json" not in s:
    s = s.replace('"tasks/Tacet.json",', '"tasks/Tacet.json",\n        "tasks/Nest.json",', 1)
    p.write_text(s, encoding="utf-8", newline="")
json.loads(s)


def add(path, extra):
    f = ROOT / path
    j = json.loads(f.read_text(encoding="utf-8"))
    j.update(extra)
    f.write_text(json.dumps(j, ensure_ascii=False, indent=4) + "\n", encoding="utf-8", newline="\n")


add("assets/locales/zh_cn.json", {
    "task.Nest.label": "聚落（残象 / 梦魇）",
    "task.Nest.description": "手册→素材获取→残象聚落/梦魇祛除：OCR 选未完成行（n/m 中 n=0）→ 快速旅行 / 直接挑战 → 战斗（任务栏「已清剿」判结束）→ 吸收声骸 → 下一个。P1 骨架，待奥丁联调。",
    "option.NestKind.label": "聚落类型",
    "option.NestKind.description": "残象聚落：前往→快速旅行（无确认框）。梦魇祛除：直接挑战→编队页开启挑战（战斗 HUD 待补）。",
    "option.NestKind.case.Canxiang": "残象聚落",
    "option.NestKind.case.Nightmare": "梦魇祛除",
})
add("assets/locales/en_us.json", {
    "task.Nest.label": "Nest (Echo / Nightmare)",
    "task.Nest.description": "Guidebook → Materials → Echo Nest / Nightmare: OCR the first unfinished row (n/m with n=0) → Fast Travel / Direct Challenge → combat (quest bar says cleared) → absorb echoes → next. P1 skeleton, pending Odin acceptance.",
    "option.NestKind.label": "Nest kind",
    "option.NestKind.description": "Echo Nest: Go → Fast Travel (no confirm). Nightmare: Direct Challenge → Start Challenge on the team page (combat HUD TBD).",
    "option.NestKind.case.Canxiang": "Echo Nest",
    "option.NestKind.case.Nightmare": "Nightmare",
})
print("ok")
