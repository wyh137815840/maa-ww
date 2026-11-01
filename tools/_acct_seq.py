"""Print the Account* node sequence (with OCR text) from a pulled maafw.log."""
import re
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "tools/_shots/maafw_acct.log"
for l in open(path, encoding="utf-8", errors="ignore"):
    if "message=Node.PipelineNode.Succeeded" in l and "AgentClient" in l:
        m = re.search(r'"name":"(Account\w+|Startup\w+|StartUpGameWait|Title\w+)"', l)
        if not m:
            continue
        txt = re.findall(r'"text":"([^"]*)"', l)
        print(l[1:24], m.group(1), txt[:3])
