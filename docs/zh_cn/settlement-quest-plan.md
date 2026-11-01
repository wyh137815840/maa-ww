# 聚落整套流程 · 落地方案

> 目标：奥丁手柄 + ADB 固化跑通「清理聚落中的残象」类日常（接取 → 前往 → 清残象 → 吸声骸 → 交付/领奖）。  
> 对标：`FEATURES.md` → SettlementQuest；`roadmap` M4「聚落任务」。  
> **不**等于手册「残象聚落」刷本页（无体力声骸场）；二者可后续复用战斗/吸骸，入口不同。

---

## 0. 范围裁定

| 名称 | 是什么 | 本期 |
| --- | --- | --- |
| **聚落任务 / SettlementQuest** | 大世界任务栏常见「清理聚落中的残象」；到点清怪 → 交互/吸骸 → 任务完成 | **主交付** |
| 手册「残象聚落」 | 素材获取页签；普通/高难；日刷、**不耗波片** | 二期复用战斗，入口另开 |
| 梦魇巢穴 NightmareNest | ok-ww 有完整任务；图鉴传送+金色声骸 | 三期；与聚落传送相关但独立 |

审查卡已见任务栏文案：`20261031-182324-openguidebook` note「清理聚落中的残象」。

---

## 1. 端到端状态机（主流程）

```text
Startup(PadReady)
  → SettlementMain
      → EnsureWorldHUD          # 小地图 / Terminal；若在副本先出本（复用 Startup 出本）
      → DetectQuestTrack        # 左栏 OCR「清理聚落|消灭残象|残象」
      → [无追踪] AcceptDaily    # 日常面板接取（待标 UI）或跳过已接
      → TrackQuest              # LB+R3 / 点追踪（待标）
      → NavigateToSite          # 走近（Go 摇杆，对齐 WalkToTacetTreasure）
      → ClearResiduals          # CombatLoop（exit=任务进度满 / 无目标）
      → AbsorbEchoes            # 吸声骸（B / 模板；可与领奖分流）
      → TurnInOrComplete        # 交付 NPC 或自动完成弹窗
      → SettlementDone
```

原则（与无音区一致）：

1. **状态驱动**：识别 → 操作 → 再识别；禁止硬长 `delay`。
2. **流程在 Pipeline**；移动/战斗在 **Go**。
3. **坐标 1280×720**；真机截图缩到长边 1280。
4. **手柄**：移动/战斗/交互用键与摇杆；菜单/日常面板可点屏。
5. **禁止**用触屏 Swipe 假摇杆走近（已在无音区踩坑）。

---

## 2. 与无音区（Tacet）复用 / 差异

| 能力 | 无音区 | 聚落 | 动作 |
| --- | --- | --- | --- |
| Startup + PadReady | ✓ | ✓ | 直接复用 |
| 副本软恢复出本 | ✓ | ✓ | 复用三横杠 / 出门 |
| 手册进本选行 | ✓ | ✗（大世界任务） | 不复用 |
| `CombatLoop` | ✓ | ✓ | 复用；换 `exit_nodes` / HUD OCR |
| `WalkToTacetTreasure` | 宝藏标 | 任务点 / 声骸光 | **抽通用** `WalkToMarker` 或参数化节点名 |
| 领取奖励体力窗 | ✓ | 通常无 | 聚落不接双倍窗 |
| 吸声骸 | 待做 | **刚需** | 本期必做 |
| 退出副本 | ✓ | 多数在大世界 | 仅异常入本时出本 |

---

## 3. 分期落地（建议 4 刀）

### P0 — 界面情报（阻塞编码）

**无截图不写可跑 Pipeline**（`AGENTS.md`）。用 touch-review 在奥丁标齐：

| 卡 ID（建议） | 界面 | 要点 |
| --- | --- | --- |
| `SettlementQuestTrack` | 大世界左栏 | OCR/ROI「清理聚落中的残象」「消灭残象」；进度 `n/m` |
| `SettlementAccept` | 日常/任务接取 | 接取按钮；已接则跳过 |
| `SettlementTrackBtn` | 追踪 | 点追踪或确认 `LB+R3` 生效表现 |
| `SettlementArrive` | 抵达 | 交互「交谈/挑战」或残象刷新 UI |
| `SettlementInCombat` | 清怪中 | 左栏进度变化；可与 `CombatHasTarget` 并用 |
| `SettlementAbsorb` | 声骸 | 地上声骸光 / 「吸收」提示 + B |
| `SettlementComplete` | 完成 | 「任务完成」/ 交付 / 领奖弹窗 |

产出：`review/cards/*` + `assets/resource_adb/image/Settlement/` + 审查备注坐标。

### P1 — Pipeline 骨架（可跑占位）

新建：

- `assets/tasks/Settlement.json`（任务入口）
- `assets/resource_adb/pipeline/Settlement.json`
- `assets/interface.json` 挂任务

节点最小集（缺图的标 `enabled:false` + desc「待补」）：

```text
SettlementMain
SettlementEnsureWorld
SettlementQuestOCR          # 有追踪 → Navigate
SettlementAcceptDaily       # 占位
SettlementNavigate          # Custom WalkToMarker
SettlementCombat            # Custom CombatLoop
SettlementAbsorbEcho        # Custom 或 ClickKey B 循环
SettlementCompleteUI
SettlementDone
```

`interface` 选项（对标日常可配）：

- 跳过接取（已接）
- 最大战斗时长
- 吸骸次数 / 超时
- 完成后是否回城（暂不做）

### P2 — Go 能力

| CustomAction | 说明 |
| --- | --- |
| 复用 `CombatLoop` | `exit_nodes`: 任务完成 OCR、进度满、无目标超时；`hud_node`: `SettlementInCombat` |
| 泛化 `WalkToMarker` | 从 `WalkToTacetTreasure` 抽出：参数 `treasure_nodes` / `claim_nodes` → `marker_nodes` / `arrive_nodes`；左摇杆 + 可选 B |
| `AbsorbEcho`（新） | 环视找声骸标 → 走近 → B；超时返回；对齐 ok-ww `pick_echo` / yolo 的降级版（先模板/OCR，不上 YOLO） |

手柄映射已有：`Interact=B`，`QuestTrack=LB+R3`（`ww-input-map`）。

### P3 — 奥丁固化验收

1. Startup → PadReady。  
2. 左栏已有「清理聚落…」时：追踪 → 走到 → 清光 → 吸骸 → 完成。  
3. 无追踪：接取日常后再跑（P0 卡齐后）。  
4. 中途掉进副本：出本再继续（复用 Startup 出本节点）。  
5. 测完 `KEYCODE_SLEEP`。

通过标准：任务进度从 `n/m` → 完成弹窗或追踪消失；日志可见 `CombatLoop` / `WalkToMarker` / `AbsorbEcho` 交接，无「站着不动」式 Swipe 环。

---

## 4. 目录与命名

```text
assets/tasks/Settlement.json
assets/resource_adb/pipeline/Settlement.json
assets/resource_adb/image/Settlement/
  QuestTrack.png / AbsorbHint.png / Complete.png ...
agent/go-service/combat/
  walk_to_treasure.go   → 抽 walk_to_marker.go（兼容旧名注册）
  absorb_echo.go        # 新
docs/zh_cn/settlement-quest-plan.md  # 本文件
```

FEATURES 状态流转：`todo` → P0 标卡后 `wip` → P3 验收 `done`。

---

## 5. 风险与对策

| 风险 | 对策 |
| --- | --- |
| 聚落点位分散、需传送 | P1 只支持「已在附近 / 追踪可指引」；传送进 `FastTravel` 二期 |
| 任务文案多版本 | OCR 多 expected：`清理聚落\|消灭残象\|残象` |
| 战斗误判结束 | 出战条件与无音区相同；exit 加「进度数字不再增加」超时 |
| 吸骸与领奖 UI 混淆 | 独立节点；禁止走 Tacet 双倍体力窗 |
| 手柄摇杆注入依赖 GamepadForwarder | 固化任务内验证；失败则日志 + 显示屏定向 fallback 仅用于**视角** |
| 与「残象聚落」手册混淆 | 入口禁止点手册该页签；文档与任务名用 SettlementQuest |

---

## 6. 建议排期（相对无音区收尾）

1. **现在**：无音区实机验收 `WalkToTacetTreasure` + 领奖稳定（聚落移动复用其结果）。  
2. **并行 P0**：奥丁标齐上表 7 张卡（可先 QuestTrack + InCombat + Absorb + Complete）。  
3. **P1**：Settlement Pipeline 骨架 + 任务入口（占位可提交）。  
4. **P2**：`WalkToMarker` 泛化 + `AbsorbEcho` + CombatLoop 参数。  
5. **P3**：固化跑通 1 条完整聚落日常。  
6. **之后**：手册「残象聚落」入口（复用战斗/吸骸）；NightmareNest。

---

## 7. 明确不做（本期）

- 全图自动寻路 / 多聚落巡回列表  
- 残象聚落普通/高难选层与日刷计数  
- 梦魇巢穴金色声骸 YOLO  
- Daily 一条龙编排（只预留 Settlement 可被 Daily 调用）
