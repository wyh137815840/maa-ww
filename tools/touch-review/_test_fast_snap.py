import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from snap_service import Snapper

s = Snapper()
s.warm()
dest = Path(s.cfg["inbox_dir"]) / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-snap-test.png"
t0 = time.perf_counter()
tag = s.capture_fast(dest)
print(f"{int((time.perf_counter()-t0)*1000)} ms {dest.name} {tag}")
