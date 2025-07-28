#!/usr/bin/env python3
import os, re, time, pickle, sys, select
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import yt_dlp
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# ---- Configuration ----
SCOPES             = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]
TOKEN_FILES        = [f"token{i}.pickle" for i in range(1,5)]
COOKIES_TXT        = Path("cookies.txt")
MAX_WORKERS        = 35
COOKIE_MAX_AGE     = 7 * 24 * 3600   # 7 days
IDLE_TIMEOUT       = 120             # seconds to wait for input
SHUTDOWN_DELAY     = 120             # seconds after tasks finish
# ------------------------

def input_with_timeout(prompt, timeout):
    """Prompt the user, wait up to timeout secs for input, else return None."""
    sys.stdout.write(prompt)
    sys.stdout.flush()
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if ready:
        return sys.stdin.readline().strip()
    return None

def warn_refresh_cookies():
    if COOKIES_TXT.exists():
        age = time.time() - COOKIES_TXT.stat().st_mtime
        if age > COOKIE_MAX_AGE:
            print("⚠️ cookies.txt older than 7 days—export a fresh one.")
    else:
        print("⚠️ cookies.txt not found—downloads may fail.")

def extract_playlist_id(s: str) -> str:
    m = re.search(r"[?&]list=([A-Za-z0-9_-]+)", s)
    return m.group(1) if m else s

class AccountRotator:
    def __init__(self, token_files):
        self.files = token_files
        self.idx = 0
        self.creds = None
        self._load()

    def _load(self):
        tf = self.files[self.idx]
        if not os.path.exists(tf):
            raise FileNotFoundError(f"{tf} missing")
        with open(tf, "rb") as f:
            self.creds = pickle.load(f)
        if self.creds.expired and self.creds.refresh_token:
            self.creds.refresh(Request())
            with open(tf, "wb") as fw:
                pickle.dump(self.creds, fw)

    def rotate(self):
        self.idx = (self.idx + 1) % len(self.files)
        print(f"🔄 Switching to account #{self.idx+1}")
        self._load()

rotator = AccountRotator(TOKEN_FILES)

def download_video(url):
    opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": "%(title)s.%(ext)s",
        "cookiefile": str(COOKIES_TXT) if COOKIES_TXT.exists() else None
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info), info.get("title","Untitled"), info.get("description","")

def upload_video(path, title, description):
    youtube = build("youtube", "v3", credentials=rotator.creds)
    body = {
        "snippet": {"title": title, "description": description, "categoryId": "22", "tags": []},
        "status": {"privacyStatus": "unlisted"}
    }
    media = MediaFileUpload(path, chunksize=1024*1024, resumable=True)
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    resp = None
    while resp is None:
        try:
            status, resp = req.next_chunk()
            if status:
                print(f"    ↑ {int(status.progress()*100)}% {title}")
        except HttpError as e:
            err = str(e)
            if (e.resp.status == 403 and "quotaExceeded" in err) or \
               (e.resp.status == 400 and "uploadLimitExceeded" in err):
                print("⚠️ Upload limit reached—rotating account and retrying...")
                rotator.rotate()
                youtube = build("youtube", "v3", credentials=rotator.creds)
                req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
                continue
            else:
                raise
    vid = resp["id"]
    print(f"✔ Uploaded: https://youtu.be/{vid}")
    return vid

def add_to_playlist(video_id, playlist_id):
    youtube = build("youtube","v3", credentials=rotator.creds)
    youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {"kind":"youtube#video","videoId":video_id}
            }
        }
    ).execute()
    print(f"➕ Added to playlist: {playlist_id}")

def worker(task):
    url, playlist_input = task
    pid = extract_playlist_id(playlist_input) if playlist_input else ""
    try:
        print(f"⏬ Downloading: {url}")
        path, title, desc = download_video(url)
        print(f"✔ Downloaded: {path}")
        print(f"⏫ Uploading: {title}")
        vid = upload_video(path, title, desc)
        if pid:
            add_to_playlist(vid, pid)
    except Exception as e:
        print(f"❌ Error {url}: {e}")

def main():
    warn_refresh_cookies()

    # 1) Collect tasks with timeout
    tasks = []
    last_pl = ""
    print("📥 Enter video URLs and playlist (URL or ID). Type 'done' to start.")
    while True:
        url = input_with_timeout("Video URL: ", IDLE_TIMEOUT)
        if url is None:
            print("\n⚠️ No input for 2 minutes—shutting down.")
            os._exit(0)
        url = url.strip()
        if url.lower() == "done":
            break
        if not url:
            continue

        raw_pl = input_with_timeout(f"Playlist (enter URL/ID) [Enter to reuse '{last_pl}']: ", IDLE_TIMEOUT)
        if raw_pl is None:
            print("\n⚠️ No input for 2 minutes—shutting down.")
            os._exit(0)
        raw_pl = raw_pl.strip()
        if raw_pl:
            last_pl = extract_playlist_id(raw_pl)
        tasks.append((url, last_pl))

    if not tasks:
        print("No tasks—exiting.")
        return

    # 2) Run tasks
    print(f"\n🚀 Processing {len(tasks)} videos with {MAX_WORKERS} workers...\n")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(worker, t) for t in tasks]
        for _ in as_completed(futures):
            pass

    # 3) Auto‑shutdown after all tasks finish
    print(f"\n🎉 All tasks completed. Shutting down in {SHUTDOWN_DELAY//60} minutes...")
    time.sleep(SHUTDOWN_DELAY)
    print("⏹ Shutting down now.")
    os._exit(0)

if __name__ == "__main__":
    main()
