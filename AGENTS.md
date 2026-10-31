# MaaWW AI Agent 编码指南

本项目基于 MaaFramework，工程规范对齐 MaaEnd；业务内容是《鸣潮》，功能对标 ok-ww。

## 首要准则

1. **禁止无界面信息编写 Pipeline**：缺少安卓截图、`roi`、模板与界面跳转时，只写占位并标注待补，不假装可跑。
2. **状态驱动**：识别 → 操作 → 再识别。优先 `pre_wait_freezes` / `post_wait_freezes` 与中间节点，避免硬 `delay`。
3. **分辨率基准**：坐标与图片一律按 **1280×720**。
4. **职责分离**：流程在 Pipeline JSON；复杂算法 / 战斗循环在 Go Service。
5. **第一期控制器**：只面向 **ADB（模拟器）**，资源放在 `assets/resource_adb/`。
6. **Git 推送**：远程为 Cursor Origin；**永远在 WSL 用 `origin` 登录后 `git push`**，禁止原生 Windows / PowerShell 直推。

## 关键路径

- 任务入口：`assets/interface.json`、`assets/tasks/`
- Pipeline：`assets/resource_adb/pipeline/`
- 模板图：`assets/resource_adb/image/`
- Go：`agent/go-service/`
- 功能清单：`FEATURES.md`
- 路线图：`docs/zh_cn/roadmap.md`

## 参考仓库（只读借鉴，勿混提 PR）

- 框架与工程：`D:\git\Maaend`（MaaEnd）
- 功能与战斗逻辑：`D:\git\ok-ww`（ok-ww）
