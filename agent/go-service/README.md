# go-service

复杂识别与操作（尤其是自动战斗）放这里，由 Pipeline 通过 Custom Recognition / Action 调用。

## CombatLoop（MVP）

- CustomAction 名：`CombatLoop`
- 行为：对标 ok-ww `BaseChar.do_perform` 的时序输出（Echo → Liberation → Resonance → Attack → Heavy → Swap）
- 输入：手柄键码（见 `docs/zh_cn/ww-input-map.json`），经 `PostClickKey` / `KeyDown`+`KeyUp` 注入
- 在战判定：Pipeline `CombatHasTarget` / `CombatEnemyHP`（对齐 ok-ww 准星+红血条）；无目标则 R3 重锁
- 退出：不在战（重锁失败）→ 交给宝藏节点；或 `exit_nodes`（宝藏/结算）；或 `max_duration_ms`

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
