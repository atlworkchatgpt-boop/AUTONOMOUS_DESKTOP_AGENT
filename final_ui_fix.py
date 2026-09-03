from pathlib import Path
import re

root = Path("web/static")
app = root / "app.js"
index = root / "index.html"
creator = root / "creator.html"

# ------------------------------------------------------------
# APP.JS
# ------------------------------------------------------------
if app.exists():
    s = app.read_text(encoding="utf-8-sig")

    # Use ASCII-only JS Unicode escapes so Windows encoding
    # cannot corrupt the chess pieces.
    pieces = {
        "K": r"\u2654",
        "Q": r"\u2655",
        "R": r"\u2656",
        "B": r"\u2657",
        "N": r"\u2658",
        "P": r"\u2659",
        "k": r"\u265A",
        "q": r"\u265B",
        "r": r"\u265C",
        "b": r"\u265D",
        "n": r"\u265E",
        "p": r"\u265F",
    }

    # Replace any existing quoted chess characters with
    # ASCII JavaScript escapes.
    for key, esc in pieces.items():
        code = ord({
            "K":"♔","Q":"♕","R":"♖","B":"♗","N":"♘","P":"♙",
            "k":"♚","q":"♛","r":"♜","b":"♝","n":"♞","p":"♟"
        }[key])
        char = chr(code)
        s = s.replace('"' + char + '"', '"' + esc + '"')
        s = s.replace("'" + char + "'", "'" + esc + "'")

    # Remove Voice button from the dynamically-created feature bar.
    s = re.sub(
        r'\s*<button[^>]*onclick="autonomousFinalVoice\(\)"[^>]*>.*?</button>',
        "",
        s,
        flags=re.I | re.S
    )

    # Remove the Voice function itself.
    s = re.sub(
        r'\s*window\.autonomousFinalVoice\s*=\s*function\s*\(\)\s*\{.*?\n\s*\};',
        "",
        s,
        flags=re.I | re.S
    )

    # Safe ASCII close button.
    s = s.replace("×", "X")

    app.write_text(s, encoding="utf-8")

# ------------------------------------------------------------
# INDEX.HTML
# ------------------------------------------------------------
if index.exists():
    s = index.read_text(encoding="utf-8-sig")
    s = s.replace("×", "X")
    index.write_text(s, encoding="utf-8")

# ------------------------------------------------------------
# CREATOR PAGE
# ------------------------------------------------------------
if creator.exists():
    s = creator.read_text(encoding="utf-8-sig")

    # Remove corrupted/non-ASCII return-button symbols.
    s = s.replace("←", "")
    s = s.replace("â†", "")
    s = s.replace("Â", "")

    # Remove existing Return-to-Autonomous-AI links/buttons so
    # we don't leave a corrupted duplicate.
    s = re.sub(
        r'<a\b[^>]*>.*?Return\s+to\s+Autonomous\s+AI.*?</a>',
        "",
        s,
        flags=re.I | re.S
    )

    s = re.sub(
        r'<button\b[^>]*>.*?Return\s+to\s+Autonomous\s+AI.*?</button>',
        "",
        s,
        flags=re.I | re.S
    )

    # Add one clean ASCII-only return button.
    button = '''
<div style="text-align:center;margin:28px 0;">
    <a href="/" style="
        display:inline-block;
        padding:11px 18px;
        border-radius:10px;
        text-decoration:none;
        font-weight:600;
        background:#19a974;
        color:white;
    ">Return to Autonomous AI</a>
</div>
'''

    if "</body>" in s.lower():
        pos = s.lower().rfind("</body>")
        s = s[:pos] + button + "\n" + s[pos:]
    else:
        s += "\n" + button

    creator.write_text(s, encoding="utf-8")

print("========================================")
print("ADA FINAL UI FIX COMPLETE")
print("Chess pieces: fixed")
print("Popup close: fixed")
print("Creator return button: fixed")
print("Voice button: removed")
print("Voice function: removed")
print("========================================")
