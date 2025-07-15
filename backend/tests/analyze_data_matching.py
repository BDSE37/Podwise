#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析 CSV 資料與資料庫的匹配情況
"""

import os
import re
import psycopg2
from minio import Minio
from minio.error import S3Error
import csv
import difflib

# ---------- 設定區 ----------
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_BUCKETS = ["business-one-min-audio", "education-one-min-audio"]

PG_HOST = "localhost"
PG_PORT = 5432
PG_USER = "bdse37"
PG_PASSWORD = "111111"
PG_DB = "podcast"

REPORT_PATH = "minio_postgres_mapping_report.txt"

# ---------- 標準化函數 ----------
def normalize_title(title: str) -> str:
    """
    標準化標題：移除標點、空格、特殊符號、全形轉半形、底線分隔
    """
    # 全形轉半形
    full_to_half = {
        '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
        '５': '5', '６': '6', '７': '7', '８': '8', '９': '9',
        'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E',
        'Ｆ': 'F', 'Ｇ': 'G', 'Ｈ': 'H', 'Ｉ': 'I', 'Ｊ': 'J',
        'Ｋ': 'K', 'Ｌ': 'L', 'Ｍ': 'M', 'Ｎ': 'N', 'Ｏ': 'O',
        'Ｐ': 'P', 'Ｑ': 'Q', 'Ｒ': 'R', 'Ｓ': 'S', 'Ｔ': 'T',
        'Ｕ': 'U', 'Ｖ': 'V', 'Ｗ': 'W', 'Ｘ': 'X', 'Ｙ': 'Y',
        'Ｚ': 'Z', 'ａ': 'a', 'ｂ': 'b', 'ｃ': 'c', 'ｄ': 'd',
        'ｅ': 'e', 'ｆ': 'f', 'ｇ': 'g', 'ｈ': 'h', 'ｉ': 'i',
        'ｊ': 'j', 'ｋ': 'k', 'ｌ': 'l', 'ｍ': 'm', 'ｎ': 'n',
        'ｏ': 'o', 'ｐ': 'p', 'ｑ': 'q', 'ｒ': 'r', 'ｓ': 's',
        'ｔ': 't', 'ｕ': 'u', 'ｖ': 'v', 'ｗ': 'w', 'ｘ': 'x',
        'ｙ': 'y', 'ｚ': 'z', '（': '(', '）': ')', '【': '[',
        '】': ']', '「': '"', '」': '"', '『': '"', '』': '"',
        '，': ',', '。': '.', '：': ':', '；': ';', '！': '!',
        '？': '?', '～': '~', '＠': '@', '＃': '#', '＄': '$',
        '％': '%', '＾': '^', '＆': '&', '＊': '*', '（': '(',
        '）': ')', '＿': '_', '＋': '+', '－': '-', '＝': '=',
        '｛': '{', '｝': '}', '｜': '|', '＼': '\\', '／': '/',
        '＜': '<', '＞': '>', '　': ' '  # 全形空格轉半形空格
    }
    for full, half in full_to_half.items():
        title = title.replace(full, half)
    # 移除所有標點符號、空格、特殊字符，只保留字母、數字、底線
    title = re.sub(r'[^\w\s]', '', title)
    # 將多個空格或底線替換為單個底線
    title = re.sub(r'[\s_]+', '_', title)
    # 移除開頭和結尾的底線
    title = title.strip('_')
    if not title:
        title = "unnamed"
    return title

# ---------- 取得 MinIO 檔案 ----------
def get_minio_files():
    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )
    files = []
    for bucket in MINIO_BUCKETS:
        try:
            objects = minio_client.list_objects(bucket, recursive=True)
            for obj in objects:
                if obj.object_name.endswith('.mp3'):
                    # 解析 podcast_id
                    m = re.match(r"Spotify_RSS_(\d+)_", obj.object_name)
                    podcast_id = m.group(1) if m else None
                    files.append({
                        'bucket': bucket,
                        'object_name': obj.object_name,
                        'podcast_id': podcast_id,
                        'normalized': normalize_title(os.path.splitext(obj.object_name)[0])
                    })
        except S3Error as e:
            print(f"[MinIO] Bucket {bucket} error: {e}")
    return files

# ---------- 取得 PostgreSQL 資料 ----------
def get_pg_episodes():
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASSWORD,
        dbname=PG_DB
    )
    cur = conn.cursor()
    cur.execute("SELECT podcast_id, episode_title FROM episodes;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            'podcast_id': str(row[0]),
            'episode_title': row[1],
            'normalized': normalize_title(row[1])
        } for row in rows
    ]

# ---------- 比對 ----------
def match_files_to_episodes(minio_files, pg_episodes):
    # 建立資料庫標準化 lookup
    db_lookup = {}
    for ep in pg_episodes:
        key = (ep['podcast_id'], ep['normalized'])
        db_lookup[key] = ep
    results = []
    for f in minio_files:
        # 解析 podcast_id
        # 假設檔名格式: Spotify_RSS_{podcast_id}_...，取出 podcast_id
        m = re.match(r"Spotify_RSS_(\d+)_", f['object_name'])
        podcast_id = m.group(1) if m else None
        key = (podcast_id, f['normalized'])
        if podcast_id and key in db_lookup:
            match_status = '完全匹配'
            db_ep = db_lookup[key]
        else:
            match_status = '未匹配'
            db_ep = None
        results.append({
            'bucket': f['bucket'],
            'object_name': f['object_name'],
            'podcast_id': podcast_id,
            'normalized': f['normalized'],
            'db_episode_title': db_ep['episode_title'] if db_ep else '',
            'match_status': match_status
        })
    return results

# ---------- 輸出報告 ----------
def write_report(results):
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['bucket', 'object_name', 'podcast_id', 'normalized', 'db_episode_title', 'match_status'])
        for r in results:
            writer.writerow([
                r['bucket'], r['object_name'], r['podcast_id'], r['normalized'], r['db_episode_title'], r['match_status']
            ])
    print(f"報告已輸出至 {REPORT_PATH}")

def fuzzy_match_files_to_episodes(minio_files, pg_episodes, threshold=0.8):
    results = []
    for f in minio_files:
        best_score = 0
        best_ep = None
        for ep in pg_episodes:
            if f['podcast_id'] == ep['podcast_id']:
                score = difflib.SequenceMatcher(None, f['normalized'], ep['normalized']).ratio()
                if score > best_score:
                    best_score = score
                    best_ep = ep
        match_status = '高相似' if best_score >= threshold else '低相似'
        results.append({
            'bucket': f['bucket'],
            'object_name': f['object_name'],
            'podcast_id': f['podcast_id'],
            'normalized': f['normalized'],
            'best_db_podcast_id': best_ep['podcast_id'] if best_ep else '',
            'best_db_episode_title': best_ep['episode_title'] if best_ep else '',
            'best_db_normalized': best_ep['normalized'] if best_ep else '',
            'similarity_score': best_score,
            'match_status': match_status
        })
    return results

def write_fuzzy_report(results, path):
    with open(path, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['bucket', 'object_name', 'podcast_id', 'normalized', 'best_db_podcast_id', 'best_db_episode_title', 'best_db_normalized', 'similarity_score', 'match_status'])
        for r in results:
            writer.writerow([
                r['bucket'], r['object_name'], r['podcast_id'], r['normalized'],
                r['best_db_podcast_id'], r['best_db_episode_title'], r['best_db_normalized'],
                f"{r['similarity_score']:.3f}", r['match_status']
            ])
    print(f"模糊比對報告已輸出至 {path}")

if __name__ == "__main__":
    minio_files = get_minio_files()
    pg_episodes = get_pg_episodes()
    results = match_files_to_episodes(minio_files, pg_episodes)
    write_report(results)
    # 新增模糊比對
    fuzzy_results = fuzzy_match_files_to_episodes(minio_files, pg_episodes, threshold=0.8)
    write_fuzzy_report(fuzzy_results, "minio_postgres_fuzzy_mapping_report.txt") 