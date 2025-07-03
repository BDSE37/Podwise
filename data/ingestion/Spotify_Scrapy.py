import os
import json
import requests
import base64
import time
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
from tqdm import tqdm
import concurrent.futures
from pathlib import Path

# ====== 1. Spotify Token ======
load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

print("📡 正在取得 Spotify Token...")
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
except Exception as e:
    print(f"❌ 無法取得 Spotify Token：{e}")
    exit(1)

access_token = token_response.json()["access_token"]
HEADERS = {"Authorization": f"Bearer {access_token}"}
print("✅ Token 成功取得")

# ====== 2. Spotify 搜尋函數（包裝搜尋 + 防限速 + 超時） ======
def real_search(title):
    params = {"q": title, "type": "episode", "limit": 10}
    try:
        resp = requests.get("https://api.spotify.com/v1/search", headers=HEADERS, params=params, timeout=10)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", "5"))
            tqdm.write(f"⚠️ Spotify 限速中，等待 {wait} 秒...")
            time.sleep(wait)
            return real_search(title)
        if resp.status_code == 200:
            return resp.json().get("episodes", {}).get("items", [])
        else:
            tqdm.write(f"⚠️ 搜尋失敗（{resp.status_code}）：{title}")
            return []
    except requests.exceptions.RequestException as e:
        tqdm.write(f"❌ 搜尋錯誤：{e}")
        return []

def search_episode_by_title(title):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(real_search, title)
        try:
            return future.result(timeout=20)
        except concurrent.futures.TimeoutError:
            tqdm.write(f"❌ 搜尋超時（超過 20 秒）：{title}")
            return []

# ====== 3. 遍歷 metadata 中所有資料夾 ======
root_metadata = Path("metadata")
if not root_metadata.exists():
    print("❌ 找不到 metadata 目錄，請確認路徑正確")
    exit(1)

subdirs = [p for p in root_metadata.iterdir() if p.is_dir()]

for subdir in subdirs:
    input_dir = subdir / "Episodes(集數列表)"
    output_dir = subdir / "Spotify_Metadata"
    os.makedirs(output_dir, exist_ok=True)

    if not input_dir.exists():
        tqdm.write(f"⚠️ 找不到 Episodes(集數列表)：{input_dir}")
        continue

    json_files = [f for f in input_dir.glob("RSS*.json") if f.is_file()]
    print(f"\n📂 處理資料夾：{subdir.name}，共偵測到 {len(json_files)} 個 JSON 檔案...\n")

    for filename in tqdm(json_files, desc=f"{subdir.name} 處理進度"):
        input_path = filename
        base_name = filename.stem
        safe_name = "".join(c if c.isalnum() else "_" for c in base_name)
        output_path = output_dir / f"Spotify_{safe_name}.json"

        tqdm.write(f"\n📁 正在處理：{filename.name}")

        if output_path.exists():
            tqdm.write(f"⚠️ 已存在：{output_path}，跳過此檔")
            continue

        try:
            with open(input_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    tqdm.write(f"⚠️ 空檔案，跳過：{filename.name}")
                    continue
                raw = json.loads(content)
            tqdm.write("📄 JSON 載入成功")
        except Exception as e:
            tqdm.write(f"❌ JSON 載入失敗：{e}")
            continue

        if isinstance(raw, dict) and "items" in raw:
            episodes = raw["items"]
        elif isinstance(raw, list):
            episodes = raw
        else:
            tqdm.write("⚠️ 格式錯誤（非 dict 或 list），跳過")
            continue

        show_titles = [ep.get("title", "").strip() for ep in episodes if "title" in ep]
        tqdm.write(f"🔎 共發現 {len(show_titles)} 個標題")

        matched_eps = []
        seen_ids = set()

        for idx, ap_title in enumerate(show_titles, 1):
            tqdm.write(f"    [{idx}/{len(show_titles)}] 🔍 搜尋標題：{ap_title[:50]}...")
            results = search_episode_by_title(ap_title)

            for item in results:
                spotify_title = item["name"].strip()
                score = fuzz.token_set_ratio(ap_title, spotify_title)
                tqdm.write(f"        🎯 相似度：{score} - {spotify_title[:50]}")
                if score >= 99 and item["id"] not in seen_ids:
                    matched_eps.append(item)
                    seen_ids.add(item["id"])
                    tqdm.write(f"        ✅ 收錄：{spotify_title[:50]}")
                    break

        if matched_eps:
            with open(output_path, "w", encoding="utf-8") as out:
                json.dump(matched_eps, out, ensure_ascii=False, indent=2)
            tqdm.write(f"📥 儲存成功：{output_path}（共 {len(matched_eps)} 筆）")
        else:
            tqdm.write(f"⚠️ 無符合項目，未產生檔案")

print("\n✅ 全部處理完成！")
