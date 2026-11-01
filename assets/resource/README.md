# resource（官服底座包）

MaaFramework `PostBundle` **必须**能单独加载成功。本目录需要：

| 路径 | 说明 |
| --- | --- |
| `default_pipeline.json` | 默认节点参数 |
| `pipeline/*.json` | 业务 Pipeline（第一期从 `resource_adb/pipeline` 同步进来） |
| `image/**` | 模板图（第一期从 `resource_adb/image` 同步） |
| `model/` | OCR 等模型（对齐 MaaEnd：`assets/resource/model` ← [MaaEnd-AI](https://github.com/MaaEnd/MaaEnd-AI)） |

> 第一期 Android 只打 **一个** Official path `./resource`（`attach_resource_path` 暂空）。  
> `resource_adb/` 仍是 ADB 侧源目录；改完后跑 `python tools/sync_resource_from_adb.py` 再打包/推送。

装机缺 model 时，可从同机已装 MaaEnd 拷贝：

```text
/storage/emulated/0/Android/data/com.aliothmoon.maafw.maaend/files/pi/resource/model
→ …/com.aliothmoon.maafw.maaww/files/pi/resource/model
```
