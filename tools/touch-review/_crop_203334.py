from PIL import Image
from pathlib import Path

im = Image.open(Path(__file__).resolve().parents[2] / "review/inbox/20261031-203334-snap.png")
inbox = Path(__file__).resolve().parents[2] / "review/inbox"
im.crop((340, 420, 560, 490)).save(inbox / "_crop_left60.png")
im.crop((700, 420, 920, 490)).save(inbox / "_crop_right120.png")
im.crop((1050, 10, 1275, 80)).save(inbox / "_crop_stamina.png")
print("ok")
