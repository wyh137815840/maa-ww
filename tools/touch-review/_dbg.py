from PIL import Image
from pathlib import Path
from tacet_select_proto import find_go_buttons
for name in [
 " 20261031-225652-live-before-idx1.png\,
 \20261031-225705-live-after-scroll-idx6.png\,
 \20261031-225723-live-after-scroll-idx12.png\,
 \20261031-225656-live-after-click-idx1.png\,
 \20261031-225708-live-after-click-idx6.png\,
]:
 p=Path(\../../review/inbox\)/name
 im=Image.open(p).convert(\RGB\)
 print(name, \btns\, find_go_buttons(im), \size\, im.size)
 # crop top-left title area of after-click
 if \after-click\ in name:
 im.crop((20,20,420,90)).save(Path(\../../review/inbox\)/(name.replace(\.png\,\-title.png\)))
 print(" wrote title crop\)
