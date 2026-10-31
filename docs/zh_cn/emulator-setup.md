# 模拟器联调说明（MuMu）

## 已确认环境

| 项 | 值 |
| --- | --- |
| 模拟器 | MuMu Player 12 |
| ADB | `D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe` |
| 常用端口 | `127.0.0.1:16384`（MuMu 主实例常见）、`127.0.0.1:5555` |

## 连接命令

```bat
"D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe" connect 127.0.0.1:16384
"D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe" devices -l
```

分辨率请设为 **1280×720（16:9）**。可用：

```bat
adb -s 127.0.0.1:16384 shell wm size
adb -s 127.0.0.1:16384 shell wm size 1280x720
```

## 分辨率注意

联调时设备报告：

- 物理尺寸常为竖屏 `720x1280`
- 可用 `adb shell wm size 1280x720` 临时覆盖为横屏

更稳妥的做法是在 **MuMu 多开器 → 该实例设置 → 显示** 里直接选平板 / 横屏 **1280×720（16:9）**，再重启实例，避免只靠临时 override。

当前机器上还可能连着真机（如 `Odin3`）。自动化请固定用模拟器序列号，例如 `127.0.0.1:16384`，不要用手机。

## 当前状态

鸣潮仍在下载资源时，只做 ADB / 分辨率联调；进入游戏主界面后再截图写 Pipeline。
