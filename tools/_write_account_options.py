"""Rewrite MultiAccount checkbox cases to set custom_action_param.enable.<Name> (UTF-8, no BOM)."""
import json
import pathlib

p = pathlib.Path(__file__).resolve().parent.parent / "assets" / "tasks" / "MultiAccount.json"
d = json.loads(p.read_text(encoding="utf-8"))
for case in d["option"]["AccountTasks"]["cases"]:
    case["pipeline_override"] = {"AccountTask" + case["name"]: {"attach": {"on": True}}}
p.write_text(json.dumps(d, ensure_ascii=False, indent=4) + "\n", encoding="utf-8", newline="\n")
print("ok")
