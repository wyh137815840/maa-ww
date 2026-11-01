# Touch Review（触屏审查工具）

用于你我协作标定鸣潮安卓触屏操作：你截图并标注点击点 / ROI，我根据导出的审查卡写 Pipeline。

## 用法

在仓库根目录 `D:\git\maa-ww`：

```bat
REM 0) 快截服务（奥丁）：python tools\touch-review\snap_service.py（或 start_snap_service.bat），保持运行
REM    按 Ctrl+Alt+空格：截奥丁当前屏 → review/inbox/*-snap.png，并自动生成「待标注」卡片
REM    （卡片说明取自 review/snap_session.json，由 agent 按场景更新；首次截图自动打开标注页）
REM    哔一声=成功；低哔=失败。截到全黑会报错不入库：奥丁息屏，或游戏在 MaaWW 虚拟显示上
REM    （screencap 截不到虚拟显示）——先停 MaaWW 任务，让游戏在主屏前台。
REM    测试不用热键：python tools\touch-review\snap_service.py --once

REM 1) 截一张当前模拟器画面（默认连 config.json 的 serial，内部 1280x720）
REM    MuMu 安卓15 上会优先截 mumuscreen001（游戏层），避免截到桌面
python tools\touch-review\capture.py --label home

REM 2) 打开本地标注页
python tools\touch-review\serve.py
```


浏览器会打开 `http://127.0.0.1:8765/`。

1. 左侧优先选带黄色「待标注」的截图（绿色「已导出」可忽略）  
2. 先读画面上方的黄色「本次任务」（我会写好你要做什么）  
3. 按说明：先框 **ROI**，再点 **点击点**  
4. 右侧字段一般已预填，核对后点「导出审查卡」  
5. 导出后该条会变成「已导出」，inbox 不再黄标；聊天发 card id 或说「已导出」即可

给某张截图补任务说明：

```bat
python tools\touch-review\brief.py 20261031-172410-boot.png --title "标题页" --goal "标点击连接" --step "框住文字" --step "点文字中心" --label TitleClickConnect
```

## 产物

```text
review/inbox/*.png              # 原始截图（默认不入库）
review/cards/<id>/
  card.json                     # 给我读的结构化数据
  CARD.md                       # 人类可读摘要
  screen.png / preview.png
  template.png                  # ROI 裁剪（若有）
review/cards/INDEX.md           # 总表
```

把某个 `card id` 或 `review/cards/<id>/CARD.md` 发给我即可继续写节点。

## 配置

`tools/touch-review/config.json`：

- `adb_path` / `serial`：当前联调以 **Odin 3 WiFi** 为准（端口以无线调试页为准）  
- `target_size`：`[1280, 720]`（设备可为 1920×1080，截图会缩到 720p 再标）  
- `port`：标注页端口，默认 `8765`

## 与 Pipeline 的衔接

导出卡后把 card id /「已导出」发回聊天即可写入 `assets/resource_adb/pipeline/`，再用：

```bat
python tools\_push_pi_only.py
```

推到设备上的 MaaWW PI。奥丁导航坐标摘要：`docs/zh_cn/odin-nav-calib.json`。
