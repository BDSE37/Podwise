import json
import os
import random
import re
import signal
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import yt_dlp

# === 配置區 ===
ROOT_DIR = "/data"  # 容器內掛載的資料夾
FFMPEG_LOCATION = None  # 容器已安裝 ffmpeg, 讓 yt-dlp 自動找
DOWNLOAD_ARCHIVE = os.path.join(ROOT_DIR, "downloaded_test.txt")
NUM_THREADS = 4
MIN_DELAY = 0.5
MAX_DELAY = 2.0
STOP_FILE = "STOP"
DOWNLOAD_COUNT = 10  # ✅ 可改為 "ALL" 或整數
EPISODES_COUNT = 10 # ✅ 可改為 "ALL" 或整數
# ===================


def _handle_abort(sig, frame):
    raise KeyboardInterrupt


signal.signal(signal.SIGINT, _handle_abort)
if hasattr(signal, "SIGBREAK"):
    signal.signal(signal.SIGBREAK, _handle_abort)



def safe_filename(title: str) -> str:
    name = re.sub(r'[\\/:*?"<>|\r\n]+', "_", title)
    return name[:80].strip() or "untitled"


def gather_download_tasks():
    tasks = []
    for folder in os.listdir(ROOT_DIR):
        if not folder.startswith("rss_outputs_"):
            continue
        rss_dir = os.path.join(ROOT_DIR, folder)
        if not os.path.isdir(rss_dir):
            continue
        gid = folder.split("_")[-1]

        mp3_dir = os.path.join(ROOT_DIR, f"mp3_test_{gid}")
        os.makedirs(mp3_dir, exist_ok=True)
        for fn in os.listdir(rss_dir):
            if fn.startswith("RSS_") and fn.lower().endswith(".json"):
                path = os.path.join(rss_dir, fn)
                RSSID = os.path.splitext(fn)[0].split("_")[1]
                try:
                    episodes = json.load(open(path, "r", encoding="utf-8"))
                except Exception:
                    continue

                if isinstance(EPISODES_COUNT, int):
                    selected_eps = episodes[:EPISODES_COUNT]
                else:
                    selected_eps = episodes  # 抓全部集數

                for ep in selected_eps:
                    url = ep.get("audio_url")
                    title = ep.get("title", "")
                    if url:
                        base = safe_filename(title)
                        filename = f"RSS_{RSSID}_podcast_{gid}_{base}"
                        tasks.append((url, mp3_dir, filename))
    if isinstance(DOWNLOAD_COUNT, int):
        tasks = tasks[:DOWNLOAD_COUNT]
    return tasks



def download_audio(task):
    url, mp3_dir, filename = task
    if os.path.exists(STOP_FILE):
        raise KeyboardInterrupt
    outtmpl = os.path.join(mp3_dir, f"{filename}.%(ext)s")
    opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "socket_timeout": 60,
        "continuedl": True,
        "retries": 10,
        "fragment_retries": 5,
        "sleep_interval": MIN_DELAY,
        "max_sleep_interval": MAX_DELAY,
        "download_archive": DOWNLOAD_ARCHIVE,
        "quiet": True,
        "ffmpeg_location": FFMPEG_LOCATION,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "96",
            }
        ],
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        # print(f"✅ 完成: {filename}")
    except KeyboardInterrupt:
        raise
    except Exception as e:
        # print(f"❌ 失敗: {filename}，{e}")
        pass



def main():
    tasks = gather_download_tasks()
    # print(f"🔹 預計下載 {len(tasks)} 檔案，使用 {NUM_THREADS} 執行緒...")
    try:
        with ThreadPoolExecutor(max_workers=NUM_THREADS) as exe:
            futures = []
            for t in tasks:
                if os.path.exists(STOP_FILE):
                    raise KeyboardInterrupt
                time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                futures.append(exe.submit(download_audio, t))
            for f in as_completed(futures):
                try:
                    f.result()
                except KeyboardInterrupt:
                    # print("🔴 下載中斷")
                    break
    except KeyboardInterrupt:
        # print("🔴 已停止所有任務，程式退出。")
        sys.exit(1)
    # print("✅ 全部下載完成。")


if __name__ == "__main__":
    main()
