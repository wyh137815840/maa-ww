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

1. 左侧选中 inbox 截图  
2. 用「点击点」模式点要点的位置  
3. 用「ROI 框」模式拖出模板区域（可选但推荐）  
4. 填 `label` / `expected_next` / `note`  
5. 点「导出审查卡」

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
