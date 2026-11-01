# Give the physical Xbox pad back to the main screen (remove the MaaWW virtual-display association).
# Use when the pad "does nothing" in the game opened normally after a MaaWW run.
#   pwsh -NoProfile -File tools\pad-unbind.ps1 [-Serial <serial>]
param([string]$Serial = "")
$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$abRoot = if ($env:MAAWW_ANDROID_BUILD) { $env:MAAWW_ANDROID_BUILD } else { "D:\git\视频学习\tools\android-build" }
$jdk = "$abRoot\jdk\jdk-17.0.20.1+1"
$sdk = "$abRoot\sdk"
$adb = "$sdk\platform-tools\adb.exe"
$androidJar = Get-ChildItem "$sdk\platforms\android-*\android.jar" | Where-Object { $_.Directory.Name -match "^android-\d+$" } | Sort-Object { [int]($_.Directory.Name -replace "\D","") } | Select-Object -Last 1
$d8 = Get-ChildItem "$sdk\build-tools\*\lib\d8.jar" | Sort-Object FullName | Select-Object -Last 1
if (-not $androidJar -or -not $d8) { throw "android.jar / d8.jar not found under $sdk" }
$adbArgs = @()
if ($Serial) { $adbArgs = @("-s", $Serial) }

$out = Join-Path $abRoot "tmp\padunbind"
New-Item -ItemType Directory -Force $out | Out-Null
$ErrorActionPreference = "Continue"   # javac/d8 write warnings to stderr
& "$jdk\bin\javac.exe" --release 8 -cp $androidJar.FullName -d $out (Join-Path $root "tools\android\PadUnbind.java") 2>&1 | Out-Null
if (-not (Test-Path (Join-Path $out "PadUnbind.class"))) { throw "javac failed" }
& "$jdk\bin\java.exe" -cp $d8.FullName com.android.tools.r8.D8 --output $out (Join-Path $out "PadUnbind.class") --lib $androidJar.FullName 2>&1 | Out-Null
$ErrorActionPreference = "Stop"
if (-not (Test-Path (Join-Path $out "classes.dex"))) { throw "d8 failed" }
& $adb @adbArgs push (Join-Path $out "classes.dex") /data/local/tmp/padunbind.dex | Out-Null

# Descriptors of the Xbox pad(s), from dumpsys input.
$dump = (& $adb @adbArgs shell dumpsys input) -join "`n"
$descs = [regex]::Matches($dump, "Xbox Wireless Controller[\s\S]{0,400}?Descriptor:\s*([0-9a-f]{40})") | ForEach-Object { $_.Groups[1].Value } | Select-Object -Unique
if (-not $descs) { Write-Output "no Xbox pad found (pad disconnected?)"; exit 0 }
$main = ((& $adb @adbArgs shell dumpsys display) -join "`n" | Select-String -Pattern 'mBaseDisplayInfo=DisplayInfo\{"[^"]*", displayId 0,[\s\S]*?uniqueId "([^"]+)"').Matches[0].Groups[1].Value
if (-not $main) { throw "main display uniqueId not found" }
foreach ($d in $descs) {
  & $adb @adbArgs shell "CLASSPATH=/data/local/tmp/padunbind.dex app_process / PadUnbind $main $d"
}
$after = (& $adb @adbArgs shell "dumpsys input | grep AssociatedDisplayUniqueIdByDescriptor | grep virtual:") -join "`n"
if ($after) { Write-Output "STILL ASSOCIATED:`n$after"; exit 1 } else { Write-Output "pad released to main screen" }
