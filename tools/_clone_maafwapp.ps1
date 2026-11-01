$ErrorActionPreference = "Continue"
$dest = "D:\git\maa-ww\Android\MaaFwApp"
$urls = @(
  "https://github.com/Aliothmoon/MaaFwApp.git",
  "https://ghproxy.net/https://github.com/Aliothmoon/MaaFwApp.git",
  "https://gitclone.com/github.com/Aliothmoon/MaaFwApp.git"
)
New-Item -ItemType Directory -Force -Path "D:\git\maa-ww\Android" | Out-Null
if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
foreach ($u in $urls) {
  Write-Output "TRY $u"
  git clone --depth 1 -b main $u $dest 2>&1 | Tee-Object -Variable out | Out-Host
  if (Test-Path (Join-Path $dest "gradlew.bat")) {
    Write-Output "OK $u"
    exit 0
  }
  if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
}
Write-Output "ALL_FAILED"
exit 1
