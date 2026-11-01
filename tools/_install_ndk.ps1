$ErrorActionPreference = "Stop"
$sdk = "D:\git\视频学习\tools\android-build\sdk"
$jdk = "D:\git\视频学习\tools\android-build\jdk\jdk-17.0.20.1+1"
$user = "D:\git\视频学习\tools\android-build\android-user"
$tmp = "D:\git\视频学习\tools\android-build\tmp"
New-Item -ItemType Directory -Force -Path "$user\cache",$tmp | Out-Null
$env:JAVA_HOME = $jdk
$env:ANDROID_HOME = $sdk
$env:ANDROID_SDK_ROOT = $sdk
$env:ANDROID_USER_HOME = $user
$env:TMP = $tmp
$env:TEMP = $tmp
$env:Path = "$jdk\bin;$sdk\cmdline-tools\latest\bin;$sdk\cmdline-tools\bin;$env:Path"

$sdkmanager = Get-ChildItem $sdk -Recurse -Filter "sdkmanager.bat" | Select-Object -First 1 -ExpandProperty FullName
if (-not $sdkmanager) { throw "sdkmanager.bat not found under $sdk" }
Write-Output "sdkmanager=$sdkmanager"

# Accept licenses non-interactively
$yes = "y`n" * 50
$yes | & $sdkmanager --sdk_root=$sdk --licenses | Out-Host

$ndk = "ndk;28.2.13676358"
Write-Output "install $ndk"
& $sdkmanager --sdk_root=$sdk $ndk
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Output "NDK_OK"
Get-ChildItem (Join-Path $sdk "ndk") | Select-Object Name
