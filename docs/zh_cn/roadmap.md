# 路线图

## 原则

1. **Pipeline 管流程，Go 管难点**：日常跳转与点击用 JSON；战斗循环、角色识别等进 `agent/go-service`。
2. **先有截图再写节点**：每个识别节点需要 **1280×720** 基准截图、`roi`、界面跳转说明（真机 1080p 由框架缩放到 720p）。
3. **功能对标 ok-ww，运行时对标 MaaEnd**：行为对齐 ok-ww，工程与控制器对齐 MaaFramework / MaaEnd。
4. **第一期 ADB 真机（Odin 3 WiFi）**：弃用模拟器联调；不优先 Win32。

## 里程碑

### M0 — 脚手架

- [x] 独立仓库与目录骨架
- [x] `interface.json`（仅 ADB）
- [x] 功能对标表 `FEATURES.md`
- [x] 模拟器 ADB 联通（历史）；现主路径 **Odin 3 WiFi**
- [x] 触屏审查工具 `tools/touch-review/`
- [x] 设备 PI 热推 `tools/_push_pi_only.py`

### M1 — 启动与场景（当前迭代）

- [x] 标题页「点击连接」（模板 + OCR）
- [x] 大世界小地图 / Terminal；**切手柄**（A×3 + PadReady「地图」检查点）
- [x] 手柄态 Terminal → 索拉指南 → Extra 双剑 → Opened 验证
- [ ] 场景识别：菜单 / 战斗中 / 对话中（通用）
- [ ] 跳过剧情、自动拾取
- [ ] 节点测试截图目录约定

### M2 — 日常骨架

- [x] 活跃行迹领取（`Daily` P1：点领取 → 100 按 Y 领宝箱 → 关弹窗 → 离开手册；成功路径待日常刷新后实测）
- [ ] 刷体力 / 邮件 / 战令等其余日常步骤
- [ ] Daily 任务入口与阶段切换
- [ ] 可配置跳过子步骤（对标 ok-ww 日常选项）

### M3 — 基础自动战斗

- [x] Go：`CombatLoop` 自定义动作（手柄时序 MVP，对标 `BaseChar.do_perform`）
- [x] HUD 右侧 3 头像识别队伍、阵亡检测、切人跳过阵亡队友、误弹「选择复苏物品」自动 A 关闭（`combat/team.go`）
- [ ] 先支持 1～2 个常用角色，再扩全角色表（绯雪 / 洛瑟菈 / 穗穗 专属循环；技能 CD / 能量 / 协奏识别需用户标 ROI）
- [ ] 战后复活队友（是否消耗复苏道具待定）

### M4 — 无音区 / 聚落（优先）

- [x] 大世界打开导能手册（审查卡 OpenGuidebook；安卓顶栏图标）
- [x] 手册「无音清剿」页签（审查卡 GuidebookTacetTab）
- [x] 列表「直接挑战」按钮模板（审查卡 TacetGoButton；多副本共用按钮，选行另做）
- [x] 编队页「开启挑战」（审查卡 TacetStartChallenge）
- [x] 本内战斗识别 InTacetCombat（目标条「清理无音区…」）
- [x] **无音区首屏 1–4 选行验收**（奥丁：直点「直接挑战」进编队页；见 `tacet-accept-1to4.json`）
- [ ] **多无音区自动选行（5+ / Go）**（设计已定；Python swipe 原型有；**Go `SelectTacetRow` 待接**）
- [x] 挑战达成识别 / 领取奖励提示 / 双倍领取（120 白字优先）
- [x] 单倍领取回退 / 双红耗尽关窗（TacetStaminaExhausted）/ 再次挑战 / 退出副本
- [x] **走到宝藏再领奖**（对齐 ok-ww `walk_to_treasure`；Go `WalkToTacetTreasure` 左摇杆+ B；旧触屏 Swipe 假摇杆已禁用）
- [ ] 跨任务「体力耗尽」标志：跳过后续一切耗体力任务（Interface/Go）
- [ ] 吸声骸（若与领取奖励分流）
- [x] Go：本内 AutoCombat 循环骨架（`CombatLoop`；实机验收中）
- [x] ADB 优先截 `mumuscreen001`（桥接可用 `192.168.1.50:5555`）
- [x] 聚落（`Nest`）：手册选未完成行（n≠m）→ 快速旅行 / 直接挑战 → `NestApproach` 走近 → 战斗 → 吸收；残象聚落 / 梦魇祛除**可多选**（`NestRun` + Go `NestKinds`）
- [ ] 梦魇祛除战斗 HUD 与流程验证；`NestAbsorbSearch` 实机搜不到声骸，需用调试帧排查；`NestAllDone` 还没关手册
- [ ] 聚落任务（接取 → 完成条件 → 交付，见 `settlement-quest-plan.md`；先标 UI）
- [ ] 基础战斗可跑通至少 1 轮无音区（`CombatLoop` 实机验收）

### M4.5 — 多账号

- [x] 任务选项 `AccountPhones`（手机号 / 后四位）+ 复选框 `AccountTasks`
- [x] Go `account.LoopAction`：逐账号切号再跑勾选任务（聚落 → 无音区 → 日常）
- [x] 切号流水线（终端长按 Start → 返回登录 → 登录页下拉按后四位选号 → 启动等待链），奥丁实测两账号通过
- [ ] 聚落 / 无音区放进循环后的整轮实跑
- [ ] 当前账号已是目标时跳过重新登录
- [ ] 标题页「登入」「账号」入口（目前只处理大世界 / 登录页 / 黑屏）

### M5+ — 刷本与声骸

- 见 `FEATURES.md` 第二期、第三期
