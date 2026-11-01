$ErrorActionPreference = "Stop"
$apk = Get-ChildItem "C:\Users\Administrator\Downloads\MaaEnd*.apk" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $apk) { throw "no MaaEnd apk in Downloads" }
Write-Output "apk=$($apk.FullName)"
$out = "D:\git\maa-ww\Android\_apk_extract"
if (Test-Path $out) { Remove-Item -Recurse -Force $out }
New-Item -ItemType Directory -Force -Path $out | Out-Null
# Only extract lib/** to avoid Windows case-collision in res/
$tmpZip = Join-Path $out "tmp.apk.zip"
Copy-Item $apk.FullName $tmpZip
Push-Location $out
try {
  tar -xf $tmpZip -- lib
} finally {
  Pop-Location
}
Remove-Item $tmpZip -Force
Get-ChildItem (Join-Path $out "lib") -Recurse -Filter "*.so" | ForEach-Object { $_.FullName }
