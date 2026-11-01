<!-- markdownlint-disable MD033 MD041 -->
<div align="center">

# MaaWW

<!-- prettier-ignore-start -->
<!-- markdownlint-disable-next-line MD036 -->
_🌊 MAA 鸣潮小助手 · 安卓手柄真机版 🌊_
<!-- prettier-ignore-end -->

[![Pipeline](https://img.shields.io/badge/Pipeline-%23876f69?logo=paddypower&logoColor=%23FFFFFF)](https://github.com/MaaXYZ/MaaFramework)
[![Go](https://img.shields.io/badge/Go-007d9c?logo=go)](agent/go-service)
[![platform](https://img.shields.io/badge/platform-Android%20(ADB)-blueviolet)](#-运行环境)
[![resolution](https://img.shields.io/badge/resolution-1280%C3%97720-green)](docs/zh_cn/resolution-scaling.md)
[![license](https://img.shields.io/badge/license-AGPL--3.0-blue)](#-许可)

基于 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 的《鸣潮》自动化项目 · 工程规范对齐 [MaaEnd](https://github.com/MaaEnd/MaaEnd) · 功能对标 [ok-ww](https://github.com/ok-oldking/ok-wuthering-waves)

绝赞开发中 🚧……首期只面向安卓 ADB，联调主力是 **AYN Odin 3（WiFi ADB）**

</div>

## ⚠️ 免责声明

本项目为外部辅助工具，通过截图识别与模拟输入（ADB 触控 / 手柄按键）与游戏交互，**不读取内存、不修改任何游戏文件或数据**。开源、免费，仅供个人学习与交流，请勿用于商业或营利用途。

请注意库洛官方《鸣潮》公平运营声明：严禁利用第三方工具破坏游戏体验，对外挂、宏脚本、自动挂机等违规行为将视情况扣除收益乃至封禁账号。**使用本项目即表示你已阅读、理解并自愿承担一切潜在风险**，因使用产生的任何问题与本项目及开发者无关。

## 📖 使用须知

这是一个**正在快速迭代**的项目，部分任务仍是骨架或只在特定设备上联调过 🐛。各任务的成熟度见下方「功能一览」与 [`FEATURES.md`](FEATURES.md)，路线图见 [`docs/zh_cn/roadmap.md`](docs/zh_cn/roadmap.md)。

> 💡 **提示**：目前没有打包好的发行版，需要自行把 Android 端 App 与资源装到设备上，步骤见 [开发者文档](docs/zh_cn/developers/README.md)。

## 🧰 运行环境

| 项 | 要求 |
| --- | --- |
| 控制器 | ADB（真机优先，模拟器不再是主路径） |
| 分辨率 | 以 **1280×720**（16:9）为基准；真机 1080p 由框架缩放到 720p 识别，点击自动映回，无需另行适配 |
| 联调设备 | AYN Odin 3（WiFi ADB） |
| 手柄 | 进大世界后切到控制器模式；战斗走 Go `CombatLoop` 的手柄时序 |
| 游戏 | 《鸣潮》安卓客户端 |

## ✨ 功能一览

| 任务 | 说明 | 状态 |
| --- | --- | --- |
| 🚀 **启动进游戏**（`Startup`） | 冷拉起 → 标题「点击连接」→ 等进大世界 → 按物理 Xbox A 切手柄（最多 3 次）→ 认到手柄 HUD 才算成功 | 奥丁联调中 |
| 🔇 **无音区**（`Tacet`） | 手册 → 索拉指南 → 无音清剿 → 选行 / 开启挑战 → 战斗 → 结算 | 选行与进本已验，战斗与结算骨架 |
| 🏚️ **聚落**（`Nest`） | 残象聚落 / 梦魇祛除（**可多选，勾几个跑几个**）→ OCR 选未完成行 → 快速旅行 / 直接挑战 → 战斗 → 吸收声骸 → 下一个 | 残象聚落已联调；梦魇战斗 HUD 未验证 |
| 🎁 **日常奖励**（`Daily`） | 手册 → 活跃行迹：一键领取 → 活跃度 100 按 Y 领宝箱 → 关弹窗离开 | P1，待日常刷新后实测 |
| 👥 **多账号轮跑**（`MultiAccount`） | 填手机号（可只填后四位），逐个切号，每个账号按 聚落 → 无音区 → 日常 跑勾选的任务 | 两账号切号已在奥丁实测 |
| ⚔️ **自动战斗**（Go `CombatLoop`） | HUD 识别队伍、跳过阵亡队友、手柄时序出招 | 基础版；冷却 / 能量 / 连携感知与专精角色待做 |
| 💬 **跳过剧情**（`SkipDialog`） | — | 占位，缺截图 |

### 多账号怎么用

1. 在任务列表里选「多账号轮跑」。
2. **手机号** 栏填需要轮跑的账号，逗号 / 分号 / 空格分隔均可；只填后四位也行（后四位须互不相同）。
3. 勾选每个账号要跑的任务（默认聚落、无音区、日常全选；日常固定最后跑），按需设置聚落类型和无音区序号——这些选项对所有账号生效。
4. 某个账号切号失败会被跳过，所有账号都失败才算整个任务失败。

> 手机号只存在你设备上的任务配置里，不会写进仓库。

## 🔧 疑难解答

提问前请先按下面几步排查：

1. **分辨率**：设备可以是 1080p 等 16:9 分辨率，但务必保持横屏；竖屏会让坐标映射错位、点到别处。
2. **手柄模式**：游戏需处于手柄 / 控制器操作界面（启动任务会尝试切换）；触屏态下多个界面入口不一样。
3. **画面干扰**：关闭会遮挡游戏画面的悬浮窗、护眼 / 滤镜类应用，使用默认亮度。
4. **自动奔跑 / 按键**：游戏里关闭自动奔跑；不要改动默认手柄键位。
5. **队伍**：队伍里每个角色都要装备主声骸，否则自动战斗可能反复锁定而不出招。
6. **怎么看日志**：App 界面常被截成旧画面，判断状态以日志为准——`files/log/maafw.log`、`files/pi/debug/go-service.log`，失败截图在 `files/log/on_error/`。
7. 仍无法解决：提 Issue，附上日志与失败截图（**先抹掉手机号、UID 等个人信息**）。

## 🛠️ 开发者指南

想参与开发或在真机上联调？👉 [开发者文档](docs/zh_cn/developers/README.md)

- 工程准则：[`AGENTS.md`](AGENTS.md)（状态驱动、1280×720、Pipeline 管流程、Go 管难点）
- Go Service：[`agent/go-service/README.md`](agent/go-service/README.md)
- 功能清单：[`FEATURES.md`](FEATURES.md) · 路线图：[`docs/zh_cn/roadmap.md`](docs/zh_cn/roadmap.md)

```text
assets/        interface.json、任务选项、Pipeline 与模板（resource_adb 为编辑主路径）
agent/         Go Service：战斗循环、聚落、多账号
Android/       覆盖到 MaaFwApp 的补丁（手柄转发 / 摇杆泵）
docs/zh_cn/    路线图、标定数据、设计文档
tools/         联调脚本、截图标注工具
```

提交前请运行 `python tools\check_secrets.py`，确认没有把本机 PIN、序列号、手机号带进仓库。

## 🙏 致谢

- [MaaFramework](https://github.com/MaaXYZ/MaaFramework)：自动化框架
- [MaaEnd](https://github.com/MaaEnd/MaaEnd)：工程分层与规范的参照
- [MaaFwApp](https://github.com/Aliothmoon/MaaFwApp)：安卓端运行载体
- [ok-ww](https://github.com/ok-oldking/ok-wuthering-waves)：功能与战斗逻辑的对标来源

## 📄 许可

本仓库代码默认 **AGPL-3.0**（与 MaaFramework / MaaEnd / ok-ww 生态一致）。正式发版前会补齐 `LICENSE` 全文。
