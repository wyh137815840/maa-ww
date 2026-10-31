# MaaWW

基于 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 的《鸣潮》自动化项目。

- **框架**：对齐 [MaaEnd](https://github.com/MaaEnd/MaaEnd) 的工程分层（Pipeline 管流程，Go 管难点，ADB 资源分离）
- **功能对标**：[ok-ww](https://github.com/ok-oldking/ok-wuthering-waves)（ok-script / PC）
- **首期目标**：安卓模拟器 ADB — 日常骨架 + 基础自动战斗

## 状态

脚手架阶段。资源与任务将按 `docs/zh_cn/roadmap.md` 与 `FEATURES.md` 增量落地。

## 运行环境（计划）

| 项 | 要求 |
| --- | --- |
| 控制器 | ADB（模拟器） |
| 分辨率 | **1280×720**，16:9 |
| 推荐模拟器 | **MuMu 模拟器**（次选雷电 9） |

模拟器安装完成后，用 `adb devices` 确认设备在线即可联调。

## 目录（规划）

```text
assets/
  interface.json          # 任务 / 控制器入口
  tasks/                  # 任务选项
  locales/                # 多语言
  resource/               # 基准资源（预留）
  resource_adb/           # ADB 模板与 Pipeline
agent/
  go-service/             # 复杂识别 / 战斗等自定义逻辑
docs/
```

## 许可

本仓库代码默认 **AGPL-3.0**（与 MaaFramework / MaaEnd / ok-ww 生态一致）。正式发版前会补齐 `LICENSE` 全文。
