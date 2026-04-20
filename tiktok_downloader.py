import customtkinter as ctk
import threading
import sqlite3
import subprocess
import os
import time
import random
import math
from tkinter import filedialog

# ===== CONFIG =====
DB = "videos.db"
num_threads = 2
download_count = 0

# ===== DATABASE =====
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        id TEXT PRIMARY KEY,
        url TEXT,
        downloaded_at TEXT
    )
    """)
    conn.commit()
    conn.close()

def is_downloaded(video_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT 1 FROM videos WHERE id=?", (video_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def save_video(video_id, url):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO videos VALUES (?, ?, datetime('now'))", (video_id, url))
    conn.commit()
    conn.close()

# ===== SMART DELAY =====
def smart_delay():
    t = time.time() % 60
    base = random.uniform(1.2, 2.5)
    wave = abs(math.sin(t))
    return base + wave

# ===== USER AGENT =====
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
    "Mozilla/5.0 (Linux; Android 12)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
]

# ===== DOWNLOAD =====
def download_video(url, folder, log_box):
    global download_count

    video_id = url.split("/")[-1].split("?")[0]

    if is_downloaded(video_id):
        log_box.insert("end", f"⏩ Bỏ qua (đã tải): {url}\n")
        log_box.see("end")
        return

    time.sleep(smart_delay())

    ua = random.choice(USER_AGENTS)

    output_template = os.path.join(
        folder,
        "%(uploader)s/%(uploader)s_%(id)s_%(title).30s.%(ext)s"
    )

    cmd = [
        "yt-dlp",
        "--restrict-filenames",
        "--user-agent", ua,
        "-o", output_template,
        url
    ]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    for line in process.stdout:
        log_box.insert("end", line)
        log_box.see("end")

    save_video(video_id, url)
    download_count += 1

    # nghỉ sau mỗi 15 video
    if download_count % 15 == 0:
        rest = random.uniform(10, 25)
        log_box.insert("end", f"\n😴 Nghỉ {int(rest)}s...\n")
        log_box.see("end")
        time.sleep(rest)

# ===== THREAD =====
def worker(urls, folder, log_box):
    for url in urls:
        if not url.strip():
            continue
        try:
            download_video(url.strip(), folder, log_box)
        except:
            wait = random.uniform(3, 6)
            log_box.insert("end", f"Lỗi, thử lại sau {int(wait)}s...\n")
            log_box.see("end")
            time.sleep(wait)

def start_download(urls, folder, log_box):
    chunk_size = len(urls) // num_threads + 1
    for i in range(num_threads):
        chunk = urls[i*chunk_size:(i+1)*chunk_size]
        threading.Thread(target=worker, args=(chunk, folder, log_box)).start()

# ===== GUI =====
ctk.set_appearance_mode("dark")
app = ctk.CTk()
app.title("TikTok Downloader PRO MAX - SMART SAFE")
app.geometry("900x600")

frame = ctk.CTkFrame(app)
frame.pack(fill="both", expand=True, padx=10, pady=10)

entry = ctk.CTkTextbox(frame, height=120)
entry.pack(fill="x", pady=10)
entry.insert("0.0", "Dán link TikTok (mỗi dòng 1 link)")

folder_entry = ctk.CTkEntry(frame, placeholder_text="Thư mục lưu (bỏ trống = downloads)")
folder_entry.pack(fill="x", pady=5)

def choose_folder():
    folder = filedialog.askdirectory()
    folder_entry.delete(0, "end")
    folder_entry.insert(0, folder)

ctk.CTkButton(frame, text="📁 Chọn thư mục", command=choose_folder).pack(pady=5)

log_box = ctk.CTkTextbox(frame)
log_box.pack(fill="both", expand=True, pady=10)

def on_start():
    urls = entry.get("1.0", "end").strip().split("\n")
    folder = folder_entry.get().strip() or "downloads"

    if not os.path.exists(folder):
        os.makedirs(folder)

    start_download(urls, folder, log_box)

ctk.CTkButton(frame, text="🚀 Bắt đầu tải", command=on_start).pack(pady=10)

init_db()
app.mainloop()
