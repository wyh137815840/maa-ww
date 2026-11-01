"""Add MultiAccount locale strings (UTF-8, no BOM)."""
import json
import pathlib

root = pathlib.Path(__file__).resolve().parent.parent / "assets" / "locales"
zh = {
    "task.MultiAccount.label": "多账号轮跑",
    "task.MultiAccount.description": "按「手机号」列表逐个切号（库洛登录页按后四位选号），每个账号把勾选的任务各跑一遍。切号失败的账号会被跳过。任务选项（聚落类型、无音区序号）对所有账号生效。",
    "option.AccountPhones.label": "账号手机号",
    "option.AccountPhones.description": "填你要轮跑的账号。登录页只显示被遮挡的手机号，实际按后四位匹配；手机号只保存在本机配置里。",
    "option.AccountPhones.input.phones": "手机号列表",
    "option.AccountPhones.input.phones.description": "多个账号用逗号、分号或空格分隔，例如：13800001234,13900005678（也可只填后四位）。后四位相同的账号无法区分，只保留第一个。",
    "option.AccountPhones.input.phones.pattern_msg": "只能填数字，账号之间用逗号/分号/空格分隔",
    "option.AccountTasks.label": "每个账号要跑的任务",
    "option.AccountTasks.description": "每切到一个账号，按「日常 → 聚落 → 无音区」顺序执行勾选的任务。",
}
en = {
    "task.MultiAccount.label": "Multi-account run",
    "task.MultiAccount.description": "Switch through the phone list (Kuro login sheet, matched by last 4 digits) and run the checked tasks on every account.",
    "option.AccountPhones.label": "Account phones",
    "option.AccountPhones.description": "The login sheet masks phones, so the last 4 digits are matched.",
    "option.AccountPhones.input.phones": "Phone list",
    "option.AccountPhones.input.phones.description": "Separate with comma, semicolon or space; last 4 digits alone also work.",
    "option.AccountPhones.input.phones.pattern_msg": "Digits only, separated by comma/semicolon/space",
    "option.AccountTasks.label": "Tasks per account",
    "option.AccountTasks.description": "Run in order Daily, Nest, Tacet for each account.",
}
for name, add in (("zh_cn.json", zh), ("en_us.json", en)):
    p = root / name
    d = json.loads(p.read_text(encoding="utf-8"))
    d.update(add)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=4) + "\n", encoding="utf-8", newline="\n")
print("ok")
