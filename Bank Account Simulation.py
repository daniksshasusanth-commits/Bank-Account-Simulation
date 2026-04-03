#!/usr/bin/env python3
"""
Indian Bank - Single-file enhanced app
- Improved login robustness (normalizes usernames, auto-hashes legacy plain passwords)
- Atomic save to avoid file corruption
- Auto-login after register to avoid "works once" confusion
- Export preview in-app with Open / Reveal / Copy
- UI polish: attention-grabbing header, button styles, spacing and input focus
Save as: indian_bank_app.py
"""

import os
import json
import hashlib
import threading
import subprocess
import sys
import webbrowser
from datetime import datetime, timedelta

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

# Optional libs (install if missing)
try:
    from PIL import Image, ImageTk
except Exception:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
    from PIL import Image, ImageTk

try:
    from playsound import playsound
except Exception:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playsound"])
    from playsound import playsound

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except Exception:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------------- config ----------------
DATA_FILE = "users.json"
LOGO_FILE = "bank_logo.png"
SOUND_FILE = "success.wav"

PALETTE = {
    "primary": "#003366",
    "accent": "#FFD700",
    "bg_light": "#FFF8E7",
    "btn_primary": "#002147",
    "text": "#2E2E2E",
    "saffron": "#FF9933"
}

CATEGORY_KEYWORDS = {
    "Salary": ["salary", "pay", "payout", "employ", "employer"],
    "Food": ["restaurant", "cafe", "food", "coffee", "dine", "meal", "burger"],
    "Groceries": ["grocery", "supermarket", "mart", "veg", "vegetable", "milk"],
    "Bills": ["bill", "electricity", "water", "internet", "mobile", "rent"],
    "Transport": ["uber", "ola", "taxi", "bus", "train", "metro", "petrol", "fuel"],
    "Shopping": ["amazon", "flipkart", "shopping", "store"],
    "Health": ["hospital", "clinic", "doctor", "pharmacy", "medicine"],
    "Entertainment": ["movie", "netflix", "prime", "game", "concert"],
    "Other": []
}

# ---------------- utilities ----------------
def center_window(win, width=760, height=620):
    win.update_idletasks()
    sw = win.winfo_screenwidth(); sh = win.winfo_screenheight()
    x = (sw - width) // 2; y = (sh - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")

def play_sound_nonblocking():
    def _p():
        try:
            if os.path.exists(SOUND_FILE):
                playsound(SOUND_FILE, block=True)
        except Exception:
            pass
    threading.Thread(target=_p, daemon=True).start()

def hash_password(pw: str):
    return hashlib.sha256(pw.encode()).hexdigest()

def _looks_like_sha256(s: str):
    if not isinstance(s, str): return False
    if len(s) != 64: return False
    try:
        int(s, 16); return True
    except Exception:
        return False

def load_users():
    # safe load + normalize username keys and migrate plain-text to hashed passwords
    users = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                raw = json.load(f) or {}
        except Exception:
            raw = {}
    else:
        raw = {}
    for k, v in raw.items():
        nk = k.strip()
        if not isinstance(v, dict): continue
        v = dict(v)
        pw = v.get("password", "")
        # if stored password isn't a sha256 hex, assume plain-text and hash it
        if isinstance(pw, str) and not _looks_like_sha256(pw):
            try:
                v["password"] = hash_password(pw)
            except Exception:
                v["password"] = ""
        users[nk] = v
    return users

def save_users(users):
    # atomic write to avoid corruption
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(users, f, indent=4)
    try:
        os.replace(tmp, DATA_FILE)
    except Exception:
        # fallback
        os.remove(DATA_FILE) if os.path.exists(DATA_FILE) else None
        os.replace(tmp, DATA_FILE)

def categorize_transaction(memo: str):
    text = (memo or "").lower()
    for cat, keys in CATEGORY_KEYWORDS.items():
        for k in keys:
            if k in text:
                return cat
    if "salary" in text or "pay" in text:
        return "Salary"
    if text.strip() == "":
        return "Other"
    return "Other"

# ---------------- splash ----------------
def splash_screen():
    s = tk.Tk()
    s.title("Indian Bank")
    s.configure(bg=PALETTE["bg_light"])
    center_window(s, 460, 320)
    header = tk.Frame(s, bg=PALETTE["bg_light"])
    header.pack(expand=True, fill="both")
    try:
        logo = Image.open(LOGO_FILE).resize((120,120))
        img = ImageTk.PhotoImage(logo)
        tk.Label(header, image=img, bg=PALETTE["bg_light"]).pack(pady=6)
        s.logo_img = img
    except Exception:
        tk.Label(header, text="🏦", font=("Segoe UI", 72), bg=PALETTE["bg_light"]).pack(pady=6)
    tk.Label(header, text="INDIAN BANK", font=("Segoe UI", 22, "bold"),
             fg=PALETTE["primary"], bg=PALETTE["bg_light"]).pack()
    tk.Label(header, text="Your Trusted Financial Partner", font=("Segoe UI", 10), bg=PALETTE["bg_light"]).pack(pady=(4,14))
    s.after(900, lambda: [s.destroy(), login_screen()])
    s.mainloop()

# ---------------- login screen ----------------
def login_screen():
    users = load_users()
    root = tk.Tk()
    root.title("Indian Bank - Login")
    root.configure(bg=PALETTE["bg_light"])
    center_window(root, 560, 480)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("Card.TFrame", background="white")
    style.configure("Primary.TButton", foreground="white", background=PALETTE["primary"])
    style.configure("Accent.TButton", foreground=PALETTE["primary"], background=PALETTE["accent"])

    container = ttk.Frame(root, padding=18)
    container.pack(expand=True, fill="both")
    card = ttk.Frame(container, padding=(14,16), style="Card.TFrame")
    card.pack(expand=True, fill="both", padx=10, pady=6)

    # polished header
    header = tk.Frame(card, bg="white")
    header.pack(fill="x")
    left = tk.Frame(header, bg="white")
    left.pack(side="left", padx=6)
    try:
        logo = Image.open(LOGO_FILE).resize((72,72))
        logo_img = ImageTk.PhotoImage(logo)
        tk.Label(left, image=logo_img, bg="white").pack()
        root.logo_img = logo_img
    except Exception:
        tk.Label(left, text="🏦", font=("Segoe UI", 36), bg="white").pack()
    tk.Label(header, text="Indian Bank", font=("Segoe UI", 20, "bold"), bg="white", fg=PALETTE["primary"]).pack(side="left", padx=8)
    tk.Label(card, text="Welcome — Sign in or create an account", background="white").pack(pady=(6,8))

    frm = ttk.Frame(card, padding=(8,6), style="Card.TFrame")
    frm.pack(pady=6, padx=6, fill="x")
    ttk.Label(frm, text="Username:", background="white").grid(row=0, column=0, sticky="w", pady=(6,4))
    user_entry = ttk.Entry(frm, width=36); user_entry.grid(row=0, column=1, padx=6, pady=(6,4))
    ttk.Label(frm, text="Password:", background="white").grid(row=1, column=0, sticky="w", pady=4)
    pw_entry = ttk.Entry(frm, show="*", width=36); pw_entry.grid(row=1, column=1, padx=6, pady=4)

    # helpful quick links
    hint = tk.Label(card, text="Tip: Use 'Register' to create an account. Use 'Forgot Password' to reset.", bg="white", fg="#666", font=("Segoe UI",8))
    hint.pack(pady=(6,8))

    user_entry.focus_set()

    def do_login():
        nonlocal users
        u = user_entry.get().strip()
        p = pw_entry.get().strip()
        if not u or not p:
            messagebox.showerror("Error", "Enter username and password"); return
        users = load_users()  # reload to ensure most recent file
        if u not in users:
            messagebox.showerror("Error", "Invalid credentials"); return
        h = hash_password(p)
        if users[u].get("password") == h:
            play_sound_nonblocking()
            root.destroy()
            open_transaction_screen(u, users)
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def do_register():
        nonlocal users
        u = user_entry.get().strip(); p = pw_entry.get().strip()
        if not u or not p:
            messagebox.showerror("Error", "Enter username and password"); return
        users = load_users()
        if u in users:
            messagebox.showwarning("Exists", "User already exists"); return
        confirm = simpledialog.askstring("Confirm Password", "Re-enter password to confirm:", show="*")
        if confirm is None or confirm.strip() == "":
            messagebox.showinfo("Cancelled", "Registration cancelled"); return
        if confirm != p:
            messagebox.showerror("Mismatch", "Passwords do not match"); return
        sec = simpledialog.askstring("Security (optional)", "Set a security answer for password reset (optional):")
        users[u] = {"password": hash_password(p), "balance": 0.0, "transactions": [], "security": sec or ""}
        save_users(users)
        play_sound_nonblocking()
        messagebox.showinfo("Registered", "Account created! You are now logged in.")
        root.destroy()
        open_transaction_screen(u, users)

    def forgot_password():
        nonlocal users
        users = load_users()
        u = simpledialog.askstring("Forgot Password", "Enter your username:")
        if not u:
            return
        if u not in users:
            messagebox.showerror("Error", "User not found"); return
        sec = users[u].get("security", "")
        if sec:
            ans = simpledialog.askstring("Security Question", "Enter your security answer:", show="*")
            if ans is None:
                return
            if ans != sec:
                messagebox.showerror("Error", "Security answer mismatch"); return
        else:
            if not messagebox.askyesno("Confirm", "No security answer is set. Allow password reset anyway?"):
                return
        newp = simpledialog.askstring("Reset Password", "Enter new password:", show="*")
        if not newp:
            messagebox.showinfo("Cancelled", "Password reset cancelled"); return
        newp2 = simpledialog.askstring("Reset Password", "Re-enter new password:", show="*")
        if newp2 != newp:
            messagebox.showerror("Mismatch", "Passwords do not match"); return
        users[u]["password"] = hash_password(newp)
        save_users(users)
        messagebox.showinfo("Reset", "Password has been reset successfully.")

    btn_frame = ttk.Frame(card, style="Card.TFrame")
    btn_frame.pack(pady=(6,2))
    b_login = ttk.Button(btn_frame, text="Login", command=do_login, width=16, style="Primary.TButton")
    b_login.pack(side="left", padx=6)
    b_reg = ttk.Button(btn_frame, text="Register", command=do_register, width=16, style="Accent.TButton")
    b_reg.pack(side="left", padx=6)
    b_fp = ttk.Button(btn_frame, text="Forgot Password", command=forgot_password, width=16)
    b_fp.pack(side="left", padx=6)

    root.bind("<Return>", lambda e: do_login())
    root.mainloop()

# ---------------- dashboard ----------------
def open_transaction_screen(username, users):
    win = tk.Tk()
    win.title(f"Indian Bank - {username}")
    win.configure(bg=PALETTE["bg_light"])
    center_window(win, 920, 740)

    theme = {"bg": PALETTE["bg_light"], "fg": PALETTE["text"]}

    def apply_theme():
        win.configure(bg=theme["bg"])
        for w in win.winfo_children():
            _apply_theme_recursive(w)

    def _apply_theme_recursive(widget):
        try:
            if isinstance(widget, (tk.Label, tk.Button, tk.Entry, tk.Frame, tk.Canvas)):
                widget.configure(bg=theme["bg"], fg=theme["fg"])
        except Exception:
            pass
        for child in getattr(widget, "winfo_children", lambda: [])():
            _apply_theme_recursive(child)

    # top header banner - attention grabbing
    banner = tk.Frame(win, bg=PALETTE["primary"], height=90)
    banner.pack(fill="x")
    try:
        logo = Image.open(LOGO_FILE).resize((64,64))
        limg = ImageTk.PhotoImage(logo)
        tk.Label(banner, image=limg, bg=PALETTE["primary"]).pack(side="left", padx=12, pady=10)
        banner.logo = limg
    except Exception:
        tk.Label(banner, text="🏦", font=("Segoe UI", 28), bg=PALETTE["primary"], fg="white").pack(side="left", padx=12, pady=10)
    tk.Label(banner, text=f"Welcome, {username}", font=("Segoe UI", 18, "bold"), bg=PALETTE["primary"], fg="white").pack(side="left")
    tk.Label(banner, text="— Your personal finance companion", bg=PALETTE["primary"], fg=PALETTE["accent"]).pack(side="left", padx=10)

    # account button
    def account_settings():
        def change_password():
            cur = simpledialog.askstring("Current Password", "Enter current password:", show="*")
            if cur is None:
                return
            if hash_password(cur) != users[username]["password"]:
                messagebox.showerror("Error", "Current password incorrect"); return
            newp = simpledialog.askstring("New Password", "Enter new password:", show="*")
            if not newp:
                return
            newp2 = simpledialog.askstring("Confirm New Password", "Re-enter new password:", show="*")
            if newp2 != newp:
                messagebox.showerror("Mismatch", "Passwords do not match"); return
            users[username]["password"] = hash_password(newp)
            save_users(users)
            messagebox.showinfo("Changed", "Password changed successfully.")
        def change_security():
            newsec = simpledialog.askstring("Security Answer", "Enter a new security answer (leave blank to clear):")
            if newsec is None:
                return
            users[username]["security"] = newsec or ""
            save_users(users)
            messagebox.showinfo("Updated", "Security answer updated.")
        w = tk.Toplevel(win); w.title("Account Settings"); center_window(w, 420, 280)
        ttk_frame = ttk.Frame(w, padding=12); ttk_frame.pack(fill="both", expand=True)
        ttk.Label(ttk_frame, text=f"Account: {username}", font=("Segoe UI", 12, "bold")).pack(pady=(4,8))
        ttk.Button(ttk_frame, text="Change Password", command=change_password).pack(fill="x", pady=6)
        ttk.Button(ttk_frame, text="Change / Clear Security Answer", command=change_security).pack(fill="x", pady=6)
        ttk.Button(ttk_frame, text="Close", command=w.destroy).pack(pady=(10,2))

    acct_btn = ttk.Button(banner, text="Account", command=account_settings)
    acct_btn.pack(side="right", padx=12, pady=18)

    # Balance card
    balance_frame = tk.Frame(win, bg=theme["bg"], pady=10)
    balance_frame.pack(fill="x", padx=12, pady=(10,0))
    bal_lbl = tk.Label(balance_frame, text="Available Balance", bg=theme["bg"], fg="#444")
    bal_lbl.pack(anchor="w")
    balance_var = tk.StringVar(value=f"₹{users[username]['balance']:.2f}")
    balance_amount = tk.Label(balance_frame, textvariable=balance_var, font=("Segoe UI", 20, "bold"), bg=theme["bg"], fg=PALETTE["primary"])
    balance_amount.pack(anchor="w")

    # entry area
    entry_frame = tk.Frame(win, bg=theme["bg"]); entry_frame.pack(pady=8, padx=12, fill="x")
    tk.Label(entry_frame, text="Amount:", bg=theme["bg"]).grid(row=0, column=0, sticky="e")
    amount_entry = tk.Entry(entry_frame, width=20); amount_entry.grid(row=0, column=1, padx=8)
    amount_entry.insert(0, "0.00")
    def _clear_default(e):
        if amount_entry.get().strip() == "0.00":
            amount_entry.delete(0, tk.END)
    amount_entry.bind("<FocusIn>", _clear_default)
    amount_entry.focus_set()
    tk.Label(entry_frame, text="Memo (optional):", bg=theme["bg"]).grid(row=1, column=0, sticky="e")
    memo_entry = tk.Entry(entry_frame, width=56); memo_entry.grid(row=1, column=1, padx=8, pady=6)

    # transactions table
    cols = ("Type","Amount","Category","Memo","Time")
    tree = ttk.Treeview(win, columns=cols, show="headings", height=14)
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=160 if c == "Memo" else 110, anchor="center")
    tree.pack(padx=12, pady=8, fill="both", expand=False)

    for t in reversed(users[username].get("transactions", [])):
        tree.insert("", tk.END, values=(t["type"], f"₹{t['amount']:.2f}", t.get("category","Other"), t.get("memo",""), t.get("time","")))

    def add_transaction_local(tx_type):
        s = amount_entry.get().strip(); memo = memo_entry.get().strip()
        try:
            if s == "" or s == "0.00":
                raise ValueError("Enter amount")
            amt = float(s)
            if amt <= 0:
                messagebox.showerror("Error", "Enter an amount greater than 0"); return
            if tx_type == "Withdraw" and amt > users[username]["balance"]:
                messagebox.showerror("Error", "Insufficient funds"); return
            cat = categorize_transaction(memo)
            now = datetime.now().strftime("%d-%m-%Y %H:%M")
            t = {"type": tx_type, "amount": amt, "memo": memo, "time": now, "category": cat}
            users[username]["transactions"].append(t)
            if tx_type == "Deposit":
                users[username]["balance"] += amt
            else:
                users[username]["balance"] -= amt
            save_users(users)
            tree.insert("", 0, values=(t["type"], f"₹{t['amount']:.2f}", t["category"], t["memo"], t["time"]))
            balance_var.set(f"₹{users[username]['balance']:.2f}")
            play_sound_nonblocking()
            messagebox.showinfo("Success", f"{tx_type} of ₹{amt:.2f} successful")
            amount_entry.delete(0, tk.END); amount_entry.insert(0, "0.00")
            memo_entry.delete(0, tk.END)
            amount_entry.focus_set()
        except ValueError:
            messagebox.showerror("Error", "Enter a valid numeric amount")

    btn_frame = tk.Frame(win, bg=theme["bg"]); btn_frame.pack(pady=6)
    ttk.Button(btn_frame, text="Deposit", command=lambda: add_transaction_local("Deposit"), width=14).pack(side="left", padx=6)
    ttk.Button(btn_frame, text="Withdraw", command=lambda: add_transaction_local("Withdraw"), width=14).pack(side="left", padx=6)
    ttk.Button(btn_frame, text="Analyze (AI Insights)", command=lambda: show_ai_insights(username, users), width=18).pack(side="left", padx=6)
    ttk.Button(btn_frame, text="Chat with AI Assistant", command=lambda: open_offline_ai_chat(username, users), width=20).pack(side="left", padx=6)

    amount_entry.bind("<Return>", lambda e: add_transaction_local("Deposit"))

    lower_frame = tk.Frame(win, bg=theme["bg"]); lower_frame.pack(pady=8, fill="x", padx=12)
    ttk.Button(lower_frame, text="Show Summary Chart", command=lambda: show_summary_chart(username, users)).pack(side="left", padx=6)
    ttk.Button(lower_frame, text="Export Transactions (JSON)", command=lambda: export_transactions(username, users, tree), width=24).pack(side="left", padx=6)
    ttk.Button(lower_frame, text="Clear All Transactions", command=lambda: clear_transactions(username, users, tree, balance_var)).pack(side="left", padx=6)
    ttk.Button(win, text="Logout", command=lambda: [win.destroy(), login_screen()]).pack(pady=10)

    apply_theme()
    win.mainloop()

# ---------------- actions ----------------
def clear_transactions(username, users, tree, balance_var):
    if not messagebox.askyesno("Confirm", "Delete ALL transactions for this user?"):
        return
    users[username]["transactions"] = []
    users[username]["balance"] = 0.0
    save_users(users)
    for i in tree.get_children(): tree.delete(i)
    balance_var.set(f"₹{users[username]['balance']:.2f}")
    messagebox.showinfo("Cleared", "All transactions cleared.")

def export_transactions(username, users, tree_widget=None):
    txs = users[username].get("transactions", [])
    fname = os.path.abspath(f"{username}_transactions_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
    with open(fname, "w") as f:
        json.dump(txs, f, indent=4)
    # preview window in-app
    w = tk.Toplevel(); w.title(f"{username} - Transactions JSON"); center_window(w, 720, 520)
    txt = tk.Text(w, wrap="none", padx=6, pady=6)
    try:
        with open(fname, "r") as f:
            content = f.read()
    except Exception:
        content = json.dumps(txs, indent=4)
    txt.insert("1.0", content); txt.configure(state="disabled")
    txt.pack(fill="both", expand=True, padx=8, pady=(8,0))
    btnf = tk.Frame(w); btnf.pack(fill="x", pady=8)
    def open_file():
        try:
            if sys.platform == "darwin":
                subprocess.call(["open", fname])
            elif sys.platform.startswith("win"):
                os.startfile(fname)
            else:
                subprocess.call(["xdg-open", fname])
        except Exception:
            webbrowser.open("file://" + fname)
    def reveal_in_folder():
        try:
            if sys.platform == "darwin":
                subprocess.call(["open", "-R", fname])
            elif sys.platform.startswith("win"):
                subprocess.call(["explorer", "/select,", fname])
            else:
                subprocess.call(["xdg-open", os.path.dirname(fname)])
        except Exception:
            pass
    def copy_clipboard():
        w.clipboard_clear(); w.clipboard_append(content)
        messagebox.showinfo("Copied", "JSON copied to clipboard.")
    tk.Button(btnf, text="Open File", command=open_file).pack(side="left", padx=6)
    tk.Button(btnf, text="Reveal in Folder", command=reveal_in_folder).pack(side="left", padx=6)
    tk.Button(btnf, text="Copy JSON", command=copy_clipboard).pack(side="left", padx=6)
    tk.Button(btnf, text="Close", command=w.destroy).pack(side="right", padx=6)
    messagebox.showinfo("Exported", f"Transactions exported to: {fname}")

# ---------------- charts ----------------
def show_summary_chart(username, users):
    txs = users[username].get("transactions", [])
    if not txs:
        messagebox.showinfo("No Data", "No transactions to chart."); return
    deposits = sum(t["amount"] for t in txs if t["type"] == "Deposit")
    withdrawals = sum(t["amount"] for t in txs if t["type"] == "Withdraw")
    cat_totals = {}
    for t in txs:
        if t["type"] == "Withdraw":
            c = t.get("category", "Other"); cat_totals[c] = cat_totals.get(c, 0) + t["amount"]
    win_chart = tk.Toplevel(); win_chart.title(f"{username} - Transaction Summary"); center_window(win_chart, 900, 520)
    fig = Figure(figsize=(8.5, 4.5), dpi=100)
    ax1 = fig.add_subplot(121); ax2 = fig.add_subplot(122)
    if deposits == 0 and withdrawals == 0:
        ax1.text(0.5, 0.5, "No deposit/withdrawal amounts", ha="center", va="center")
        ax1.set_title("Deposits vs Withdrawals")
    else:
        ax1.pie([deposits if deposits > 0 else 0.0001, withdrawals if withdrawals > 0 else 0.0001],
                labels=[f"Deposits\n₹{deposits:.2f}", f"Withdrawals\n₹{withdrawals:.2f}"], autopct="%1.1f%%")
        ax1.set_title("Deposits vs Withdrawals")
    labels = list(cat_totals.keys())
    sizes = list(cat_totals.values())
    if not sizes or sum(sizes) == 0:
        ax2.text(0.5, 0.5, "No withdrawals to chart", ha="center", va="center")
        ax2.set_title("Withdrawal by Category")
    else:
        ax2.pie([s if s > 0 else 0.0001 for s in sizes], labels=labels, autopct="%1.1f%%"); ax2.set_title("Withdrawal by Category")
    canvas = FigureCanvasTkAgg(fig, master=win_chart); canvas.draw(); canvas.get_tk_widget().pack(fill="both", expand=True)

# ---------------- insights ----------------
def show_ai_insights(username, users):
    txs = users[username].get("transactions", [])
    if not txs:
        messagebox.showinfo("No Data", "No transactions to analyze."); return
    for t in txs:
        if "category" not in t: t["category"] = categorize_transaction(t.get("memo", ""))
    save_users(users)
    total_deposits = sum(t["amount"] for t in txs if t["type"] == "Deposit")
    total_withdraws = sum(t["amount"] for t in txs if t["type"] == "Withdraw")
    withdraws = [t for t in txs if t["type"] == "Withdraw"]
    cat_totals = {}
    for t in withdraws: cat_totals[t["category"]] = cat_totals.get(t["category"], 0) + t["amount"]
    top_cats = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)[:3]
    avg_withdraw = (sum(t["amount"] for t in withdraws) / max(1, len(withdraws)))
    now = datetime.now(); daily_net = {}
    for t in txs:
        try:
            ts = datetime.strptime(t["time"], "%d-%m-%Y %H:%M")
        except Exception:
            ts = now
        day = ts.date(); net = t["amount"] if t["type"] == "Deposit" else -t["amount"]; daily_net[day] = daily_net.get(day, 0) + net
    last30 = [daily_net.get(now.date() - timedelta(days=i), 0) for i in range(30)]
    avg_daily_net = sum(last30) / 30
    forecast_next_month = avg_daily_net * 30
    suggestions = []
    if avg_withdraw > (total_deposits * 0.5 if total_deposits > 0 else 1000):
        suggestions.append("High average withdrawals compared to deposits — review subscriptions and discretionary spend.")
    if top_cats:
        suggestions.append(f"Top spending category: {top_cats[0][0]} (₹{top_cats[0][1]:.2f}). Consider setting a budget.")
    suggestions.append("Tip: 50/30/20 rule — needs / wants / savings.")
    lines = [
        f"Total Deposits: ₹{total_deposits:.2f}",
        f"Total Withdrawals: ₹{total_withdraws:.2f}",
        f"Average Withdrawal: ₹{avg_withdraw:.2f}",
        f"Forecast (next 30 days net change): ₹{forecast_next_month:.2f}",
        "",
        "Top Spending Categories:"
    ]
    for c, a in top_cats: lines.append(f" - {c}: ₹{a:.2f}")
    lines.append(""); lines.append("Suggestions:")
    for s in suggestions: lines.append(f" • {s}")
    w = tk.Toplevel(); w.title(f"{username} - AI Insights"); center_window(w, 520, 420)
    tbox = tk.Text(w, wrap="word", padx=10, pady=10); tbox.insert("1.0", "\n".join(lines)); tbox.configure(state="disabled"); tbox.pack(fill="both", expand=True, padx=8, pady=8)
    def quick_budget():
        if not top_cats:
            messagebox.showinfo("No data", "No categories to set budget for."); return
        cat = top_cats[0][0]; val = simpledialog.askfloat("Set Budget", f"Set monthly budget for {cat} (₹):", minvalue=0)
        if val is None: return
        messagebox.showinfo("Budget Set", f"Budget ₹{val:.2f} set for {cat}. (Local note only.)")
    ttk.Button(w, text="Quick: Set Budget for Top Category", command=quick_budget).pack(pady=6)

# ---------------- chat ----------------
def open_offline_ai_chat(username, users):
    chat_win = tk.Toplevel(); chat_win.title("AI Assistant - Offline"); center_window(chat_win, 700, 520)
    frame = tk.Frame(chat_win); frame.pack(fill="both", expand=True, padx=8, pady=8)
    txt = tk.Text(frame, wrap="word", state="disabled", bg="#f8f8f8"); txt.pack(fill="both", expand=True, pady=6)
    entry_frame = tk.Frame(frame); entry_frame.pack(fill="x", pady=4)
    entry = tk.Entry(entry_frame); entry.pack(side="left", fill="x", expand=True, padx=4)
    send_btn = tk.Button(entry_frame, text="Send", bg=PALETTE["primary"], fg="white")
    send_btn.pack(side="left", padx=6)
    def append(role, message):
        txt.config(state="normal"); txt.insert("end", f"{role}: {message}\n\n"); txt.see("end"); txt.config(state="disabled")
    append("System", "You are an offline financial assistant. Ask about budgeting, transactions, or app help.")
    def offline_reply(user_message):
        m = user_message.lower()
        if any(k in m for k in ("budget", "save", "saving", "savings")):
            return ("Try the 50/30/20 rule: 50% for needs, 30% for wants, 20% for savings. "
                    "Set monthly limits for your top spending categories and track daily expenses.")
        if any(k in m for k in ("forecast", "predict", "future")):
            return ("Open 'Analyze (AI Insights)' in the dashboard; it will compute a 30-day net forecast.")
        if any(k in m for k in ("category", "categorize", "auto", "memo")):
            return ("Transactions are auto-categorized from memo keywords (e.g., 'amazon' -> Shopping). Add a memo for better results.")
        if any(k in m for k in ("balance", "how much", "current")):
            bal = users[username]["balance"]
            return f"Your current balance is ₹{bal:.2f}."
        if any(k in m for k in ("transfer", "send", "pay")):
            return ("This demo doesn't perform real transfers. Use Deposit/Withdraw to simulate transactions locally.")
        if any(k in m for k in ("help", "how to", "use app")):
            return ("Use 'Deposit' to add funds and 'Withdraw' to remove funds. Use 'Analyze' for insights and 'Show Summary Chart' for visuals.")
        return ("I don't have internet access, but I can still help: try asking for 'budget tips', 'explain forecast', or 'top categories'.")
    def send_msg(event=None):
        msg = entry.get().strip()
        if not msg: return
        append("You", msg); entry.delete(0, tk.END)
        append("AI", "Thinking...")
        def worker():
            resp = offline_reply(msg)
            def update():
                append("AI", resp)
            chat_win.after(300, update)
        threading.Thread(target=worker, daemon=True).start()
    send_btn.config(command=send_msg); entry.bind("<Return>", send_msg)

# ---------------- entry point ----------------
if __name__ == "__main__":
    if not os.path.exists(DATA_FILE):
        save_users({})
    splash_screen()
