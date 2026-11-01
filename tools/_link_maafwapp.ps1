$ErrorActionPreference = "Stop"
$link = "D:\git\maa-ww\Android\MaaFwApp"
$target = "D:\git\视频学习\tools\MaaFwApp-analysis"
New-Item -ItemType Directory -Force -Path "D:\git\maa-ww\Android" | Out-Null
if (Test-Path $link) {
  $item = Get-Item $link -Force
  if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
    cmd /c rmdir "$link"
  } else {
    Remove-Item -Recurse -Force $link
  }
}
cmd /c mklink /J "$link" "$target"
if (-not (Test-Path "$link\gradlew.bat")) { throw "junction failed" }
Write-Output "OK $link -> $target"
