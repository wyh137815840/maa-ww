# MaaFwApp overlays（本仓可提交）

`Android/MaaFwApp` 是指向外部 MaaFwApp 源码树的 junction，**不要**在外部树里直接改功能并当本仓改动。

需要改 MaaFwApp 行为时：

1. 把补丁源文件放在本目录（相对路径对齐 `app/src/main/java/...` 的包路径，见下）。
2. `tools/android-build-install.ps1` 在 gradle 前把 overlays **复制覆盖**进 `Android/MaaFwApp/...`。
3. git 只提交本仓 `Android/overlays/**`。

当前：

| 本仓路径 | 覆盖到 |
| --- | --- |
| `maafw/remote/internal/GamepadForwarder.kt` | `app/src/main/java/com/aliothmoon/maafw/remote/internal/GamepadForwarder.kt` |
| `maafw/remote/internal/StickCommand.kt` | `app/src/main/java/com/aliothmoon/maafw/remote/internal/StickCommand.kt` |

该 Forwarder 增加摇杆文件泵：周期性读 `/data/local/tmp/maaww_stick`，解析后注入 Xbox 节点（左摇杆 `ABS_X/ABS_Y`，右摇杆/镜头 `ABS_Z` 偏航、`ABS_RZ` 俯仰）。

**手柄关联（按需）**：把物理 Xbox 关联到虚拟屏是系统级状态（存在 InputManager，与 MaaWW 进程生死无关）。
为避免“跑过一次后，直接在主屏打开鸣潮手柄没反应”，Forwarder 只在有摇杆/按键注入时才关联虚拟屏，
空闲 6 秒还给主屏；还手柄 = 先关联到主屏（刷新 InputReader 缓存）再移除；服务启动时清遗留关联。
关联异常残留时手动救：`pwsh -NoProfile -File tools\pad-unbind.ps1`（需要 `MAAWW_ANDROID_BUILD` 指向工具链 ASCII 路径时设上）。
注意：游戏本身若还在虚拟屏上，要先停 MaaWW 的虚拟显示/把游戏拉回主屏，否则手柄回主屏也没有可控的游戏。

协议（单行，ABS 原始值 ±32767，Y 负=前进）：

- `lx ly holdMs`：仅左摇杆（旧版 agent 写这种）。
- `lx ly rx ry holdMs`：左摇杆 + 右摇杆（镜头）。`holdMs` 限幅 50–2000。

- **发布（生产端）**：先完整写 `maaww_stick.tmp` 再 `mv -f` 覆盖，保证原子。
  - `GOOS=android` 的 Go agent：本机 `os.WriteFile(tmp)` + `os.Rename`。
  - 电脑端 Go agent + ADB：只用 `Controller.PostShell`（`echo … > tmp && mv -f tmp live`），**禁止**在电脑上 `os.WriteFile`（会写到电脑磁盘）。失败就返回失败，不做本地兜底。
- **消费**：MaaFw 进程内 overlay 泵 rename 成 `.take` 再读并删；rename 失败本轮跳过，不读后截断。轴状态与到期时间独立保存，读取失败也按期回中。与 Go **不是同一进程**，写成功≠角色已移动。
- **镜头校准**：Go 参数 `yaw_full_ms` 是在 `yaw_deflect` 下转一整圈的时间，默认 3000 仅为猜测，必须在设备上实测后再启用 `aim_mode: "yaw"`。
路径常量：`/data/local/tmp/maaww_stick`（Go `stickCmdPath`）。
