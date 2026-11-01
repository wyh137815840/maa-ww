import json
from pathlib import Path

for p in [
    Path(r"D:\git\maa-ww\assets\resource_adb\pipeline\Startup.json"),
    Path(r"D:\git\maa-ww\assets\resource\pipeline\Startup.json"),
]:
    d = json.loads(p.read_text(encoding="utf-8"))
    for k in ("StartupPadReady", "StartupPadReadyRT", "StartupPadReadyDPad", "StartupPadReadyMenu"):
        assert k in d, k
    assert "InInstanceClaimHint" in d["StartupPadWatch"]["next"]
    print(p.name, "ok", "Ready thr", d["StartupPadReady"]["threshold"], "roi", d["StartupPadReady"]["roi"])
