# Touch Review（触屏审查工具）

用于你我协作标定鸣潮安卓触屏操作：你截图并标注点击点 / ROI，我根据导出的审查卡写 Pipeline。

## 用法

在仓库根目录 `D:\git\maa-ww`：

```bat
REM 1) 截一张当前模拟器画面（默认 127.0.0.1:16384，缩放到 1280x720）
python tools\touch-review\capture.py --label home

REM 2) 打开本地标注页
python tools\touch-review\serve.py
```

浏览器会打开 `http://127.0.0.1:8765/`。

1. 左侧优先选带黄色「待标注」的截图  
2. 先读画面上方的黄色「本次任务」（我会写好你要做什么）  
3. 按说明：先框 **ROI**，再点 **点击点**  
4. 右侧字段一般已预填，核对后点「导出审查卡」  
5. 在聊天里把 card id 发我，或直接说「已导出」

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

- `adb_path` / `serial`：MuMu ADB  
- `target_size`：`[1280, 720]`  
- `port`：标注页端口，默认 `8765`
