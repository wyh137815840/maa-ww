# 无音区「按目标自动滚到对应行」设计

目标：你只要说打第 N 个 / 某个副本名，程序自己打开列表、滚动、点右侧「直接挑战」。  
**不要**为每一行单独截图标定 IndexN。

## 结论（怎么做）

| 层 | 职责 |
| --- | --- |
| Pipeline JSON | 只负责：开手册 → 点「无音清剿」→ 调用自定义动作 → 接「开启挑战」 |
| Go CustomAction `SelectTacetRow` | 负责：按序号/名称计算滚动、找齐可见「直接挑战」、点中目标行 |
| 静态资源 | **一份**共用的「直接挑战」模板 + 列表区 ROI + 滚动条 X；分区行数表 |

对齐 ok-ww `click_on_book_target`（`BaseWWTask.py`），不要堆 `TacetGoIndex1..N`。

## 输入

任务选项二选一（可同时支持，名称优先）：

- `tacet_index`：从 1 起的全局序号（与 ok-ww「Which Tacet Suppression」一致）
- `tacet_name`：左侧副本名子串（如「沉心域」「落日堤屿」）→ 先查表得到 index

## 列表模型（已知）

- 每行：**左名称 + 右「直接挑战」**
- 分区间有**分区标题行**（如「瑝珑·梦州」「索拉里斯之极·拉海洛」），会打断纯行距
- ok-ww 分区结构：`structure = [4, 5, 5, 7]`，`total = 21`
- 视口大约同时露出 **3～4** 个「直接挑战」
- 右侧有竖滚动条：滑块为**亮色**、轨道偏暗（勿按深色块找）
- 已用滚动序列 `205657→205700→205704→205708` 校准，见 `tacet-scrollbar-calib.json`：
  - `bar_x = 1245`（0.973）
  - `bar_bottom = 0.8806`（底态滑块底边 y≈635）
  - `thumb_h ≈ 104px`；`bar_top` 运行时取亮色滑块顶边（fallback 0.1963）

首屏实测（1280×720）：行距 ≈ 102px，按钮中心 x ≈ 1146；这些只作校准初值，运行时以「检出的按钮」为准。

## 核心算法（序号）

```
SelectTacetRow(index):
  1. 在列表 ROI 内 TemplateMatch 所有「直接挑战」，按 y 排序 → buttons[]
  2. 若 index <= 视口容量 且 列表已在顶部:
       直接点 buttons[index-1]
       return
  3. 否则按 structure 算「跨过几个分区标题」cross：
       cross = 有多少个 prefix_sum < index
     用 ok-ww 公式算滚动条点击 y：
       item_h = (bar_bottom - bar_top - (len(structure)-1)*header_h) / total
       y = bar_top + item_h * index + cross * header_h
       点击 (bar_x, y)   // 把目标滚进视口
  4. 再找 buttons[]
     - 优先：若能判断「当前视口对应全局区间」，点对应下标
     - 简化（ok-ww 同款）：滚完后点 y 最大的那个按钮
       （滚动条标定成「目标落在视口底部」）
  5. 若进入编队/开启挑战页 → 成功；否则微调滚动条 y ± item_h*0.5 重试 1～2 次
```

名称模式：`name → catalog 下标 → 同上`；catalog 可用常量表（见下），不必截每行。

## 为什么 Index1..7 模板不够

- 同一副本滚动前后 **y 会变**，固定 ROI 的 IndexN 只能在「某一滚动态」碰巧对上
- 分区标题打乱行距，外推第 8+ 行会漂
- 新开图/筛选项会改列表，模板行号全废

共用「直接挑战」+ 运行时找齐再点，才稳。

## 需要的资源（尽量少）

已有 / 可从现图裁：

1. `Guidebook/TacetGoButton.png`（或任意一行裁的「直接挑战」）— **共用**
2. 列表按钮搜索 ROI：约 `[1040, 160, 200, 520]`
3. 滚动条点击 X：约 `1245`（0.973×1280）；顶/底用相对坐标

滚动条几何已用你提供的滑动序列标定，**不必再为滚动条补图**。仍可能需要的只有：

- 分区数量变了 → 改 `structure` 常量
- 名称选副本 → 一次划到底 OCR 补全 `tacet-catalog.json`（仍不必逐行审查卡）

## Pipeline 形态（示意）

```
OpenGuidebook → GuidebookTacetTab → SelectTacetRow(Custom) → TacetStartChallenge → …
```

`SelectTacetRow` 的 `custom_action_param` 传入 `{"index":3}` 或 `{"name":"落日堤屿"}`。

## 实现顺序

1. 文档 + 任务选项字段（本文件 / interface）— 已完成
2. 离线用现有截图验证「找齐按钮 + 排序」— 已完成（`tacet_select_proto.py`）
3. **奥丁联调**：Python `_live_test_select.py` 验证选行（滚动条点击在奥丁常无效，改用列表区 content swipe；约 50px/行 @720p）
4. Go `SelectTacetRow`（agent/go-service 初始化后）— 待做
5. 删掉/降级仅作调试用的 `TacetGoIndexN` 节点 — 待做

### 奥丁实测备注（2026-10-31）

- 导航：Terminal `(1198,38)` → 索拉指南 `(634,500)` → 无音清剿 `(183,531)`（左侧第 6 项）
- `find_go_buttons`：右栏 x∈[0.88w,0.96w]，合并碎裂暗带；首屏按钮约 `(1174, 237/339/441/543)`
- 滚动条：点轨道/拖滑块常无位移；**内容区 swipe** 可靠
- **验收（用户）**：首屏 1–4 直点进编队页即通过 — 已记 `tacet-accept-1to4.json`
- index≥5 需先 content swipe 再点视口最底按钮（滚动条点击在奥丁常无效）

## 名称表示例（首批，可改）

来自已截列表（顺序 = 全局序号）：

1. 沉心域无音区  
2. 炽心域无音区  
3. 方掌西峰无音区  
4. 玄幽东岳无音区  
5. 落日堤屿无音区  
6. 冰原运输港无音区  
7. 加拉尔冠阶无音区  
8. 隐喙深腹无音区（底部已露出，未完整标定）  
… 其余按 `structure` 补全，开一次游戏划到底 OCR 即可，仍不必逐行导出审查卡
