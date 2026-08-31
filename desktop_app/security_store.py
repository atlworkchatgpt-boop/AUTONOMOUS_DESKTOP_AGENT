from __future__ import annotations
import base64, hashlib, hmac, json, os, secrets, smtplib, ssl
from email.message import EmailMessage
from pathlib import Path
APP=Path(os.getenv("APPDATA") or Path.home())/"AutonomousAI"; APP.mkdir(parents=True,exist_ok=True); CFG=APP/"security.json"
def _hash(p,s=None):
    s=s or secrets.token_bytes(16); d=hashlib.pbkdf2_hmac("sha256",p.encode(),s,250000); return base64.b64encode(s).decode(),base64.b64encode(d).decode()
def exists():return CFG.exists()
def create(password,recovery_email=""):
    if len(password)<6:raise ValueError("Password must be at least 6 characters.")
    s,h=_hash(password); CFG.write_text(json.dumps({"salt":s,"hash":h,"recovery_email":recovery_email.strip()}),encoding="utf-8")
def verify(password):
    if not CFG.exists():return False
    d=json.loads(CFG.read_text(encoding="utf-8")); s=base64.b64decode(d["salt"]); _,h=_hash(password,s); return hmac.compare_digest(h,d["hash"])
def change(old,new):
    if not verify(old):return False
    d=json.loads(CFG.read_text(encoding="utf-8")); create(new,d.get("recovery_email","") or ""); return True
def recovery_email():
    if not CFG.exists():return ""
    return json.loads(CFG.read_text(encoding="utf-8")).get("recovery_email","") or ""
def send_code():
    target=recovery_email(); sender=os.getenv("AUTONOMOUS_RECOVERY_GMAIL"); apppw=os.getenv("AUTONOMOUS_RECOVERY_GMAIL_APP_PASSWORD")
    if not target:raise RuntimeError("No recovery email configured.")
    if not sender or not apppw:raise RuntimeError("Set AUTONOMOUS_RECOVERY_GMAIL and AUTONOMOUS_RECOVERY_GMAIL_APP_PASSWORD in Windows environment variables first.")
    code=str(secrets.randbelow(900000)+100000); msg=EmailMessage(); msg["From"]=sender; msg["To"]=target; msg["Subject"]="Autonomous AI password verification"; msg.set_content("Your verification code is: "+code+"\nIt expires when this window closes.")
    with smtplib.SMTP_SSL("smtp.gmail.com",465,context=ssl.create_default_context()) as s:s.login(sender,apppw);s.send_message(msg)
    return code
