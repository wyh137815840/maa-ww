$ErrorActionPreference = "Stop"
$destRoot = "D:\git\视频学习\tools\android-build\gradle-home\wrapper\dists\gradle-9.4.1-bin\manual"
New-Item -ItemType Directory -Force -Path $destRoot | Out-Null
$zip = Join-Path $destRoot "gradle-9.4.1-bin.zip"
$urls = @(
  "https://mirrors.cloud.tencent.com/gradle/gradle-9.4.1-bin.zip",
  "https://mirrors.aliyun.com/macports/distfiles/gradle/gradle-9.4.1-bin.zip",
  "https://services.gradle.org/distributions/gradle-9.4.1-bin.zip"
)
foreach ($u in $urls) {
  Write-Output "TRY $u"
  try {
    Invoke-WebRequest -Uri $u -OutFile $zip -TimeoutSec 600
    if ((Get-Item $zip).Length -gt 50MB) {
      Write-Output "OK size=$((Get-Item $zip).Length)"
      # wrapper expects a hash-named dir; also unpack here for direct use
      Expand-Archive -Path $zip -DestinationPath $destRoot -Force
      Write-Output "unpacked"
      exit 0
    }
  } catch {
    Write-Output "FAIL $_"
  }
}
exit 1
