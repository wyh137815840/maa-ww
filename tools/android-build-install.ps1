# Build MaaWW APK via MaaFwApp and installDebug to connected device.
#   -TestOnly : copy overlays + run overlay unit tests (StickCommand/AxisWriter), no install.
param([switch]$TestOnly)
$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$app = Join-Path $root "Android\MaaFwApp"
# Set MAAWW_ANDROID_BUILD to an ASCII junction of the toolchain dir if Gradle test workers fail on non-ASCII paths.
$abRoot = if ($env:MAAWW_ANDROID_BUILD) { $env:MAAWW_ANDROID_BUILD } else { "D:\git\视频学习\tools\android-build" }
$sdk = "$abRoot\sdk"
$jdk = "$abRoot\jdk\jdk-17.0.20.1+1"
$gradleHome = "$abRoot\gradle-home"
if (-not (Test-Path $jdk)) { throw "JDK not found: $jdk" }
if (-not (Test-Path $sdk)) { throw "SDK not found: $sdk" }
if (-not (Test-Path (Join-Path $app "gradlew.bat"))) { throw "MaaFwApp missing: $app" }
New-Item -ItemType Directory -Force -Path $gradleHome | Out-Null

$tmp = "$abRoot\tmp"
$userHome = "$abRoot\android-user"
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
if (-not $TestOnly) {
  Write-Output "build android go-service"
  python (Join-Path $root "tools\build_android_agents.py")
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

# Apply maa-ww-owned overlays onto MaaFwApp tree (may be a junction to external source).
# Source of truth for git is Android/overlays/** — never edit the junction target as "repo work".
$overlayRoot = Join-Path $root "Android\overlays"
$overlayDestRoot = Join-Path $app "app\src\main\java\com\aliothmoon\maafw\remote\internal"
# Every file here is REQUIRED: GamepadForwarder.kt references StickCommand. A missing source
# must fail the build, not silently produce an APK that cannot compile / has a stale pump.
$overlayFiles = @(
  "GamepadForwarder.kt",
  "StickCommand.kt"
)
New-Item -ItemType Directory -Force -Path $overlayDestRoot | Out-Null
foreach ($name in $overlayFiles) {
  $src = Join-Path $overlayRoot "maafw\remote\internal\$name"
  $dst = Join-Path $overlayDestRoot $name
  if (-not (Test-Path $src)) { throw "Missing required overlay source: $src" }
  Copy-Item -Force $src $dst
  if (-not (Test-Path $dst)) { throw "Overlay copy failed: $dst" }
  if ((Get-FileHash $src).Hash -ne (Get-FileHash $dst).Hash) { throw "Overlay content mismatch: $dst" }
  Write-Output "overlay applied: $name"
}

# Overlay unit tests (JUnit4, already a test dependency of MaaFwApp).
$testOverlayRoot = Join-Path $overlayRoot "maafw\test\remote\internal"
$testDestRoot = Join-Path $app "app\src\test\java\com\aliothmoon\maafw\remote\internal"
if (Test-Path $testOverlayRoot) {
  New-Item -ItemType Directory -Force -Path $testDestRoot | Out-Null
  Get-ChildItem $testOverlayRoot -Filter *.kt | ForEach-Object {
    Copy-Item -Force $_.FullName (Join-Path $testDestRoot $_.Name)
    Write-Output "overlay test applied: $($_.Name)"
  }
}

Set-Location $app

if ($TestOnly) {
  Write-Output "gradle :app:testDebugUnitTest (overlay tests)"
  & .\gradlew.bat --no-daemon :app:testDebugUnitTest --tests "com.aliothmoon.maafw.remote.internal.*"
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  Write-Output "OVERLAY_TESTS_OK"
  exit 0
}

$so = Join-Path $app "app\src\main\jniLibs\arm64-v8a\libMaaFramework.so"
if (-not (Test-Path $so)) {
  throw "Missing $so — run tools/_stage_jni_libs.ps1 first"
}

Write-Output "gradle :app:installDebug"
& .\gradlew.bat --no-daemon :app:installDebug
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Output "INSTALL_OK"
