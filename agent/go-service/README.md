# go-service

复杂识别与操作（尤其是自动战斗）放这里，由 Pipeline 通过 Custom Recognition / Action 调用。

## CombatLoop（MVP）

- CustomAction 名：`CombatLoop`
- 行为：对标 ok-ww `BaseChar.do_perform` 的时序输出（Echo → Liberation → Resonance → Attack → Heavy → Swap）
- 输入：手柄键码（见 `docs/zh_cn/ww-input-map.json`），经 `PostClickKey` / `KeyDown`+`KeyUp` 注入
- 在战判定：Pipeline `CombatHasTarget` / `CombatEnemyHP`（对齐 ok-ww 准星+红血条）；无目标则 R3 重锁
- 退出：不在战（重锁失败）→ 交给宝藏节点；或 `exit_nodes`（宝藏/结算）；或 `max_duration_ms`

### 队伍识别与角色（`combat/team.go`）

- 数据源：战斗 HUD **右侧竖排 3 个头像**（不依赖队伍界面）。头像模板在 `combat/teamdata/*.png`（`go:embed`），角色定位表 `charRoles`（绯雪 主C / 洛瑟菈 副C / 穗穗 奶妈）。
- `readTeam`：模板匹配认人，血条亮度判存活，当前出场角色看蓝色角标；整排变暗（过场）时沿用上一帧的名单，避免误判全员阵亡。
- 队友阵亡后 `nextAlive` 跳过他，切人不再切到阵亡者；若误切出「选择复苏物品」框，`CombatLoop` 每轮检测并按 A 关闭（**绝不确认**，不消耗复苏道具）。
- 测试：`go test ./combat/`（`testdata/hud_alive.png`、`hud_dead.png`）。尚未做：技能 CD / 能量 / 协奏识别、各角色专属输出循环、战后复活。

### 聚落动作

| CustomAction | 作用 |
| --- | --- |
| `NestKinds` | 聚落任务入口 `NestRun`：按选项 `NestKind`（可多选）依次对残象聚落 / 梦魇祛除各跑一遍 `NestMain` |
| `NestApproach` | 传送落地后左摇杆向前走，直到任务栏「清剿残象聚落」出现（默认上限 15 s） |
| `NestAbsorbSearch` | 清剿后没有「吸收」提示时转镜头 + 前进搜声骸（**实机仍搜不到，待用调试帧排查**） |

调试帧：`combat/debug_frame.go` 的 `dumpDebugFrame` 把当前帧写到 go-service.log 旁的 `frames/` 目录（上限 40 张，`MAAWW_AGENT_LOG_DIR` 可改），游戏在虚拟屏上时 ADB `screencap` 截不到，靠它和 `files/log/on_error/*.png` 看画面。

## 多账号（`account/`）

| CustomAction | 作用 |
| --- | --- |
| `AccountLoop` | 解析手机号列表（`ParsePhones`：全号或后四位，逗号/分号/空格分隔，后四位重复只留第一个）→ 每个账号：`AccountEnsureGame` → `AccountSwitchMain`（override 目标后四位到 `AccountCurrentIsTarget` / `AccountPickRow`）→ 依次跑勾选的任务（聚落 → 无音区 → 日常）。切号失败的账号整个跳过，所有账号都失败才判任务失败 |
| `AccountHoldKey` | 长按一个手柄键（终端页长按 Start=108 弹出「是否确定退出游戏？」） |
| `AccountFail` | 恒返回 false，让切号分支以失败结束 |

**任务选项约定（踩过的坑）：**

- 同一节点字段上的多个 `pipeline_override` 是**整体替换，不是深合并**。`AccountPhones` 输入选项会把 `AccountLoopMain` 的 `custom_action_param` 整个换成 `{"phones": "..."}`，所以任务列表、入口名等默认值写在 Go（`defaultTasks`），不要写在这个 param 里。
- 复选框（`AccountTasks`、`NestKind`）每个 case 改**各自的开关节点**（`AccountTaskDaily`、`NestKindCanxiang` ……）的 `attach.on`，Go 用 `ctx.GetNode(name).Attach["on"]` 读取。**不要**靠覆盖 `enabled` 再用 `GetNodeJSON` 读，实测读不到。
- 子任务选项（无音区序号等）是任务级 override，`ctx.RunTask` 会继承，所以 `MultiAccount` 里一并列出这些选项即可。

## 分辨率（奥丁 / ADB）

资源与 Pipeline 坐标固定 **1280×720**。控制器创建并 `Connect` 成功后必须：

```go
ctrl.SetScreenshotTargetLongSide(1280) // 或 ShortSide(720)，16:9 等价
```

真机可为 1920×1080；框架缩放截图并映回点击。见 `docs/zh_cn/resolution-scaling.md`。

## 构建（Android arm64）

```bash
python tools/build_android_agents.py
```

产出：`Android/agent-dist/arm64-v8a/jniLibs/libgo-service.so`

通常直接用 `pwsh -NoProfile -File tools\android-build-install.ps1`，它会重编 agent、复制 `Android/overlays`、出包并装到设备。离线机器上跑 `go` 需要模块缓存：设 `GOMODCACHE` 指向已有缓存、`GOPROXY=off`。

Go 代码改完要跑：`gofmt -l .`（`combat/gamepad.go`、`walk_to_treasure.go` 有历史格式问题，别顺手改）、`go vet ./...`、`go test ./combat/ ./account/`。
