# 聚落（残象聚落 / 梦魇拔除）· ok-ww 方案分析与落地计划

> 来源：`D:\git\ok-ww\src\task\NightmareNestTask.py` + `BaseWWTask.py` / `BaseCombatTask.py`。
> 结论先行：**ok-ww 里的「聚落」就是 `NightmareNestTask`**。i18n 中 `Tacet Discord Nest = 残像聚落`、`Nightmare Purification = 梦魇拔除`，
> 对应手册「素材获取」里的两个页签。`settlement-quest-plan.md` 中「ok-ww 无同名任务」的说法不成立：
> 大世界任务栏「清理聚落中的残象」（SettlementQuest）才是 ok-ww 没有的另一件事，两者入口不同，不要混。

---

## 1. ok-ww 的完整流程

```text
run
 ├─ ensure_main                         # 在大世界且在队伍中
 ├─ _init_queue                         # 按配置排队：残象聚落(2 个滚动位) / 梦魇拔除(2 个滚动位)
 └─ while nest = get_nest_to_go():      # 每次重新开手册
        combat_nest(nest)
 └─ ensure_main
```

### 1.1 找目标（手册 → 页签 → OCR 计数）

1. `openF2Book("gray_book_boss")`：按手册键（F2），点「素材获取」标签。
2. `open_boss_book('canxiang' | 'mengyan')`：左侧列表固定比例点击（x=0.24；残象聚落 y=0.83，梦魇 y=0.86）。
3. 队列里每个页签有一个「向下滚动」变体（点右侧滚动条位置）以露出下半截列表。
4. `find_nest`：对右侧区域 (0.35,0.25)-(1,0.96) 做 OCR，匹配 `n/m`：
   - 只认**未完成**的：`n == 0` 且 `m ∈ {24, 36, 48, 41}`（每个聚落的残象总数）。
   - 点击点：同一行、x=0.9（行右侧「前往」按钮列）。
   - `cache_key = 页签:m:行槽位`，用于「本次不可达」和「死亡次数」去重。

### 1.2 进入聚落

点击后 `wait_feature` 四选一：

| 命中 | 含义 | 动作 |
| --- | --- | --- |
| `team_close` | 需要组队挑战的（实例化）聚落 | `click_team_challenge`（`team_start_challenge` + 跳过对话确认）→ 等进入队伍+世界(120s) |
| `fast_travel_custom` / `gray_teleport` / `remove_custom` | 可传送 | 点传送键 → 有确认框则点确认 → 等加载(120s)；按钮仍在 = 不可达，记入 `_unreachable_nests`，`back` |

传送落地后：

- `find_f_with_text` 有交互则按 F（逐个处理，最多等 40s 回世界）。**用户确认：残象聚落、梦魇拔除传送后都直接进入战斗，无需 F 触发；ok-ww 的这一步不要移植。**
- `run_until(in_combat, 'w', 10s, target=True)`：向前走并 `middle_click` 锁定，直到进入战斗。

### 1.3 战斗与收尾（核心）

```text
loop:
  combat_once(wait_combat_time=10, target=True)     # 等进战斗 → perform 循环 → 战斗结束
    ├─ 角色阵亡 CharRevivedException → 记死亡次数；≥3 次本轮放弃；否则回手册重进
    ├─ [捕获模式] 战斗中每帧 pick_f + 检测「声骸捕获」通知，成功即停
    ├─ sleep 3s
    ├─ walk_find_echo(5s, 回退 2.5s)                  # walk_until_f，目标文字 /吸收|Absorb/，找到则 pick_f
    │    └─ 失败 → yolo_find_echo(turn=True, 30s)     # 中键回正镜头 → YOLO 找声骸 → 对准/前进 → pick_f；转向 A 最多 4 次
    │         └─ 仍没拿到且非组队聚落 → 重新开手册传送回该聚落（面朝金色声骸群）再搜一次
    └─ wait_combat(3s) 若又进战斗 → 继续循环（wait_combat_time=1）
  结束：组队聚落 esc_world_confirm（Esc → 右按钮确认 → 回世界）
```

关键事实：

- **吸骸 = 交互键 F 且提示文字含「吸收/Absorb」**，不是拾取宝箱的普通 F。
- 声骸掉落位置不固定，ok-ww 用 **YOLO**（`find_echos`）定位；没有 YOLO 时只能「回退 + 前进 + 文字」的降级搜索。
- 吸骸后会弹「领取」类界面时用 `handle_claim_button`（Esc 关闭）。
- 无体力消耗；日刷「每个聚落 n/m」靠 OCR 计数判断是否已完成。

---

## 2. 对照 maa-ww 现状

| ok-ww 能力 | maa-ww 现状 | 缺口 |
| --- | --- | --- |
| 手册开页签、点行 | 有（`OpenGuidebook` / `GuidebookTacetTab` / `SelectTacetRow`，无音区用 OCR 选行） | 需新增「残象聚落」行与右侧列表节点 |
| OCR 计数 `n/m` 选未完成 | 无 | 新增（Pipeline OCR + Go 或 `expected` 正则） |
| 传送键 + 确认 + 不可达去重 | 无（无音区靠「前往」按钮） | 新增 + 缓存 key（Go 或任务选项） |
| 战斗循环 `CombatLoop` | **有**（exit_nodes / 死亡） | 需新 `exit_nodes`（无目标 / 声骸出现）、`wait_combat` 目标锁定 |
| 走近 / 搜索 / 视角扫视 | **有**（`WalkToTacetTreasure`：gate、搜索序列、右摇杆 yaw） | 需泛化成 `WalkToMarker`（目标换成「吸收」提示或声骸标） |
| 吸骸（F+「吸收」） | 无 | **新增 `AbsorbEcho`**：OCR/模板「吸收」→ B(Interact)；先降级版，不上 YOLO |
| 死亡复活 / 重进 | 部分 | 先只做「死亡 ≥ N 次放弃本聚落」 |
| 组队聚落入口 | 无 | 二期（`team_close` / `team_start_challenge` 需 UI 卡） |
| 退出聚落 | 无音区已有出本链路 | 组队型聚落复用「三横杠 → 确认离开」 |

### 手柄（奥丁）适配要点

- F → **B（Interact）**；中键回正镜头 → R3 / 右摇杆归中序列（ok-ww 的 `center_camera`）。
- ok-ww 的 `middle_click` 重新锁定在手柄上用「锁定键」或右摇杆扫视替代，已有 `scan_mode: camera` 可复用。
- 手册内点选仍用触屏（与无音区一致）；大世界移动/战斗/交互必须走手柄摇杆与按键，禁止触屏 Swipe 假摇杆。

---

## 3. 建议范围与顺序

**用户已确认：本期「残象聚落 + 梦魇拔除」一起做**（同一个 `NightmareNestTask` 流程，只是手册页签不同）。
实现顺序仍先打通「残象聚落」，再把页签/行 OCR/战斗配置参数化接入「梦魇拔除」；
组队聚落（`team_close`）放二期。梦魇拔除是大型 BOSS 战，战斗时长与阵亡处理要单独设上限。

```text
SettlementNestMain
  → EnsureWorld
  → OpenGuidebook → 素材获取 → 残象聚落页签
  → PickNest        # OCR n/m，选 n==0 的行；缓存不可达
  → TravelNest      # 传送键 → 确认 → 等加载；不可达则 back + 下一个
  → ApproachCombat  # 向前走，等进战斗（复用 CombatLoop 入口）
  → CombatLoop      # 复用；exit=无目标稳定 / 进度
  → AbsorbEcho      # 新：走近「吸收」F 提示 → B；搜索降级
  → NextNestOrDone  # 再开手册找下一个；全 n/m 完成则结束
```

### 分期

| 期 | 内容 | 前置 |
| --- | --- | --- |
| P0 界面情报 | 标齐：手册「残象聚落」页签与列表（含 `n/m`、前往列）、传送键与确认框、「吸收」提示（含位置）、战斗中 HUD | 奥丁截图（**无图不写可跑 Pipeline**） |
| P1 Pipeline 骨架 | `Settlement`/`Nest` 任务入口与节点，缺图的 `enabled:false` 并标注待补 | P0 |
| P2 Go | `AbsorbEcho`；`WalkToTacetTreasure` → `WalkToMarker`（保留旧名注册）；`CombatLoop` 新 exit 参数 | P0 部分 |
| P3 固化验收 | 奥丁上跑完整一个聚落：开手册 → 传送 → 战斗 → 吸骸 → 回到下一个/结束 | P1+P2 |

### 风险

| 风险 | 对策 |
| --- | --- |
| 声骸落点随机、无 YOLO | 降级：吸收文字提示 + 回退/前进/右摇杆环视（已有扫视序列）；记录成功率，不够再评估轻量检测 |
| `n/m` 的 m 取值随版本变 | 不写死 {24,36,48,41}：用「n 为 0 且 m≥1」并以 OCR 相对位置选行 |
| 列表需要滚动 | 与 ok-ww 一致用「页签 + 滚动」两种变体，先固定比例点击，P0 再标 |
| 手柄中键锁定缺失 | 沿用右摇杆扫视；必要时增加 Lock-on 键位 |
| 与「清理聚落中的残象」混淆 | 文档与任务名分开：`Nest`（手册）vs `SettlementQuest`（任务栏） |

---

## 4. 下一步需要用户确认 / 提供

1. 范围：先做「残象聚落」（本文建议）？还是同时要「梦魇拔除」？
2. P0 界面截图：在奥丁上手动打开手册 → 素材获取 → 残象聚落，并到一个聚落门口，我用 touch-review 逐张标注。
