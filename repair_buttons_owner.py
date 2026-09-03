from pathlib import Path
import re

p = Path("web/static/app.js")
s = p.read_text(encoding="utf-8-sig")

# ============================================================
# REPAIR THE FEATURE BAR / VOICE DAMAGE
# ============================================================

start = s.find("function featureBar(){")
end = s.find("async function mediaRequest", start)

if start != -1 and end != -1:
    clean_feature_bar = r'''
function featureBar(){
    if(document.getElementById("autonomousFinalFeatureBar"))return;

    const input=first(SELECTORS.input);
    if(!input)return;

    const bar=document.createElement("div");
    bar.id="autonomousFinalFeatureBar";

    bar.innerHTML=`
        <button type="button" onclick="autonomousFinalImage()">Image</button>
        <button type="button" onclick="autonomousFinalVideo()">Video</button>
    `;

    const form=input.closest("form");

    if(form && form.parentElement){
        form.parentElement.insertBefore(bar,form);
    }else if(input.parentElement){
        input.parentElement.insertBefore(bar,input);
    }
}

'''
    s = s[:start] + clean_feature_bar + s[end:]
    print("Repaired damaged feature-bar section.")
else:
    print("Feature-bar section not found; no change made there.")

# ============================================================
# FIX CREATOR / OWNER ANSWER
# ============================================================

old_pattern = r'const ownerQuestion = .*?;'
new_pattern = r'''const ownerQuestion =
        /(who\s+(is|'s)\s+(your\s+)?(creator|owner)|who\s+(is|'s)\s+(the\s+)?(creator|owner)|who\s+(is|'s)\s+(the\s+)?creator\s+and\s+owner|who\s+made\s+you|who\s+created\s+you|who\s+owns\s+you|creator\s+and\s+owner)[?!.,\s]*$/i;'''

s, count = re.subn(
    old_pattern,
    new_pattern,
    s,
    count=1,
    flags=re.S
)

if count:
    print("Expanded creator/owner question detection.")
else:
    print("Creator/owner regex was not replaced; checking answer separately.")

old_answer = 'addMessage("assistant", "My creator and owner is Shreyansh Ray.");'

new_answer = '''addMessage(
            "assistant",
            "Creator & Owner: Shreyansh Ray\\nHonorable Mention — Support: Arnav Baliyan"
        );'''

if old_answer in s:
    s = s.replace(old_answer, new_answer, 1)
    print("Updated creator/owner answer.")
else:
    # If the previous source has a slightly different formatting,
    # replace the first matching answer line.
    s, n = re.subn(
        r'addMessage\(\s*"assistant",\s*"My creator and owner is Shreyansh Ray\."\s*\);',
        new_answer,
        s,
        count=1,
        flags=re.S
    )
    if n:
        print("Updated creator/owner answer using fallback.")

# ============================================================
# ENSURE STATUS ALSO KNOWS THE HONORABLE MENTION
# ============================================================

status_old = '"creator": "Shreyansh Ray",'

if status_old in s:
    s = s.replace(
        status_old,
        '"creator": "Shreyansh Ray",\n        "honorable_mention": "Arnav Baliyan",',
        1
    )
    print("Added honorable mention to status metadata.")

# ============================================================
# WRITE UTF-8 WITHOUT BOM
# ============================================================

p.write_text(s, encoding="utf-8")

print("")
print("==============================================")
print("ADA REPAIR COMPLETE")
print("==============================================")
print("Buttons: restored")
print("Voice button: removed")
print("Voice code: removed")
print("Creator: Shreyansh Ray")
print("Owner: Shreyansh Ray")
print("Honorable Mention — Support: Arnav Baliyan")
print("==============================================")
