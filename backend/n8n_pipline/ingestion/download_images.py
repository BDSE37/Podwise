import os
import glob
import json
import requests


def download_images_from_json(json_path: str, output_dir: str):
    """
    從 json_path 讀取，每個 item 的 images 陣列，
    依 height 命名並下載到 output_dir。
    """
    base_name = os.path.splitext(os.path.basename(json_path))[0]
    base_name = base_name.replace("Spotify_", "")

    os.makedirs(output_dir, exist_ok=True)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        for img in item.get("images", []):
            height = img.get("height")
            url = img.get("url")
            if not (height and url):
                continue

            fn = f"{base_name}_{height}.jpg"
            fp = os.path.join(output_dir, fn)

            if os.path.exists(fp):
                print(f"⚠️ 已存在，跳過：{fn}")
                continue

            try:
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                with open(fp, "wb") as out:
                    out.write(r.content)
                print(f"✅ 已下載：{fn}")
            except Exception as e:
                print(f"❌ 下載失敗 ({url})：{e}")


# ========= 主流程 =========
# 來源根目錄（假設 Notebook 就在這個資料夾底下）
root = os.getcwd()

# 要處理的子資料夾清單
folders = ["商業(json)_1321", "教育(json)_1304"]

for folder in folders:
    src_dir = os.path.join(root, folder)
    dst_dir = os.path.join(src_dir, "images")  # 每個資料夾底下建立 images/

    pattern = os.path.join(src_dir, "Spotify_*.json")
    json_files = glob.glob(pattern)

    if not json_files:
        print(f"❌ 在 {folder} 找不到任何 Spotify_*.json")
        continue

    print(f"\n🔎 處理資料夾：{folder}，共找到 {len(json_files)} 個 JSON：")
    for jf in json_files:
        print("  •", os.path.basename(jf))
        download_images_from_json(jf, dst_dir)