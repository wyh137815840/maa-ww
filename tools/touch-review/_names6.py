from PIL import Image
from pathlib import Path
from tacet_select_proto import find_go_buttons
inbox=Path('../../review/inbox')
im=Image.open(inbox/'20261031-231311-live-after-scroll-idx6.png').convert('RGB')
btns=find_go_buttons(im)
print('btns', btns)
for i,(cx,cy) in enumerate(btns):
 im.crop((280,cy-40,700,cy+20)).save(inbox/f'idx6-vis-{i+1}.png')
 print('saved', i+1)
