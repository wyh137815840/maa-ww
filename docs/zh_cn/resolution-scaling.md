# 分辨率：720p 资源 + 真机自动缩放

## 结论

**奥丁 3 跑 1080p 不必重标模板。**  
Pipeline / 模板 / `roi` / `target` 继续按 **1280×720**。运行时让 MaaFramework 把截图缩到该基准再识别，点击坐标再映回设备像素。

## MaaEnd 里实际有两套「720」

| 机制 | 适用 | 做什么 |
| --- | --- | --- |
| Win32 比例检查 / 改窗口 | PC 客户端 | 非 16:9 时可能把**游戏窗口**调到接近 1280×720（真改窗口，不是截图缩放） |
| `SetScreenshotTargetLongSide(1280)` | Win32 **与** ADB | **只缩放截图**用于识别；触控由框架换算回原始分辨率 |

ADB / 奥丁走的是第二种。MaaEnd 文档原话大意：截图以 1280×720 为基准，**无需手动切游戏分辨率**，framework 会改图片尺寸。

参考：

- `MaaEnd/docs/zh_cn/developers/coding-standards.md`（1280×720 基准 + 自动转换）
- `MaaEnd/docs/zh_cn/developers/getting-started.md`
- MaaEnd-Client：`ctrl.SetScreenshotTargetLongSide(1280)`
- MaaFramework ImageCropper 示例：`set_screenshot_target_long_side(1280)` / `short_side(720)`

## 我们怎么接

1. 资源与审查：`target_size = [1280, 720]`（`tools/touch-review/config.json`：奥丁截图后缩到 720p 再标）
2. 运行 MXU / Agent 时：控制器创建后调用  
   `SetScreenshotTargetLongSide(1280)`（或短边 720，16:9 等价）——见 `agent/go-service/README.md`
3. 设备保持 16:9（奥丁横屏 `1920×1080` 即可），**不要**为了 Maa 去 `wm size 1280x720`
4. **手工/脚本点击**（touch-review 联调）必须把 720p 坐标乘以 `device_w/1280`、`device_h/720`（`tools/touch-review/device_geom.py`）；只有 MaaFramework 控制器会自动换算
5. 奥丁重连：`tools/touch-review/_odin_reconnect.ps1`（端口以无线调试页为准，写入 `config.json`）

## 联调底座检查（步骤 1）

- [x] WiFi ADB 可连（Odin3）
- [x] 原始截图 1920×1080，审查输出 1280×720
- [x] 点击坐标缩放辅助 `device_geom.py`
- [x] 手册导航坐标标定 → `docs/zh_cn/odin-nav-calib.json`  
  （Terminal `1198,38` → 索拉指南 `634,500` → 无音清剿 `183,531`；已到列表且检出「直接挑战」）
- [x] LongSide 约定已写入本文与 `agent/go-service/README.md`（Go `Connect` 后正式调用仍待接入）
- [ ] Agent/MXU 正式接上 `SetScreenshotTargetLongSide`（Go 初始化时）

## 注意

- 缩放会轻微损失细节；模板阈值可略放宽若 1080→720 匹配不稳
- 若游戏在不同 DPI 下 UI 布局**不成比例**（少见），才需要分资源包；鸣潮横屏 16:9 一般成比例
- Win32「小窗改窗口」那套与奥丁无关，不要混用
