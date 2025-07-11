import os
import sys
import json
import requests
import base64
import time
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
import concurrent.futures
from pathlib import Path

# ====== 靜音 ======
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

# ====== 0. 配置路徑 ======
ROOT_DIR = Path(os.getenv("RSS_ROOT_DIR", "/data"))
OUTPUT_DIR = Path(os.getenv("SPOTIFY_OUTPUT_DIR", ROOT_DIR / "Spotify_Metadata"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ====== 1. Spotify Token ======
load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

client_credentials = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
b64_credentials = base64.b64encode(client_credentials.encode()).decode()

try:
    token_response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {b64_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={"grant_type": "client_credentials"},
        timeout=10
    )
    token_response.raise_for_status()
except Exception:
    exit(1)

access_token = token_response.json().get("access_token")
if not access_token:
    exit(1)
HEADERS = {"Authorization": f"Bearer {access_token}"}

# ====== 2. Spotify 搜尋函數 ======
def real_search(title):
    params = {"q": title, "type": "episode", "limit": 10}
    try:
        resp = requests.get(
            "https://api.spotify.com/v1/search",
            headers=HEADERS,
            params=params,
            timeout=10
        )
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", "5"))
            time.sleep(wait)
            return real_search(title)
        if resp.status_code == 200:
            return resp.json().get("episodes", {}).get("items", [])
        else:
            return []
    except requests.exceptions.RequestException:
        return []

def search_episode_by_title(title):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(real_search, title)
        try:
            return future.result(timeout=20)
        except concurrent.futures.TimeoutError:
            return []

# ====== 3. 遍歷所有 rss_ 開頭的資料夾 ======
rss_roots = [p for p in ROOT_DIR.iterdir() if p.is_dir() and p.name.lower().startswith('rss_')]

if not rss_roots:
    exit(1)

for rss_root in rss_roots:
    json_files = list(rss_root.rglob('RSS_*.json'))
    if not json_files:
        continue

    for filename in json_files:
        input_path = filename
        base_name  = filename.stem
        safe_name  = "".join(c if c.isalnum() else "_" for c in base_name)
        output_path = OUTPUT_DIR / f"Spotify_{safe_name}.json"

        if output_path.exists():
            continue

        try:
            with open(input_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    continue
                raw = json.loads(content)
        except Exception:
            continue

        if isinstance(raw, dict) and "items" in raw:
            episodes = raw["items"]
        elif isinstance(raw, list):
            episodes = raw
        else:
            continue

        show_titles = [ep.get("title", "").strip() for ep in episodes if "title" in ep]

        matched_eps = []
        seen_ids = set()

        for ap_title in show_titles:
            results = search_episode_by_title(ap_title)

            for item in results:
                spotify_title = item.get("name", "").strip()
                score = fuzz.token_set_ratio(ap_title, spotify_title)
                if score >= 99 and item["id"] not in seen_ids:
                    matched_eps.append(item)
                    seen_ids.add(item["id"])
                    break

        if matched_eps:
            with open(output_path, "w", encoding="utf-8") as out:
                json.dump(matched_eps, out, ensure_ascii=False, indent=2)
