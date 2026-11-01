$ErrorActionPreference = "Stop"
$src = "D:\git\maa-ww\Android\_apk_extract\lib\arm64-v8a"
$dst = "D:\git\maa-ww\Android\MaaFwApp\app\src\main\jniLibs\arm64-v8a"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
# Only upstream MaaFramework + deps. Do NOT overlay MaaFwApp's own bridge/launcher/agentexec.
Get-ChildItem $dst -Filter "*.so" -ErrorAction SilentlyContinue | Remove-Item -Force
$keep = @(
  "libMaaFramework.so",
  "libMaaUtils.so",
  "libMaaToolkit.so",
  "libMaaAgentClient.so",
  "libMaaAgentServer.so",
  "libMaaAdbControlUnit.so",
  "libMaaAndroidNativeControlUnit.so",
  "libMaaCustomControlUnit.so",
  "libMaaRecordControlUnit.so",
  "libMaaReplayControlUnit.so",
  "libonnxruntime.so",
  "libopencv_world4.so",
  "libfastdeploy_ppocr.so",
  "libncnn.so",
  "libc++_shared.so"
)
foreach ($name in $keep) {
  $p = Join-Path $src $name
  if (-not (Test-Path $p)) { throw "missing $name" }
  Copy-Item $p (Join-Path $dst $name) -Force
  Write-Output "staged $name"
}
# Version stamp so AGP plugins don't insist on re-download
Set-Content -Path (Join-Path $dst "..\..\.maafwversion") -Value "from-MaaEnd-apk-extract" -Encoding ascii
Write-Output "count=$((Get-ChildItem $dst -Filter *.so).Count)"
