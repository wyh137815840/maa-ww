$adb = 'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe'
$serial = '127.0.0.1:16384'
& $adb connect $serial
& $adb devices
& $adb -s $serial shell wm size
& $adb -s $serial shell 'dumpsys window | grep -E mCurrentFocus|mFocusedApp'
$remote = '/data/local/tmp/maa_ww_diag.png'
& $adb -s $serial shell rm -f $remote
& $adb -s $serial shell screencap -p $remote
& $adb -s $serial pull $remote D:\git\maa-ww\review\inbox\_diag.png
$img = Get-Item D:\git\maa-ww\review\inbox\_diag.png
Write-Output ("diag_bytes=" + $img.Length)
python -c "from PIL import Image; im=Image.open(r'D:\git\maa-ww\review\inbox\_diag.png'); print(im.size, im.mode); px=im.convert('RGB').getpixel((640,360)); print('center', px); print('extrema', im.convert('RGB').getextrema())"
