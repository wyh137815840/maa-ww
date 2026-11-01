from pathlib import Path
from PIL import Image
p = Path("assets/resource_adb/image/Guidebook")
for f in sorted(p.glob("TacetTreasure*.png")):
    print(f.name, Image.open(f).size)
