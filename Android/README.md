# Android 客户端（MaaFwApp）

对齐 [MaaEnd/Android](https://github.com/MaaEnd/MaaEnd/tree/v2/Android)：外壳为 MaaFwApp，业务资源来自本仓库 `assets/`。

## 首次

1. 准备 JDK 17、Android SDK（可用 `D:\git\视频学习\tools\android-build\`）。
2. 将 `MaaFwApp` 放到 `Android/MaaFwApp`（本机可从 `D:\git\视频学习\tools\MaaFwApp-analysis` 拷贝/junction）。
3. 写 `Android/MaaFwApp/local.properties`（不进 git）：

```properties
sdk.dir=D:/git/视频学习/tools/android-build/sdk
pi.profile=../profile.yaml
build.debugAbi=arm64-v8a
build.releaseAbi=arm64-v8a
```

4. 铺 MaaFramework native：

```bash
python Android/MaaFwApp/scripts/setup_maa_framework.py --abi arm64-v8a --tag v5.14.0
```

## 出包并装到奥丁

```bash
# 仅改 assets 时：
.\Android\MaaFwApp\gradlew.bat -p Android\MaaFwApp :app:installDebug
```

实机验证走 **App 内任务**（Shizuku），禁止 ADB 替点游戏；可截图/看日志。测完关屏。
