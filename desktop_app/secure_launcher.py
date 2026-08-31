from __future__ import annotations
import os, subprocess, sys, tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog
from security_store import exists,create,verify,change,send_code,recovery_email
ROOT=Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parent.parent))
OWNER="Shreyansh Ray"
def first_run():
    while not exists():
        p=simpledialog.askstring("Autonomous AI setup","Create a startup/action password (minimum 6 characters):",show="*")
        if p is None:sys.exit(0)
        p2=simpledialog.askstring("Confirm password","Re-enter the password:",show="*")
        if p!=p2:messagebox.showerror("Password","Passwords do not match.");continue
        email=simpledialog.askstring("Recovery","Optional recovery Gmail address:") or ""
        try:create(p,email);messagebox.showinfo("Autonomous AI","Password created.")
        except Exception as e:messagebox.showerror("Setup",str(e))
def login():
    for _ in range(5):
        p=simpledialog.askstring("Autonomous AI","Enter your password:",show="*")
        if p is None:return None
        if verify(p):return p
        messagebox.showerror("Access denied","Incorrect password.")
    return None
def launch(password):
    env=os.environ.copy();env["GNG_STARTUP_PASSWORD"]=password;env["GNG_ACTION_PASSWORD"]=password;env["OWNER_NAME"]=OWNER
    main=ROOT/"main.py"
    if not main.exists():messagebox.showerror("Autonomous AI","main.py not found beside the installed app.");return
    subprocess.Popen([sys.executable,str(main)],cwd=str(ROOT),env=env)
def change_password():
    old=simpledialog.askstring("Change password","Old password:",show="*");
    if old and verify(old):
        new=simpledialog.askstring("Change password","New password (minimum 6 characters):",show="*")
        if new:
            try:
                change(old,new);messagebox.showinfo("Password","Password changed.")
            except Exception as e:messagebox.showerror("Password",str(e))
        return
    if messagebox.askyesno("Recovery","Old password failed. Use Gmail verification?"):
        try:expected=send_code()
        except Exception as e:messagebox.showerror("Gmail recovery",str(e));return
        got=simpledialog.askstring("Gmail verification","Enter the 6-digit code:")
        if got==expected:
            new=simpledialog.askstring("New password","Create new password:",show="*")
            if new:
                email=recovery_email();create(new,email);messagebox.showinfo("Password","Password changed.")
        else:messagebox.showerror("Verification","Incorrect code.")
def main():
    root=tk.Tk();root.withdraw();first_run();pwd=login();
    if not pwd:return
    win=tk.Toplevel(root);win.title("Autonomous AI - Shreyansh Ray");win.geometry("430x260");win.resizable(False,False)
    tk.Label(win,text="AUTONOMOUS AI",font=("Segoe UI",18,"bold")).pack(pady=(28,4));tk.Label(win,text="Creator and owner: Shreyansh Ray").pack(pady=(0,22))
    tk.Button(win,text="Launch Autonomous AI",width=28,command=lambda:launch(pwd)).pack(pady=6);tk.Button(win,text="Change password",width=28,command=change_password).pack(pady=6);tk.Button(win,text="Exit",width=28,command=root.destroy).pack(pady=6)
    root.mainloop()
if __name__=="__main__":main()
