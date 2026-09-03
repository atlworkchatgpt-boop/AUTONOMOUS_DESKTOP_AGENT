from pathlib import Path

files = list(Path("web/static").glob("*.html")) + list(Path("web/static").glob("*.js"))

fixes = {
    chr(0x00C3)+chr(0x0097): "&times;",
    chr(0x00E2)+chr(0x009C)+chr(0x00A6): "&#10022;",
    chr(0x00E2)+chr(0x0099)+chr(0x009F): "&#9823;",
    chr(0x00E2)+chr(0x0099)+chr(0x009C): "&#9820;",
    chr(0x00E2)+chr(0x0099)+chr(0x009E): "&#9822;",
    chr(0x00E2)+chr(0x0099)+chr(0x009D): "&#9821;",
    chr(0x00E2)+chr(0x0099)+chr(0x009B): "&#9819;",
    chr(0x00E2)+chr(0x0099)+chr(0x009A): "&#9818;",
    chr(0x00E2)+chr(0x0099)+chr(0x0094): "&#9812;",
    chr(0x00E2)+chr(0x0099)+chr(0x0095): "&#9813;",
    chr(0x00E2)+chr(0x0099)+chr(0x0096): "&#9814;",
    chr(0x00E2)+chr(0x0099)+chr(0x0097): "&#9815;",
    chr(0x00E2)+chr(0x0099)+chr(0x0098): "&#9816;",
    chr(0x00E2)+chr(0x0099)+chr(0x0099): "&#9817;",
}

for p in files:
    s = p.read_text(encoding="utf-8-sig")
    old = s
    for bad, good in fixes.items():
        s = s.replace(bad, good)
    if s != old:
        p.write_text(s, encoding="utf-8")
        print("Fixed:", p)

print("FINAL ICON FIX COMPLETE")
