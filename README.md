# YouTube Bulk Transfer BY VIDU
![Header Image](header.png)

For the first time use this command

# sudo apt-get install -y ffmpeg

Press ↑ to enter the command to the terminal then press ↵ Enter to run the script (Do this everytime after launching codespace) 

Playlists 
1) SFT speed revision
# https://www.youtube.com/playlist?list=PL9zX0VbNmKiHKo-BtyV8BPWTSYna5uKac

2) ET paper
# https://www.youtube.com/playlist?list=PL9zX0VbNmKiFkshoAPMjeQfMS2FfzGmrK

3) SFT Paper Class
# https://www.youtube.com/playlist?list=PL9zX0VbNmKiGvjsOA_PkSwmDDk1rvfJba

4) ET Chinthaka balasuriya
# https://www.youtube.com/playlist?list=PL9zX0VbNmKiGYGvjdBVkcWhzDa_wdY-_f

5) ICT pubudu wijekoon
# https://www.youtube.com/playlist?list=PL9zX0VbNmKiHlw4n8kLRrD7TNfxnuCc0M
  
This repository provides a fully automated solution to **download YouTube videos** and **upload them** to multiple YouTube accounts inside GitHub Codespaces, including adding uploaded videos to specified playlists.

---

## Features

* **Bulk download & upload** (multi-threaded)
* **Playlist support**: add each uploaded video to a playlist (ID or URL)
* **Account rotation**: cycle through multiple OAuth tokens when quotas are exceeded
* **Best quality** video + audio downloads via `yt-dlp`
* **Persistent cookies** management for downloading age-restricted/private videos
* **Fully automated** in Codespaces (auto-starts on container boot)

---

## 1. Prepare OAuth Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a **Google Cloud project**.
3. Enable the **YouTube Data API v3**:

   * **APIs & Services** → **Library** → Search for **YouTube Data API v3** → **Enable**.
4. Create OAuth credentials:

   * **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth client ID**.
   * Select **Desktop app** and click **Create**.
   * Download the JSON file and rename it to `client_secret.json`.
   * Place `client_secret.json` in the **root** of this repository.

---

## 2. Generate `tokenX.pickle` Files Locally

You need one token file per YouTube account (e.g., `token1.pickle`, `token2.pickle`, etc.).

1. On **your local machine**, clone this repo (or create a new directory) and copy `client_secret.json` into it.

   ```bash
   git clone https://github.com/vidu2006/youtube-bulk-transfer
   cd your-repo
   ```

2. Install required Python packages:

   ```bash
   python3 -m venv venv
   source venv/bin/activate     # macOS/Linux
   .\venv\Scripts\activate    # Windows
   pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
   ```

3. Create a helper script `get_token.py`:

   ```python
   # get_token.py
   from google_auth_oauthlib.flow import InstalledAppFlow
   import pickle

   SCOPES = [
       "https://www.googleapis.com/auth/youtube.upload",
       "https://www.googleapis.com/auth/youtube"
   ]

   flow = InstalledAppFlow.from_client_secrets_file(
       'client_secret.json', SCOPES
   )
   creds = flow.run_local_server(port=0)

   with open('token1.pickle', 'wb') as f:
       pickle.dump(creds, f)
   print('✅ Created token1.pickle')
   ```

4. Run the helper to generate **one** token:

   ```bash
   python3 get_token.py
   ```

   * A browser window will open. Log in with your first YouTube account.
   * After consent, a `token1.pickle` file appears.

5. Repeat steps 3–4, renaming the output to `token2.pickle`, `token3.pickle`, etc., for each additional account.

6. Copy all `tokenX.pickle` files into the **root** of your GitHub repository. **Do not commit them publicly**.

---

## 3. Export YouTube Cookies 

For age-restricted downloads, export your YouTube cookies:

1. Install the **Get cookies.txt** extension in your browser.
2. Log in to YouTube and export cookies as `cookies.txt`.
3. Place `cookies.txt` in the repo root. It is auto-refreshed by Playwright in Codespaces.

---

## 4. Open in GitHub Codespaces

1. Fork this repository and click **Code → Codespaces → New codespace**.
2. Codespaces will build the container
3. Once started, Run the main script using this:

   ```bash
   python3 -u youtube_transfer.py
   ```

   * Then paste each **Video URL** and its **Playlist URL or ID** (press Enter to reuse last).
   * Type `done` to begin bulk download/upload.

---

## 5. Usage

* **Video URL**: e.g. `https://youtu.be/VIDEO_ID`
* **Playlist**: full URL (`https://www.youtube.com/playlist?list=PL...`) or just the ID (`PL...`).
* **Press Enter** for playlist reuse.

The script will:

1. Download best video + audio.
2. Upload to YouTube (unlisted).
3. Add the new video to the specified playlist.
4. Rotate accounts on quota limits.

---

## 6. Security & Cleanup

* Keep the repo **private**.

* Add sensitive files to `.gitignore`:

  ```gitignore
  client_secret.json
  token*.pickle
  cookies.txt
  ```

* To stop the Codespace, simply close it; your uploads run in the cloud.

---

Happy bulk transferring! 🎉
