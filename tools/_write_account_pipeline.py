"""Write the real AccountSwitch pipeline nodes into Account.json (UTF-8, no BOM), mirror to resource/."""
import json
import pathlib
import shutil

root = pathlib.Path(__file__).resolve().parent.parent / "assets"
p = root / "resource_adb" / "pipeline" / "Account.json"
d = json.loads(p.read_text(encoding="utf-8"))
d["AccountLoopMain"]["action"]["param"]["custom_action_param"]["current_node"] = "AccountCurrentIsTarget"
for k in list(d):
    if k != "AccountLoopMain":
        d.pop(k)
cap = d["AccountLoopMain"]["action"]["param"]["custom_action_param"]
cap["ensure_entry"] = "AccountEnsureGame"
cap.pop("enable", None)
for t in cap["tasks"]:
    t["gate"] = "AccountTask" + t["name"]
for name in ("Daily", "Nest", "Tacet"):
    d["AccountTask" + name] = {
        "desc": "开关节点：AccountTasks 勾选对应任务时 pipeline_override 把 attach.on 改成 true；Go AccountLoop 用 GetNode().Attach 读取。不参与识别。",
        "recognition": "DirectHit",
        "action": "DoNothing",
        "attach": {"on": False},
    }

d.update({
    "AccountEnsureGame": {
        "desc": "切号前保证游戏在前台：已在手柄大世界 / 已在库洛登录页 → 直接成功；否则（黑屏、未启动、标题页）StartApp 后走 StartUpGameWait 到大世界。",
        "next": ["StartupPadReady", "StartupPadReadyMenu", "AccountLoginSheetSeen", "AccountLaunch"],
    },
    "AccountLoginSheetSeen": {
        "desc": "已在库洛登录页，无需拉起。",
        "recognition": "OCR",
        "roi": [540, 470, 200, 50],
        "expected": ["其他登录方式"],
        "action": "DoNothing",
        "next": [],
    },
    "AccountLaunch": {
        "desc": "拉起 / 前台化游戏（不 force-stop），之后走启动等待链直到手柄大世界。",
        "recognition": "DirectHit",
        "action": {"type": "StartApp", "param": {"package": "com.kurogame.mingchao/com.epicgames.ue4.GameActivity"}},
        "next": ["StartUpGameWait"],
    },
    "AccountSwitchMain": {
        "desc": "切号入口（坐标均 1280x720，来自 20261101 用户 6 张截图，原图 1024x576 换算）。流程：大世界点顶栏 Terminal → 终端页长按 Start(108) → 弹窗「是否确定退出游戏？」点「返回登录」→ 库洛登录页：当前行后四位=目标则点登录，否则点下拉箭头选目标行 → 登录后进 StartUpGameWait（下载条 / 点击连接 / 手柄切换 / 月卡，到手柄 HUD 结束）。目标后四位由 Go AccountLoop 在 AccountCurrentIsTarget / AccountPickRow 的 expected 里 override。",
        "next": ["AccountLoginSheet", "AccountQuitDialog", "AccountTerminalPage", "AccountOpenTerminal"],
        "timeout": 20000,
        "on_error": ["AccountSwitchFail"],
    },
    "AccountOpenTerminal": {
        "desc": "大世界手柄态顶栏 Terminal 图标（同 DailyOpenGuidebook）。",
        "recognition": "TemplateMatch",
        "roi": [1180, 0, 100, 80],
        "template": "Guidebook/OpenGuidebookPad.png",
        "threshold": 0.72,
        "action": "Click",
        "target": [1221, 35],
        "post_wait_freezes": {"time": 500, "timeout": 8000, "threshold": 0.95},
        "next": ["AccountTerminalPage"],
        "timeout": 8000,
        "on_error": ["AccountSwitchFail"],
    },
    "AccountTerminalPage": {
        "desc": "终端页（左上「终端」）。页脚「(长按)退出游戏」= 手柄菜单键，长按 Start(KEYCODE_BUTTON_START=108) 弹出退出弹窗。",
        "recognition": "OCR",
        "roi": [50, 15, 140, 45],
        "expected": ["终端"],
        "action": {
            "type": "Custom",
            "param": {"custom_action": "AccountHoldKey", "custom_action_param": {"key": 108, "hold_ms": 1500}},
        },
        "max_hit": 4,
        "post_delay": 800,
        "next": ["AccountQuitDialog", "AccountTerminalPage"],
        "timeout": 6000,
        "on_error": ["AccountSwitchFail"],
    },
    "AccountQuitDialog": {
        "desc": "「是否确定退出游戏？」弹窗，左「退出游戏」右「返回登录」。识别右侧按钮文字并点击（勿点左侧退出游戏）。",
        "recognition": "OCR",
        "roi": [740, 425, 200, 52],
        "expected": ["返回登录"],
        "action": "Click",
        "next": ["AccountLoginSheet"],
        "timeout": 60000,
        "on_error": ["AccountSwitchFail"],
    },
    "AccountLoginSheet": {
        "desc": "库洛登录页：用底部「其他登录方式」认页（下拉展开时被盖住，不会误命中）。",
        "recognition": "OCR",
        "roi": [540, 470, 200, 50],
        "expected": ["其他登录方式"],
        "action": "DoNothing",
        "next": ["AccountCurrentIsTarget", "AccountOpenDropdown"],
        "timeout": 8000,
        "on_error": ["AccountSwitchFail"],
    },
    "AccountCurrentIsTarget": {
        "desc": "当前选中行（如 153****0075）后四位 = 目标 → 点「登录」(639,415)，转入启动等待链。expected 由 Go override 为目标后四位。",
        "recognition": "OCR",
        "roi": [387, 285, 502, 66],
        "expected": ["__ACCOUNT_LAST4__"],
        "action": "Click",
        "target": [639, 415],
        "post_wait_freezes": {"time": 800, "timeout": 8000, "threshold": 0.95},
        "next": ["StartUpGameWait"],
        "on_error": ["AccountSwitchFail"],
    },
    "AccountOpenDropdown": {
        "desc": "当前行不是目标：点右侧下拉箭头 (851,317) 展开列表（3 行，行距约 70px）。",
        "recognition": "DirectHit",
        "action": "Click",
        "target": [851, 317],
        "post_delay": 700,
        "next": ["AccountPickRow"],
        "timeout": 6000,
        "on_error": ["AccountSwitchFail"],
    },
    "AccountPickRow": {
        "desc": "展开列表里后四位 = 目标的行（行中心 y≈391/461/531）。expected 由 Go override。选后回到登录页再认当前行。账号不在列表则超时失败。",
        "recognition": "OCR",
        "roi": [387, 360, 502, 210],
        "expected": ["__ACCOUNT_LAST4__"],
        "action": "Click",
        "post_delay": 800,
        "next": ["AccountLoginSheet"],
        "timeout": 8000,
        "on_error": ["AccountSwitchFail"],
    },
    "AccountSwitchFail": {
        "desc": "切号失败：Go 动作返回 false，使 RunTask 判失败，AccountLoop 跳过该账号。",
        "recognition": "DirectHit",
        "action": {"type": "Custom", "param": {"custom_action": "AccountFail"}},
        "next": [],
    },
})
p.write_text(json.dumps(d, ensure_ascii=False, indent=4) + "\n", encoding="utf-8", newline="\n")
shutil.copyfile(p, root / "resource" / "pipeline" / "Account.json")
print("ok", len(d))
