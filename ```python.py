```python
# -*- coding: utf-8 -*-
import sys, os, traceback

_log = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'error.log'), 'w', encoding='utf-8')
_log.write("=== 起動開始 ===\n"); _log.flush()

try:
    import re, json, smtplib
    from email.message import EmailMessage
    from PyPDF2 import PdfReader
    from tkinter import Tk, StringVar, Label, Button, Entry, Frame
    from tkinter import filedialog, messagebox
    from tkinter.scrolledtext import ScrolledText
except Exception:
    _log.write("=== インポートエラー ===\n" + traceback.format_exc())
    _log.close()
    sys.exit(1)

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

def save_config():
    config = {
        'resume': resume_path.get(), 'career': career_path.get(),
        'smtp_host': smtp_host_var.get(), 'smtp_port': smtp_port_var.get(),
        'smtp_user': smtp_user_var.get(), 'smtp_pass': smtp_pass_var.get(),
    }
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f)
    except Exception:
        pass

def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def extract_emails(path):
    if not path or not os.path.isfile(path):
        return []
    try:
        reader = PdfReader(path)
        text = "".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return []
    return sorted({m.group(0) for m in re.finditer(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)})

def on_close():
    save_config()
    root.destroy()

def choose_file(var, label, title, filetypes):
    path = filedialog.askopenfilename(title=title, filetypes=filetypes)
    if path:
        var.set(path)
        label.config(text=os.path.basename(path))
        save_config()

def choose_pdf():
    choose_file(pdf_path, pdf_label, "求人票PDFを選択", [("PDF Files", "*.pdf"), ("All Files", "*")])
    if pdf_path.get():
        emails = extract_emails(pdf_path.get())
        if emails:
            recipient_var.set(", ".join(emails))
            found_label.config(text="抽出: " + ", ".join(emails))
        else:
            found_label.config(text="メールアドレスが見つかりませんでした。")

def send_email():
    to_addrs = [a.strip() for a in recipient_var.get().split(",") if a.strip()]
    if not to_addrs:
        messagebox.showwarning("送信先なし", "送信先を入力してください。")
        return
    files = [resume_path.get(), career_path.get(), cover_path.get()]
    attachments = [os.path.basename(p) for p in files if p]
    summary = "送信先: {}\n件名: {}\n添付: {}".format(", ".join(to_addrs), subject_var.get(), ", ".join(attachments))
    if not messagebox.askyesno("送信確認", summary + "\n\n送信しますか？"):
        return
    msg = EmailMessage()
    msg["Subject"] = subject_var.get()
    msg["From"] = sender_var.get().strip() or smtp_user_var.get().strip()
    msg["To"] = ", ".join(to_addrs)
    msg.set_content(body_text.get("1.0", "end"))
    for p in files:
        if p:
            try:
                with open(p, "rb") as f:
                    data = f.read()
                msg.add_attachment(data, maintype="application", subtype="octet-stream", filename=os.path.basename(p))
            except Exception as exc:
                messagebox.showerror("添付エラー", str(exc)); return
    try:
        port = int(smtp_port_var.get()) if smtp_port_var.get().isdigit() else 587
        if port == 465:
            server = smtplib.SMTP_SSL(smtp_host_var.get().strip(), port, timeout=60)
        else:
            server = smtplib.SMTP(smtp_host_var.get().strip(), port, timeout=60)
            server.starttls()
        if smtp_user_var.get().strip():
            server.login(smtp_user_var.get().strip(), smtp_pass_var.get().strip())
        server.send_message(msg)
        server.quit()
        save_config()
        messagebox.showinfo("送信完了", "送信しました。")
    except Exception as exc:
        messagebox.showerror("送信失敗", str(exc))

try:
    root = Tk()
    root.title("ハローワーク求人PDFメール送信ツール")
    resume_path = StringVar(); career_path = StringVar(); pdf_path = StringVar()
    cover_path = StringVar(); recipient_var = StringVar()
    subject_var = StringVar(value="応募のご挨拶"); sender_var = StringVar()
    smtp_host_var = StringVar(value="smtp.example.com")
    smtp_port_var = StringVar(value="587")
    smtp_user_var = StringVar(); smtp_pass_var = StringVar()
    cfg = load_config()
    resume_path.set(cfg.get('resume', '')); career_path.set(cfg.get('career', ''))
    smtp_host_var.set(cfg.get('smtp_host', 'smtp.example.com'))
    smtp_port_var.set(cfg.get('smtp_port', '587'))
    smtp_user_var.set(cfg.get('smtp_user', '')); smtp_pass_var.set(cfg.get('smtp_pass', ''))
    root.protocol("WM_DELETE_WINDOW", on_close)
    Label(root, text="① 履歴書・職務経歴書を選択").pack(anchor="w", padx=10, pady=5)
    frame1 = Frame(root); frame1.pack(fill="x", padx=10)
    resume_label = Label(frame1, text=os.path.basename(resume_path.get()) if resume_path.get() else "履歴書未選択", width=30, anchor="w")
    resume_label.pack(side="left")
    Button(frame1, text="履歴書選択", command=lambda: choose_file(resume_path, resume_label, "履歴書を選択", [("PDF or DOCX", "*.pdf;*.docx"), ("All Files", "*")])).pack(side="left", padx=5)
    career_label = Label(frame1, text=os.path.basename(career_path.get()) if career_path.get() else "職務経歴書未選択", width=30, anchor="w")
    career_label.pack(side="left", padx=5)
    Button(frame1, text="職務経歴書選択", command=lambda: choose_file(career_path, career_label, "職務経歴書を選択", [("PDF or DOCX", "*.pdf;*.docx"), ("All Files", "*")])).pack(side="left", padx=5)
    Label(root, text="② 求人票PDFを選択してアドレス抽出").pack(anchor="w", padx=10, pady=5)
    frame2 = Frame(root); frame2.pack(fill="x", padx=10)
    pdf_label = Label(frame2, text="求人票未選択", width=50, anchor="w"); pdf_label.pack(side="left")
    Button(frame2, text="PDF選択", command=choose_pdf).pack(side="left", padx=5)
    found_label = Label(root, text="メールアドレス抽出結果がここに表示されます。", anchor="w", justify="left")
    found_label.pack(fill="x", padx=10)
    Label(root, text="送信先メールアドレス (編集可)").pack(anchor="w", padx=10, pady=2)
    Entry(root, textvariable=recipient_var, width=100).pack(fill="x", padx=10)
    Label(root, text="③ 紹介状の選択").pack(anchor="w", padx=10, pady=5)
    frame3 = Frame(root); frame3.pack(fill="x", padx=10)
    cover_label = Label(frame3, text="紹介状未選択", width=50, anchor="w"); cover_label.pack(side="left")
    Button(frame3, text="紹介状選択", command=lambda: choose_file(cover_path, cover_label, "紹介状を選択", [("PDF or DOCX", "*.pdf;*.docx"), ("All Files", "*")])).pack(side="left", padx=5)
    Label(root, text="④ 件名・本文").pack(anchor="w", padx=10, pady=5)
    Entry(root, textvariable=subject_var, width=100).pack(fill="x", padx=10)
    body_text = ScrolledText(root, width=100, height=10); body_text.pack(padx=10, pady=5)
    body_text.insert("1.0", "このたびは貴社の求人に応募いたします。添付の履歴書・職務経歴書をご確認ください。")
    Label(root, text="SMTP設定").pack(anchor="w", padx=10, pady=5)
    frame4 = Frame(root); frame4.pack(fill="x", padx=10)
    Label(frame4, text="SMTPホスト").grid(row=0, column=0, sticky="w")
    Entry(frame4, textvariable=smtp_host_var, width=25).grid(row=0, column=1, padx=5)
    Label(frame4, text="ポート").grid(row=0, column=2, sticky="w")
    Entry(frame4, textvariable=smtp_port_var, width=8).grid(row=0, column=3, padx=5)
    Label(frame4, text="ユーザー").grid(row=0, column=4, sticky="w")
    Entry(frame4, textvariable=smtp_user_var, width=25).grid(row=0, column=5, padx=5)
    Label(frame4, text="差出人").grid(row=1, column=0, sticky="w", pady=5)
    Entry(frame4, textvariable=sender_var, width=25).grid(row=1, column=1, padx=5, pady=5)
    Label(frame4, text="パスワード").grid(row=1, column=2, sticky="w", pady=5)
    Entry(frame4, textvariable=smtp_pass_var, show="*", width=25).grid(row=1, column=3, columnspan=3, padx=5, pady=5)
    Button(root, text="⑤ 送信確認と送信", command=send_email, bg="#4a90e2", fg="white").pack(pady=10)
    root.mainloop()
except Exception:
    _log.write("=== 実行時エラー ===\n" + traceback.format_exc())
finally:
    _log.close()
```