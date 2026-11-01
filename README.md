# MaaWW

基于 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 的《鸣潮》自动化项目。

- **框架**：对齐 [MaaEnd](https://github.com/MaaEnd/MaaEnd) 的工程分层（Pipeline 管流程，Go 管难点，ADB 资源分离）
- **功能对标**：[ok-ww](https://github.com/ok-oldking/ok-wuthering-waves)（ok-script / PC）
- **首期目标**：安卓 ADB — 启动进大世界（切手柄）+ 无音清剿骨架 + 基础自动战斗

## 状态（2026-11）

联调主路径已切到 **AYN Odin 3 WiFi ADB**（弃用模拟器为主路径）。资源与任务按 `docs/zh_cn/roadmap.md`、`FEATURES.md` 增量落地。

已可跑（奥丁实机迭代中）：

| 任务 | 说明 |
| --- | --- |
| **启动** | 冷拉起 → 标题「点击连接」→ 等进大世界 → **按物理 Xbox A 切手柄**（最多 3 次）→ 认手柄 HUD 检查点成功 |
| **无音清剿** | Terminal → 索拉指南 →（手柄多一步）左侧双剑 → 验证素材获取打开 → 无音清剿 tab → 选行 / 开启挑战 / 结算骨架 |

坐标与模板一律 **1280×720**；真机 1920×1080 由框架 `SetScreenshotTargetLongSide(1280)` 缩放后识别。

## 运行环境

| 项 | 要求 |
| --- | --- |
| 控制器 | ADB（真机优先） |
| 分辨率基准 | **1280×720**，16:9 |
| 联调设备 | **AYN Odin 3 WiFi**（`tools/touch-review/config.json` 的 `serial`） |
| 手柄 | 进大世界后切到控制器模式；战斗走 Go `CombatLoop` 手柄时序 |

设备解锁 PIN（仅本机联调，勿写进公开功能文档）：见 `.cursor/rules/odin-test-discipline.mdc`。

## 当前导航要点（手柄态）

标定摘要见 `docs/zh_cn/odin-nav-calib.json`；审查卡在 `review/cards/`。

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

注意：

- 勿用过小 Terminal 图标做「是否大世界」判断（标题页会误命中）。
- 进大世界后须先 `StartupSwitchPad`，再验手柄图标（禁止检查点抢在按 A 前结束任务）。
- 误进「活跃行迹」时优先走 `SolaGuidebookExtra`，不要当成功。

## 目录

```text
assets/
  interface.json          # 任务 / 控制器入口
  tasks/                  # 任务选项
  locales/                # 多语言
  resource/               # 推送到设备的资源镜像
  resource_adb/           # ADB 模板与 Pipeline（编辑主路径）
agent/
  go-service/             # CombatLoop / GamepadForwarder 等
docs/zh_cn/
  roadmap.md
  odin-nav-calib.json     # 奥丁导航坐标摘要
tools/touch-review/       # 截图 + 浏览器标注 → review/cards
review/
  inbox/                  # 待标注截图
  cards/                  # 已导出审查卡
```

## 联调速查

```bat
REM 截图（1280x720）
python tools\touch-review\capture.py --label pad-hud

REM 标注页 http://127.0.0.1:8765/
python tools\touch-review\serve.py

REM 推 PI 到奥丁上的 MaaWW（改 pipeline/image 后）
python tools\_push_pi_only.py
```

测完关屏：`adb shell input keyevent KEYCODE_SLEEP`。  
Git 推送：远程为 Cursor Origin，**只在 WSL** 用 `origin` 登录后 `git push`（见 `AGENTS.md`）。

## 许可

本仓库代码默认 **AGPL-3.0**（与 MaaFramework / MaaEnd / ok-ww 生态一致）。正式发版前会补齐 `LICENSE` 全文。
