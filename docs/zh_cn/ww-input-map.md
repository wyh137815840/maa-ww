# 鸣潮输入映射（Xbox 手柄 ↔ PC 键鼠）

用于安卓端战斗：ok-ww / PC 逻辑动作 → 奥丁手柄键（或等价 KeyEvent），**不必点屏幕技能钮**。  
菜单 / 无音选本仍走 Pipeline 识图点击。

来源：用户提供（2026-11-01）。

| 功能 | Xbox | PC 键鼠 | 逻辑动作名（建议） |
| --- | --- | --- | --- |
| 移动 | 左摇杆 | WASD | `Move` |
| 视角 | 右摇杆 | 鼠标 | `Look` |
| 普攻 / 长按重击 | **X** | 左键 | `Attack` / `HeavyAttack` |
| 闪避 / 疾跑 | **RB** | 右键 / 左 Shift | `Dodge` / `Sprint` |
| 跳跃 | **A** | Space | `Jump` |
| 共鸣技能 | **Y** | E | `ResonanceSkill` |
| 共鸣解放 | **RT** | R | `Liberation` |
| 声骸技能 | **LT** | Q | `EchoSkill` |
| 探索工具 | **LB + Y** | T | `Tool` |
| 瞄准切换 | **LB + X** | G | `AimToggle` |
| 交互 / 拾取 | **B** | F | `Interact` |
| 攀爬下落 | **X** | X | `ClimbDrop` |
| 切人 1 / 2 / 3 | 十字 **上 / 右 / 下** | 1 / 2 / 3 | `Swap1` / `Swap2` / `Swap3` |
| 切人 4 | **LB + 十字下** | 4 | `Swap4` |
| 快捷轮盘 | 十字 **左** | Tab | `Wheel` |
| 锁定 / 长按取消 | **R3** 点按 / 长按 | 滚轮点按 / 长按 | `Lock` / `LockCancel` |
| 任务追踪 | **LB + R3** | V | `QuestTrack` |
| 组合键主键 | **LB** | — | `ModifierLB` |
| 终端 / 设置 | **Menu** | Esc | `Menu` |
| 决定 / 取消 | **A / B** | — | `Confirm` / `Cancel` |
| 聊天（长按） | **View** | Enter | `Chat` |

## 实现约定

1. Go / 战斗循环只发**逻辑动作名**；平台层查本表发手柄或键鼠。
2. 组合键：`LB` 为修饰键，先按下修饰再点副键，再按序抬起。
3. 长按：`Attack` 长按 = 重击；`R3` 长按 = 取消锁定；`View` 长按 = 聊天。
4. 进游戏后切一次控制器模式并保持。登录页按键不会弹出切换询问。控制器模式下屏幕点击仍然有效，手册、选本、结算继续用 Pipeline 识图点击。点屏幕不会切回触屏。
5. 后台模式时游戏在虚拟屏上，实体手柄仍跟主屏焦点，不会自己跟过去。任务里的按键用 `input gamepad -d <游戏所在 displayId>`（`tools/touch-review/maaww_pad.sh`）。切控制器模式的那一下 A 仍写 Xbox 设备节点，且只在游戏位于主屏时才会弹出询问。

机器可读副本：`docs/zh_cn/ww-input-map.json`。
