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

该 Forwarder 增加摇杆文件泵：周期性读 `/data/local/tmp/maaww_stick`（单行 `x y hold_ms`），解析后注入左摇杆。

- **写入**：Go agent（`WalkToTacetTreasure` / `pulseStick`）用 `os.WriteFile` 写该文件（常见为 app/agent 子进程 uid，权限靠 `0666`；**不要**依赖 `Controller.PostShell`——AndroidNativeController 不支持 Shell）。
- **消费**：MaaFw 进程内 overlay `GamepadForwarder` 文件泵读取并 `injectAxis`；与 Go **不是同一进程**，WriteFile 成功≠角色已移动。

路径常量：`/data/local/tmp/maaww_stick`（Go `stickCmdPath`）。
