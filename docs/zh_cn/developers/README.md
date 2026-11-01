# 开发者文档

> 面向想参与开发或在真机上联调 MaaWW 的人。使用说明见仓库根目录 [README](../../../README.md)。

## 工程原则

完整版见 [`AGENTS.md`](../../../AGENTS.md)，要点：

1. **状态驱动**：识别 → 操作 → 再识别，优先 `pre_wait_freezes` / `post_wait_freezes` 与中间节点，避免硬 `delay`。
2. **没有界面信息不写 Pipeline**：缺安卓截图、`roi`、模板与界面跳转时只写占位并标注待补。
3. **分辨率基准 1280×720**：坐标与模板一律按 720p。真机（奥丁 3 等）可以是 1080p，运行时由 `SetScreenshotTargetLongSide(1280)` 缩放后识别，点击坐标自动映回设备，**不必按 1080p 重标**。
4. **职责分离**：流程写在 Pipeline JSON；复杂算法 / 战斗循环放在 Go Service。
5. **首期只面向 ADB**，联调优先 AYN Odin 3 WiFi。

## 目录

```text
assets/
  interface.json          # 任务 / 控制器入口
  tasks/                  # 任务选项（Startup / Tacet / Nest / Daily / MultiAccount / SkipDialog）
  locales/                # 多语言
  resource/               # 推送到设备的资源镜像（由 resource_adb 同步生成）
  resource_adb/           # ADB 模板与 Pipeline（编辑主路径）
agent/
  go-service/
    combat/               # CombatLoop、HUD 队伍识别(team.go)、聚落 / 无音区动作
    account/              # 多账号：AccountLoop / AccountHoldKey / AccountFail
Android/overlays/         # 覆盖到外部 MaaFwApp 的补丁（手柄转发 / 摇杆泵）
docs/zh_cn/
  roadmap.md              # 路线图
  odin-nav-calib.json     # 奥丁导航坐标摘要
tools/touch-review/       # 截图 + 浏览器标注 → review/cards
review/
  inbox/                  # 待标注截图
  cards/                  # 已导出审查卡
FEATURES.md               # 对标 ok-ww 的功能清单
```

## 联调速查

```bat
REM 截图（1280x720）
python tools\touch-review\capture.py --label pad-hud

REM 标注页 http://127.0.0.1:8765/
python tools\touch-review\serve.py

REM 推 PI 到奥丁上的 MaaWW（改 pipeline/image/tasks/locales 后；会强停 App）
python tools\_push_pi_only.py

REM 改了 Go agent / Android overlays：重新出包并装机（先设 MAAWW_ANDROID_BUILD、ANDROID_SERIAL）
pwsh -NoProfile -File tools\android-build-install.ps1

REM 改了 assets/resource_adb 后同步到 assets/resource
python tools\sync_resource_from_adb.py

REM Go 单测（agent/go-service）
go test ./combat/ ./account/
```

- 设备序列号以 `tools/touch-review/config.json` 的 `serial` 为准（奥丁 WiFi 调试端口会变；`_nest_verify.py` 也可用环境变量 `ANDROID_SERIAL` 覆盖）。
- 联调时 App 界面常被截成旧画面，判断状态以日志（`files/log/maafw.log`、`files/pi/debug/go-service.log`）和 `files/log/on_error/*.png` 为准。
- 验收纪律：固化的 MaaWW 软件验证**不要**用 ADB 直接替软件点奥丁，要走任务入口 / MXU；测完用 `adb shell input keyevent KEYCODE_SLEEP` 关屏。详见 `.cursor/rules/odin-test-discipline.mdc`。

## 本机私有配置

设备 PIN、序列号、内网 git 地址等只放 `tools/touch-review/config.json`（已 `.gitignore`，不入库）。

1. 新机器先复制 `tools/touch-review/config.example.json` 为 `config.json` 并填写。
2. 脚本通过 `tools/_local_cfg.py` 读取；环境变量 `ODIN_PIN` / `ANDROID_SERIAL` / `REF_GIT_BASE` 可覆盖。
3. 提交前运行 `python tools\check_secrets.py`，检查已跟踪文件里有没有本机 PIN / 序列号 / 手机号。

## Git 推送

远程为 Cursor Origin，**只在 WSL** 用 `origin` 登录后 `git push`，禁止原生 Windows / PowerShell 直推（见 `AGENTS.md`）。

## 手柄态导航要点

标定摘要见 [`odin-nav-calib.json`](../odin-nav-calib.json)；审查卡在 `review/cards/`。

```text
启动
  TitleClickConnect / OCR「点击连接」
  → StartupPadWatch：查 PadReady；不符则 StartupPadSwitchOnce（A）
  → 弹窗确认（若有）→ 等 10s 再查；SwitchOnce 最多 15 次
  → StartupPadReady（左下 View+「地图」）成功结束

无音清剿
  OpenGuidebook / FromWorld → Terminal [1221, 35]
  → SolaGuidebookTile [634, 499]
  → SolaGuidebookExtra（左栏双剑 [51, 214]，手柄多一步）
  → SolaGuidebookOpened（双剑选中态，仅验证）
  → GuidebookTacetTab「无音清剿」
  → SelectTacetRow / TacetGo* / 开启挑战 / 战斗 / 结算
```

```text
多账号轮跑（每个账号）
  AccountEnsureGame：已在大世界 / 登录页则放行，否则拉起游戏并走启动等待链
  → AccountSwitchMain：Terminal 图标 → 终端页长按 Start(108) → 弹窗「返回登录」
  → AccountLoginSheet：当前行后四位 = 目标 ? 点登录 : 点下拉箭头 → AccountPickRow 选行 → 回登录页
  → 登录 → StartUpGameWait（下载条 / 点击连接 / 切手柄）→ 手柄大世界
  → 依次 NestRun / TacetMain / DailyMain（勾选的）
```

注意：

- 勿用过小 Terminal 图标做「是否大世界」判断（标题页会误命中）。
- 进大世界后须先 `StartupSwitchPad`，再验手柄图标（禁止检查点抢在按 A 前结束任务）。
- 误进「活跃行迹」时优先走 `SolaGuidebookExtra`，不要当成功。
- 同一节点字段上的 `pipeline_override` 是**浅替换**，不会深合并；多选项要拆到各自的 gate 节点（见 [`agent/go-service/README.md`](../../../agent/go-service/README.md) 的多账号一节）。

## 参考与延伸

| 文档 | 内容 |
| --- | --- |
| [`roadmap.md`](../roadmap.md) | 里程碑 |
| [`FEATURES.md`](../../../FEATURES.md) | 对标 ok-ww 的功能清单与状态 |
| [`agent/go-service/README.md`](../../../agent/go-service/README.md) | Go Service：战斗循环、聚落、多账号 |
| [`resolution-scaling.md`](../resolution-scaling.md) | 分辨率缩放 |
| [`ww-input-map.md`](../ww-input-map.md) | 手柄 / 按键映射 |
| [`tacet-select-design.md`](../tacet-select-design.md) | 无音区选行设计 |
| [`nest-analysis-ok-ww.md`](../nest-analysis-ok-ww.md) | 聚落对标分析 |
| [`emulator-setup.md`](../emulator-setup.md) | 模拟器配置（非主路径） |

参考仓库（只读借鉴，勿混提 PR）：[MaaEnd](https://github.com/MaaEnd/MaaEnd)（框架与工程）、[ok-ww](https://github.com/ok-oldking/ok-wuthering-waves)（功能与战斗逻辑）。
