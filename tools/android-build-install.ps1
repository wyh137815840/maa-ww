# Build MaaWW APK via MaaFwApp and installDebug to connected device.
$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$app = Join-Path $root "Android\MaaFwApp"
$sdk = "D:\git\视频学习\tools\android-build\sdk"
$jdk = "D:\git\视频学习\tools\android-build\jdk\jdk-17.0.20.1+1"
$gradleHome = "D:\git\视频学习\tools\android-build\gradle-home"
if (-not (Test-Path $jdk)) { throw "JDK not found: $jdk" }
if (-not (Test-Path $sdk)) { throw "SDK not found: $sdk" }
if (-not (Test-Path (Join-Path $app "gradlew.bat"))) { throw "MaaFwApp missing: $app" }
New-Item -ItemType Directory -Force -Path $gradleHome | Out-Null

$tmp = "D:\git\视频学习\tools\android-build\tmp"
$userHome = "D:\git\视频学习\tools\android-build\android-user"
New-Item -ItemType Directory -Force -Path $tmp,$userHome | Out-Null
$env:JAVA_HOME = $jdk
$env:ANDROID_HOME = $sdk
$env:ANDROID_SDK_ROOT = $sdk
$env:ANDROID_USER_HOME = $userHome
$env:GRADLE_USER_HOME = $gradleHome
$env:TMP = $tmp
$env:TEMP = $tmp
$env:TMPDIR = $tmp
$env:Path = "$jdk\bin;$sdk\platform-tools;" + $env:Path


Write-Output "root=$root"
Write-Output "JAVA_HOME=$env:JAVA_HOME"
Write-Output "GRADLE_USER_HOME=$env:GRADLE_USER_HOME"

# Cross-compile go-service → Android/agent-dist/.../libgo-service.so (CombatLoop)
$env:Path = "C:\Program Files\Go\bin;" + $env:Path
if (-not $env:GOPROXY) { $env:GOPROXY = "https://goproxy.cn,direct" }
if (-not $env:GOSUMDB) { $env:GOSUMDB = "sum.golang.google.cn" }
$env:GOTMPDIR = $tmp
Write-Output "build android go-service"
python (Join-Path $root "tools\build_android_agents.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Apply maa-ww-owned overlays onto MaaFwApp tree (may be a junction to external source).
# Source of truth for git is Android/overlays/** — never edit the junction target as "repo work".
$overlayRoot = Join-Path $root "Android\overlays"
$forwarderOverlay = Join-Path $overlayRoot "maafw\remote\internal\GamepadForwarder.kt"
$forwarderTarget = Join-Path $app "app\src\main\java\com\aliothmoon\maafw\remote\internal\GamepadForwarder.kt"
if (Test-Path $forwarderOverlay) {
  $destDir = Split-Path $forwarderTarget -Parent
  New-Item -ItemType Directory -Force -Path $destDir | Out-Null
  Copy-Item -Force $forwarderOverlay $forwarderTarget
  Write-Output "overlay applied: GamepadForwarder.kt"
} else {
  Write-Output "WARN: missing overlay $forwarderOverlay"
}

Set-Location $app

$so = Join-Path $app "app\src\main\jniLibs\arm64-v8a\libMaaFramework.so"
if (-not (Test-Path $so)) {
  throw "Missing $so — run tools/_stage_jni_libs.ps1 first"
}

Write-Output "gradle :app:installDebug"
& .\gradlew.bat --no-daemon :app:installDebug
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Output "INSTALL_OK"
