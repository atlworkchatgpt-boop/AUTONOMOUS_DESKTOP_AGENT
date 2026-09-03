from pathlib import Path
import re

p = Path("web/static/index.html")
s = p.read_text(encoding="utf-8-sig")

def fix(m):
    x = m.group(0)
    try:
        y = x.encode("cp1252").decode("utf-8")
        return y
    except:
        return x

s = re.sub(r"[^\x00-\x7F]{2,}", fix, s)
p.write_text(s, encoding="utf-8")
print("DONE - UI encoding fixed")
