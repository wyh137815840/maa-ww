from pathlib import Path
from PIL import Image
from tacet_select_proto import detect_thumb, find_go_buttons
inbox = Path('../../review/inbox')
for name in ['20261031-205657-snap.png','20261031-205700-snap.png','20261031-205704-snap.png','20261031-205708-snap.png','20261031-205201-snap.png']:
 p=inbox/name
 if not p.exists():
  print('missing', name); continue
 im=Image.open(p).convert('RGB')
 print(name, 'thumb', detect_thumb(im), 'btns', find_go_buttons(im), 'size', im.size)
