"""Nest: NestKind becomes a checkbox (both kinds selectable); entry NestRun runs NestMain per kind.
Also fixes task order for MultiAccount (Daily last). UTF-8, no BOM, mirrors pipelines."""
import json
import pathlib
import shutil

root = pathlib.Path(__file__).resolve().parent.parent / "assets"


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def save(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=4) + "\n", encoding="utf-8", newline="\n")


# pipeline
pp = root / "resource_adb" / "pipeline" / "Nest.json"
d = load(pp)
d["NestRun"] = {
    "desc": "聚落任务入口：Go NestKinds 按任务选项 NestKind 勾选的类型（残象聚落 / 梦魇祛除，可都选）依次跑 NestMain。",
    "recognition": "DirectHit",
    "action": {"type": "Custom", "param": {"custom_action": "NestKinds"}},
}
for name in ("Canxiang", "Nightmare"):
    d["NestKind" + name] = {
        "desc": "开关节点：NestKind 勾选对应类型时 pipeline_override 把 attach.on 改成 true；Go NestKinds 读取。不参与识别。",
        "recognition": "DirectHit",
        "action": "DoNothing",
        "attach": {"on": False},
    }
save(pp, d)
shutil.copyfile(pp, root / "resource" / "pipeline" / "Nest.json")

# task
tp = root / "tasks" / "Nest.json"
t = load(tp)
t["task"][0]["entry"] = "NestRun"
opt = t["option"]["NestKind"]
opt["type"] = "checkbox"
opt["default_case"] = ["Canxiang"]
opt["min_count"] = 1
for case in opt["cases"]:
    case["pipeline_override"] = {"NestKind" + case["name"]: {"attach": {"on": True}}}
save(tp, t)

# locale text
for name, desc in (
    ("zh_cn.json", "可多选，选了几种就依次跑几种。残象聚落：前往→快速旅行（无确认框）。梦魇祛除：直接挑战→编队页开启挑战（战斗 HUD 待补）。"),
    ("en_us.json", "Multi-select; each selected kind runs in turn."),
):
    lp = root / "locales" / name
    L = load(lp)
    if name == "zh_cn.json" or "option.NestKind.description" in L:
        L["option.NestKind.description"] = desc
    save(lp, L)
print("ok")
