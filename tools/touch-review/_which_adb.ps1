$adb = 'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe'
$ErrorActionPreference = 'Continue'
foreach ($p in @('16384','16416')) {
  Write-Output ("======== 127.0.0.1:$p ========")
  & $adb connect "127.0.0.1:$p" 2>&1 | Out-String
}
& $adb devices -l
Set-Location D:\git\maa-ww
python - <<'PY'
import subprocess
from pathlib import Path
from PIL import Image
import tempfile, os

adb = r'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe'
inbox = Path('review/inbox')
for port in ('16384', '16416'):
    serial = f'127.0.0.1:{port}'
    remote = '/data/local/tmp/maa_ww_which.png'
    out = inbox / f'_which-{port}.png'
    subprocess.run([adb, 'connect', serial], capture_output=True)
    r = subprocess.run([adb, '-s', serial, 'shell', 'echo', 'ok'], capture_output=True, text=True)
    if 'ok' not in (r.stdout or ''):
        print(port, 'not reachable', r.stderr)
        continue
    subprocess.run([adb, '-s', serial, 'shell', 'rm', '-f', remote], capture_output=True)
    subprocess.run([adb, '-s', serial, 'shell', 'screencap', '-p', remote], check=False)
    with tempfile.TemporaryDirectory() as tmp:
        local = Path(tmp) / 'raw.png'
        pr = subprocess.run([adb, '-s', serial, 'pull', remote, str(local)], capture_output=True, text=True)
        if not local.is_file():
            print(port, 'pull failed', pr.stderr)
            continue
        im = Image.open(local).convert('RGB')
        im.save(out)
        # sample center + corners brightness
        cx, cy = im.size[0]//2, im.size[1]//2
        print(port, 'size', im.size, 'center', im.getpixel((cx,cy)), 'saved', out.name)
    # focus
    fo = subprocess.run([adb, '-s', serial, 'shell', 'dumpsys', 'activity', 'activities'], capture_output=True)
    text = fo.stdout.decode('utf-8', errors='ignore')
    for line in text.splitlines():
        if 'topResumedActivity' in line or 'mResumedActivity' in line or 'mingchao' in line.lower():
            print(port, line.strip()[:160])
            break
    else:
        # fallback packages running
        ps = subprocess.run([adb, '-s', serial, 'shell', 'pidof', 'com.kurogame.mingchao'], capture_output=True, text=True)
        print(port, 'pidof mingchao=', (ps.stdout or '').strip() or 'none')
PY
