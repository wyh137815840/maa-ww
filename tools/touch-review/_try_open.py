from common import load_config
from capture import capture_png, ensure_device
from device_geom import raw_screen_size, tap720
from tacet_select_proto import find_go_buttons
from PIL import Image
from pathlib import Path
from datetime import datetime
import time
cfg=load_config(); ensure_device(cfg['adb_path'], cfg['serial'])
dw,dh=raw_screen_size(cfg['adb_path'], cfg['serial'])
OUT=Path('../../review/inbox')
def snap(label):
 p=OUT/(datetime.now().strftime('%Y%m%d-%H%M%S')+f'-{label}.png')
 print(capture_png(cfg['adb_path'], cfg['serial'], p, cfg), p.name); return p
def tap(x,y,w=1.2):
 print('tap',x,y,tap720(cfg['adb_path'], cfg['serial'],x,y,dw,dh)); time.sleep(w)
# try terminal then nearby icons
snap('try-hud')
for xy in [(1198,38),(1160,38),(1220,40),(1100,40),(1040,40),(980,40)]:
 tap(*xy, 1.5); p=snap(f'try-{xy[0]}-{xy[1]}'); im=Image.open(p).convert('RGB')
 # terminal menu: dark overlay with tiles
 w,h=im.size
 dark=sum(1 for y in range(200,500,8) for x in range(400,900,8) if sum(im.getpixel((x,y)))<180)
 print(' darkish', dark, 'btns', find_go_buttons(im))
 if dark>800 or len(find_go_buttons(im))>=2:
  print('OPENED at', xy); break
