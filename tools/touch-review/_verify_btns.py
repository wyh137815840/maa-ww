from pathlib import Path
from PIL import Image
from tacet_select_proto import find_go_buttons

inbox = Path("../../review/inbox")
for name in [
    "20261031-230956-s2-g0.png",
    "20261031-225244-odin-tacetrail-183-531.png",
    "20261031-230719-fin-tacet.png",
]:
    print(name, find_go_buttons(Image.open(inbox / name).convert("RGB")))
