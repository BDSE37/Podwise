#!/usr/bin/env python3
"""
檢查 Spotify_RSS 檔案與 RSS 檔案的 mapping 關係
確認 Spotify_RSS 是否正確補充了 Apple Podcast 資料
"""

import os
import sys
import json
import logging
from typing import Dict, List, Set, Tuple
from datetime import datetime
import traceback

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BATCH_INPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'batch_input')

def get_podcast_id_from_filename(filename: str) -> int:
    """從檔案名稱提取 podcast_id"""
    name = filename.replace('.json', '')
    if filename.startswith('podcast_'):
        return int(name.split('_')[1])
    elif filename.startswith('RSS_'):
        return int(name.split('_')[1])
    elif filename.startswith('Spotify_RSS_'):
        return int(name.split('_')[2])
    else:
        raise ValueError(f'無法解析 podcast_id: {filename}')

def get_all_rss_files() -> Tuple[List[str], List[str]]:
    """獲取所有 RSS 和 Spotify_RSS 檔案"""
    files = os.listdir(BATCH_INPUT_DIR)
    rss_files = [f for f in files if f.startswith('RSS_') and f.endswith('.json') and not f.startswith('Spotify_RSS_')]
    spotify_rss_files = [f for f in files if f.startswith('Spotify_RSS_') and f.endswith('.json')]
    return rss_files, spotify_rss_files

def parse_json_file(filepath: str) -> List[Dict]:
    """解析 JSON 檔案"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'episodes' in data:
                return data['episodes']
            elif isinstance(data, list):
                return data
            else:
                return []
    except Exception as e:
        logger.error(f"解析檔案失敗 {filepath}: {e}")
        return []

def normalize_episode_data(episode: Dict) -> Dict:
    """標準化 episode 資料"""
    normalized = episode.copy()
    
    # 處理標題欄位
    if 'title' in episode and 'episode_title' not in episode:
        normalized['episode_title'] = episode['title']
    elif 'name' in episode and 'episode_title' not in episode:
        normalized['episode_title'] = episode['name']
    
    # 處理發布日期欄位
    if 'published' in episode and 'published_date' not in episode:
        normalized['published_date'] = episode['published']
    elif 'release_date' in episode and 'published_date' not in episode:
        normalized['published_date'] = episode['release_date']
    
    # 處理音訊URL欄位
    if 'audio_url' not in episode:
        if 'enclosure' in episode and isinstance(episode['enclosure'], dict):
            normalized['audio_url'] = episode['enclosure'].get('url')
        elif 'link' in episode:
            normalized['audio_url'] = episode['link']
        elif 'audio_preview_url' in episode:
            normalized['audio_url'] = episode['audio_preview_url']
    
    # 處理描述欄位
    if 'description' not in episode and 'summary' in episode:
        normalized['description'] = episode['summary']
    
    # 處理時長欄位
    if 'duration_ms' in episode and 'duration' not in episode:
        normalized['duration'] = episode['duration_ms'] // 1000  # 轉換為秒
    
    return normalized

def get_episode_titles_and_apple_data(filepath: str) -> Tuple[Set[str], List[Dict]]:
    """獲取檔案中的 episode titles 和 Apple Podcast 相關資料"""
    episodes = parse_json_file(filepath)
    titles = set()
    apple_data = []
    
    for ep in episodes:
        normalized_ep = normalize_episode_data(ep)
        if 'episode_title' in normalized_ep:
            titles.add(normalized_ep['episode_title'])
            
            # 檢查是否有 Apple Podcast 相關欄位
            apple_fields = ['apple_episodes_ranking', 'apple_podcast_id', 'apple_episode_id']
            has_apple_data = any(field in normalized_ep for field in apple_fields)
            if has_apple_data:
                apple_data.append({
                    'title': normalized_ep['episode_title'],
                    'apple_fields': {k: v for k, v in normalized_ep.items() if k in apple_fields}
                })
    
    return titles, apple_data

def analyze_mapping_relationship():
    """分析 mapping 關係"""
    logger.info("=== 分析 Spotify_RSS 與 RSS 檔案 mapping 關係 ===")
    
    rss_files, spotify_rss_files = get_all_rss_files()
    
    # 建立 podcast_id 到檔案的映射
    rss_mapping = {}
    spotify_mapping = {}
    
    for rf in rss_files:
        podcast_id = get_podcast_id_from_filename(rf)
        rss_mapping[podcast_id] = rf
    
    for srf in spotify_rss_files:
        podcast_id = get_podcast_id_from_filename(srf)
        spotify_mapping[podcast_id] = srf
    
    # 分析結果
    report = []
    report.append("=" * 80)
    report.append("Spotify_RSS 與 RSS 檔案 Mapping 分析報告")
    report.append("=" * 80)
    report.append(f"分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 統計摘要
    report.append(f"\n📊 檔案統計:")
    report.append(f"   - RSS 檔案總數: {len(rss_files)}")
    report.append(f"   - Spotify_RSS 檔案總數: {len(spotify_rss_files)}")
    report.append(f"   - 有對應 RSS 的 Spotify_RSS: {len(set(rss_mapping.keys()) & set(spotify_mapping.keys()))}")
    report.append(f"   - 只有 RSS 的 podcast: {len(set(rss_mapping.keys()) - set(spotify_mapping.keys()))}")
    report.append(f"   - 只有 Spotify_RSS 的 podcast: {len(set(spotify_mapping.keys()) - set(rss_mapping.keys()))}")
    
    # 詳細分析每個 podcast
    report.append(f"\n🔍 詳細 Mapping 分析:")
    
    all_podcast_ids = set(rss_mapping.keys()) | set(spotify_mapping.keys())
    
    for podcast_id in sorted(all_podcast_ids):
        report.append(f"\n📻 Podcast {podcast_id}:")
        
        has_rss = podcast_id in rss_mapping
        has_spotify = podcast_id in spotify_mapping
        
        if has_rss:
            rss_file = rss_mapping[podcast_id]
            rss_titles, rss_apple_data = get_episode_titles_and_apple_data(os.path.join(BATCH_INPUT_DIR, rss_file))
            report.append(f"   ✅ RSS: {rss_file} ({len(rss_titles)} episodes, {len(rss_apple_data)} Apple data)")
        
        if has_spotify:
            spotify_file = spotify_mapping[podcast_id]
            spotify_titles, spotify_apple_data = get_episode_titles_and_apple_data(os.path.join(BATCH_INPUT_DIR, spotify_file))
            report.append(f"   🎵 Spotify_RSS: {spotify_file} ({len(spotify_titles)} episodes, {len(spotify_apple_data)} Apple data)")
        
        # 分析重疊和差異
        if has_rss and has_spotify:
            rss_file = rss_mapping[podcast_id]
            spotify_file = spotify_mapping[podcast_id]
            
            rss_titles, rss_apple_data = get_episode_titles_and_apple_data(os.path.join(BATCH_INPUT_DIR, rss_file))
            spotify_titles, spotify_apple_data = get_episode_titles_and_apple_data(os.path.join(BATCH_INPUT_DIR, spotify_file))
            
            common_titles = rss_titles & spotify_titles
            rss_only = rss_titles - spotify_titles
            spotify_only = spotify_titles - rss_titles
            
            report.append(f"   📋 重疊 episodes: {len(common_titles)}")
            report.append(f"   📋 RSS 獨有: {len(rss_only)}")
            report.append(f"   📋 Spotify 獨有: {len(spotify_only)}")
            
            # Apple Podcast 資料分析
            if spotify_apple_data:
                report.append(f"   🍎 Spotify_RSS 包含 Apple Podcast 資料: {len(spotify_apple_data)} episodes")
                for apple_ep in spotify_apple_data[:3]:  # 只顯示前3個
                    report.append(f"     - {apple_ep['title'][:50]}...")
                    report.append(f"       Apple fields: {apple_ep['apple_fields']}")
            else:
                report.append(f"   ⚠️ Spotify_RSS 無 Apple Podcast 資料")
            
            if rss_apple_data:
                report.append(f"   🍎 RSS 包含 Apple Podcast 資料: {len(rss_apple_data)} episodes")
            else:
                report.append(f"   ℹ️ RSS 無 Apple Podcast 資料")
        
        elif has_rss:
            report.append(f"   ⚠️ 只有 RSS 檔案，無 Spotify_RSS 補充")
        
        elif has_spotify:
            report.append(f"   ⚠️ 只有 Spotify_RSS 檔案，無對應 RSS")
    
    # 總結
    report.append(f"\n{'='*80}")
    report.append("總結")
    report.append(f"{'='*80}")
    
    total_with_mapping = len(set(rss_mapping.keys()) & set(spotify_mapping.keys()))
    total_spotify_with_apple = 0
    
    for podcast_id in spotify_mapping:
        spotify_file = spotify_mapping[podcast_id]
        _, spotify_apple_data = get_episode_titles_and_apple_data(os.path.join(BATCH_INPUT_DIR, spotify_file))
        if spotify_apple_data:
            total_spotify_with_apple += 1
    
    report.append(f"✅ 成功 mapping 的 podcast: {total_with_mapping}")
    report.append(f"🍎 包含 Apple Podcast 資料的 Spotify_RSS: {total_spotify_with_apple}")
    
    if total_with_mapping > 0:
        report.append(f"📈 Mapping 成功率: {total_with_mapping/len(spotify_mapping)*100:.1f}%")
    
    report.append(f"\n{'='*80}")
    
    return "\n".join(report)

def main():
    """主程式"""
    try:
        report = analyze_mapping_relationship()
        print(report)
        
        # 儲存報告
        report_file = os.path.join(os.path.dirname(BATCH_INPUT_DIR), 'spotify_rss_mapping_report.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Spotify_RSS mapping 分析報告已儲存到: {report_file}")
        
    except Exception as e:
        logger.error(f"分析失敗: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 