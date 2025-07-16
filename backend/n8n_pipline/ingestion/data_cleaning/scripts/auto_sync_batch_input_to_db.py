#!/usr/bin/env python3
"""
自動比對與補齊 batch_input 資料到 PostgreSQL
- 以 (podcast_id, episode_title) 為主鍵
- 自動補上缺漏的 podcast/episode
- 產生詳細比對與修正報告
"""
import os
import sys
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Set, Tuple
from datetime import datetime
from pathlib import Path
import traceback

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BATCH_INPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'batch_input')

# 資料庫連線設定
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'postgres.podwise.svc.cluster.local'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'podcast'),
    'user': os.getenv('POSTGRES_USER', 'bdse37'),
    'password': os.getenv('POSTGRES_PASSWORD', '111111')
}

# 主要欄位對應
PODCAST_FIELDS = ['podcast_id', 'name', 'description', 'category', 'languages', 'created_at', 'updated_at']
EPISODE_FIELDS = ['podcast_id', 'episode_title', 'published_date', 'audio_url', 'duration', 'description', 'audio_preview_url', 'languages', 'explicit', 'created_at', 'updated_at', 'apple_episodes_ranking']


def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    return conn

def parse_podcast_json(filepath: str) -> Dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_rss_json(filepath: str) -> List[Dict]:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, dict) and 'episodes' in data:
            return data['episodes']
        elif isinstance(data, list):
            return data
        else:
            return []

def normalize_episode_data(episode: Dict) -> Dict:
    """標準化 episode 資料，處理不同格式的欄位名稱"""
    normalized = episode.copy()
    
    # 處理標題欄位
    if 'title' in episode and 'episode_title' not in episode:
        normalized['episode_title'] = episode['title']
    
    # 處理發布日期欄位
    if 'published' in episode and 'published_date' not in episode:
        normalized['published_date'] = episode['published']
    
    # 處理音訊URL欄位
    if 'audio_url' not in episode:
        if 'enclosure' in episode and isinstance(episode['enclosure'], dict):
            normalized['audio_url'] = episode['enclosure'].get('url')
        elif 'link' in episode:
            normalized['audio_url'] = episode['link']
    
    # 處理描述欄位
    if 'description' not in episode and 'summary' in episode:
        normalized['description'] = episode['summary']
    
    return normalized

def get_podcast_id_from_filename(filename: str) -> int:
    name = filename.replace('.json', '')
    if filename.startswith('podcast_'):
        return int(name.split('_')[1])
    elif filename.startswith('RSS_'):
        return int(name.split('_')[1])
    elif filename.startswith('Spotify_RSS_'):
        return int(name.split('_')[2])
    else:
        raise ValueError(f'無法解析 podcast_id: {filename}')

def get_all_batch_input_files() -> Tuple[List[str], List[str]]:
    files = os.listdir(BATCH_INPUT_DIR)
    podcast_files = [f for f in files if f.startswith('podcast_') and f.endswith('.json')]
    rss_files = [f for f in files if (f.startswith('RSS_') or f.startswith('Spotify_RSS_')) and f.endswith('.json')]
    return podcast_files, rss_files

def fetch_db_podcasts(conn) -> Set[int]:
    with conn.cursor() as cursor:
        cursor.execute('SELECT podcast_id FROM podcasts')
        return set(row[0] for row in cursor.fetchall())

def fetch_db_episodes_map(conn) -> Dict[int, Set[str]]:
    """回傳 {podcast_id: set(episode_title)}"""
    with conn.cursor() as cursor:
        cursor.execute('SELECT podcast_id, episode_title FROM episodes')
        result = {}
        for row in cursor.fetchall():
            pid, title = row
            result.setdefault(pid, set()).add(title)
        return result

def insert_podcast(conn, podcast: Dict):
    fields = [f for f in PODCAST_FIELDS if f in podcast]
    values = [podcast.get(f) for f in fields]
    placeholders = ','.join(['%s'] * len(fields))
    sql = f"INSERT INTO podcasts ({','.join(fields)}) VALUES ({placeholders}) ON CONFLICT (podcast_id) DO NOTHING"
    with conn.cursor() as cursor:
        cursor.execute(sql, values)

def insert_episode(conn, episode: Dict):
    fields = [f for f in EPISODE_FIELDS if f in episode]
    values = [episode.get(f) for f in fields]
    placeholders = ','.join(['%s'] * len(fields))
    sql = f"INSERT INTO episodes ({','.join(fields)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
    with conn.cursor() as cursor:
        cursor.execute(sql, values)

def main():
    logger.info('=== 自動比對與補齊 batch_input 資料 ===')
    report = []
    conn = None
    try:
        conn = get_db_connection()
        db_podcast_ids = fetch_db_podcasts(conn)
        db_episodes_map = fetch_db_episodes_map(conn)
        podcast_files, rss_files = get_all_batch_input_files()
        
        # 處理 podcast 主檔
        podcast_file_ids = set()
        for pf in podcast_files:
            podcast_id = get_podcast_id_from_filename(pf)
            podcast_file_ids.add(podcast_id)
            if podcast_id not in db_podcast_ids:
                podcast = parse_podcast_json(os.path.join(BATCH_INPUT_DIR, pf))
                insert_podcast(conn, podcast)
                report.append(f'✅ 新增 podcast: {podcast_id} ({pf})')
            else:
                report.append(f'✔️ 已存在 podcast: {podcast_id} ({pf})')
        
        # 處理 episodes
        for rf in rss_files:
            podcast_id = get_podcast_id_from_filename(rf)
            episodes = parse_rss_json(os.path.join(BATCH_INPUT_DIR, rf))
            
            # 標準化 episode 資料
            normalized_episodes = []
            for ep in episodes:
                normalized_ep = normalize_episode_data(ep)
                if 'episode_title' in normalized_ep:
                    normalized_episodes.append(normalized_ep)
            
            file_episode_titles = set(ep['episode_title'] for ep in normalized_episodes)
            db_episode_titles = db_episodes_map.get(podcast_id, set())
            missing_titles = file_episode_titles - db_episode_titles
            
            for ep in normalized_episodes:
                if ep.get('episode_title') in missing_titles:
                    ep['podcast_id'] = podcast_id
                    insert_episode(conn, ep)
            
            report.append(f'Podcast {podcast_id} ({rf}): 檔案內 {len(file_episode_titles)} 集, 資料庫 {len(db_episode_titles)} 集, 新增 {len(missing_titles)} 集')
        
        conn.commit()
        
        # 最終比對
        db_episodes_map = fetch_db_episodes_map(conn)
        for rf in rss_files:
            podcast_id = get_podcast_id_from_filename(rf)
            episodes = parse_rss_json(os.path.join(BATCH_INPUT_DIR, rf))
            
            # 標準化 episode 資料
            normalized_episodes = []
            for ep in episodes:
                normalized_ep = normalize_episode_data(ep)
                if 'episode_title' in normalized_ep:
                    normalized_episodes.append(normalized_ep)
            
            file_episode_titles = set(ep['episode_title'] for ep in normalized_episodes)
            db_episode_titles = db_episodes_map.get(podcast_id, set())
            report.append(f'【比對】Podcast {podcast_id} ({rf}): 檔案 {len(file_episode_titles)} 集, 資料庫 {len(db_episode_titles)} 集, 差異 {len(file_episode_titles-db_episode_titles)}')
        
        # 輸出報告
        report_file = os.path.join(os.path.dirname(BATCH_INPUT_DIR), 'auto_sync_report.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        logger.info(f'報告已儲存到: {report_file}')
        print('\n'.join(report))
        
    except Exception as e:
        logger.error(f'自動比對/補齊失敗: {e}')
        traceback.print_exc()
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            logger.info('資料庫連接已關閉')

if __name__ == '__main__':
    main() 