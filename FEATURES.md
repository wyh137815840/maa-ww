# 功能对标清单（ok-ww → MaaWW）

来源：`ok-oldking/ok-wuthering-waves` 的 `src/task/`。  
状态：`todo` / `wip` / `done` / `wontfix`（PC 专属等）。

## 第一期（日常骨架 + 基础战斗）

| ok-ww 任务 | 说明 | 状态 |
| --- | --- | --- |
| SkipDialogTask | 跳过剧情对话 | todo |
| AutoPickTask | 自动拾取 | todo |
| AutoLoginTask | 自动登录 | todo |
| DailyTask | 日常一条龙骨架 | todo |
| AutoCombatTask | 自动战斗（先通用 BaseChar；专精角色后补） | wip |
| BaseCombatTask / BaseChar | 战斗与角色基类（移植为 Go `CombatLoop`） | wip |

## 优先推进（用户指定）

| 任务 | 对标 / 说明 | 状态 | 前置依赖 |
| --- | --- | --- | --- |
| TacetTask（无音区） | ok-ww `TacetTask`：手册 → 无音清剿 → **按序号/名称自动选行** → 开启挑战 → 本内战斗 → **走到宝藏** → 结算 | wip | 奥丁已验进本；本内 `CombatLoop`（手柄时序）已接；结算前需 `walk_to_treasure`（Pipeline 短步+宝藏标已接；完整环绕待 Go）；待：Go `SelectTacetRow`、5+、耗尽标志、实机验收 |
| SettlementQuest（聚落任务） | ok-ww 无同名任务；指聚落侧可自动任务流（接取/完成/交付）。界面卡待标 | todo | 大世界 HUD、聚落 NPC/任务 UI 卡；复杂战斗可后置 |

## 第二期（刷本 / 体力）

| ok-ww 任务 | 说明 | 状态 |
| --- | --- | --- |
| FarmEchoTask | 刷声骸 | todo |
| TacetTask / TacetEliminationTask | 无音区（见上「优先推进」） | todo |
| DomainTask | 副本 | todo |
| ForgeryTask | 伪作 | todo |
| SimulationTask | 模拟挑战 | todo |
| NightmareNestTask | 梦魇巢穴（图鉴传送与聚落相关） | todo |

## 第三期（声骸养成 / 周常）

| ok-ww 任务 | 说明 | 状态 |
| --- | --- | --- |
| MergeEchoTask | 合成废弃声骸 | todo |
| EnhanceEchoTask | 强化声骸 | todo |
| FiveToOneTask | 数据坞五合一 | todo |
| ChangeEchoTask | 换声骸 | todo |
| GardenTask | 周常乐园 | todo |

## 其他

| ok-ww 任务 | 说明 | 状态 |
| --- | --- | --- |
| FastTravelTask | 传送 | todo |
| CharacterCodeTask | 角色码 | todo |
| FarmMapTask | 地图相关 | todo |
| DiagnosisTask | 诊断 | todo |
| MultiAccountDailyTask | 多账号日常 | todo |
| MultiAccountConfigTask | 多账号配置 | todo |
| MouseResetTask | 防鼠标漂移 | wontfix（PC） |
| 后台静音等 | Windows 专属 | wontfix（PC） |
| 全角色战斗脚本（约 60） | 在基础战斗稳定后逐个移植 | todo |
