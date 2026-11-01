$ErrorActionPreference = "Stop"
$srcZip = "D:\git\视频学习\tools\android-build\gradle-home\wrapper\dists\gradle-9.4.1-bin\manual\gradle-9.4.1-bin.zip"
$hashDir = "D:\git\视频学习\tools\android-build\gradle-home\wrapper\dists\gradle-9.4.1-bin\arn2x92ynaizyzdaamcbpbhtj"
New-Item -ItemType Directory -Force -Path $hashDir | Out-Null
Copy-Item $srcZip (Join-Path $hashDir "gradle-9.4.1-bin.zip") -Force
# Wrapper marks complete with a .ok file after extract; pre-extract to save time
if (-not (Test-Path (Join-Path $hashDir "gradle-9.4.1\bin\gradle.bat"))) {
  Expand-Archive -Path (Join-Path $hashDir "gradle-9.4.1-bin.zip") -DestinationPath $hashDir -Force
}
# Touch ok marker used by some wrapper versions
New-Item -ItemType File -Force -Path (Join-Path $hashDir "gradle-9.4.1-bin.zip.ok") | Out-Null
Write-Output "ready $hashDir"
Get-ChildItem $hashDir | Select-Object Name,Length
