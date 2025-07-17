#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MinIO 都沒問題，剩下就是前端 JS 綁定或 nginx 代理設定問題。
請提供前端圖片 Request URL 或 nginx 配置，我能幫你最後定位！
"""

import os
import re
import json
import psycopg2
from typing import List, Dict, Optional
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MinioEpisodeService:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'postgres.podwise.svc.cluster.local'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'user': os.getenv('POSTGRES_USER', 'bdse37'),
            'password': os.getenv('POSTGRES_PASSWORD', '111111'),
            'database': os.getenv('POSTGRES_DB', 'podcast')
        }
        
        # MinIO 配置
        self.minio_config = {
            'endpoint': '192.168.32.66:30090',
            'access_key': 'bdse37',
            'secret_key': '11111111'
        }
    
    def get_db_connection(self):
        """獲取資料庫連接"""
        return psycopg2.connect(**self.db_config)
    
    def parse_minio_filename(self, filename: str) -> Optional[Dict]:
        """
        解析 MinIO 檔案名稱
        支援多種格式:
        1. Spotify_RSS_{rss_id}_{episode_title}.mp3
        2. RSS_{rss_id}_{episode_title}.mp3
        3. RSS_{rss_id}_EP{episode_number}_{podcast_name}.mp3
        """
        try:
            # 移除 .mp3 副檔名
            name_without_ext = filename.replace('.mp3', '')
            
            # 更寬鬆的解析方式：只要以 RSS_ 開頭，後面跟數字，然後是下劃線
            if name_without_ext.startswith('RSS_'):
                # 找到第一個下劃線後的位置
                first_underscore = name_without_ext.find('_', 4)  # 跳過 "RSS_"
                if first_underscore != -1:
                    try:
                        rss_id = int(name_without_ext[4:first_underscore])
                        episode_title = name_without_ext[first_underscore + 1:]
                        
                        if rss_id and episode_title:
                            return {
                                'rss_id': rss_id,
                                'episode_title': episode_title,
                                'filename': filename
                            }
                    except ValueError:
                        # 如果 rss_id 不是數字，跳過
                        pass
            
            # 如果都不匹配，記錄警告但返回基本資訊
            logger.warning(f"無法解析檔案名稱: {filename}")
            return None
                
        except Exception as e:
            logger.error(f"解析檔案名稱失敗 {filename}: {e}")
            return None
    
    def get_minio_episodes(self, category: str = "business") -> List[Dict]:
        """
        獲取 MinIO 指定類別資料夾中的所有節目
        使用 mc ls 命令列出檔案
        """
        try:
            # 根據類別選擇資料夾
            folder_map = {
                "business": "business-one-min-audio",
                "education": "education-one-min-audio"
            }
            
            folder = folder_map.get(category, "business-one-min-audio")
            
            # 使用 mc ls 命令獲取檔案列表，並使用 --json 格式
            import subprocess
            result = subprocess.run(
                ['mc', 'ls', '--json', f'minio/{folder}/'],
                capture_output=True,
                text=True,
                check=True
            )
            
            episodes = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        import json
                        file_info = json.loads(line)
                        filename = file_info.get('key', '')  # 使用 'key' 而不是 'name'
                        
                        if filename.endswith('.mp3'):
                            parsed = self.parse_minio_filename(filename)
                            if parsed:
                                parsed['category'] = category
                                episodes.append(parsed)
                            else:
                                # 無法解析的檔案記錄警告
                                logger.warning(f"無法解析檔案名稱: {filename}")
                    except json.JSONDecodeError:
                        # 如果不是 JSON 格式，嘗試舊的解析方式
                        parts = line.split()
                        if len(parts) >= 4:
                            filename = parts[-1]
                            if filename.endswith('.mp3'):
                                parsed = self.parse_minio_filename(filename)
                                if parsed:
                                    parsed['category'] = category
                                    episodes.append(parsed)
                                else:
                                    logger.warning(f"無法解析檔案名稱: {filename}")
            
            logger.info(f"從 MinIO {folder} 獲取到 {len(episodes)} 個節目")
            return episodes
            
        except subprocess.CalledProcessError as e:
            logger.error(f"mc ls 命令執行失敗: {e}")
            return []
        except Exception as e:
            logger.error(f"獲取 MinIO 節目失敗: {e}")
            return []
    
    def match_episodes_with_database(self, minio_episodes: List[Dict]) -> List[Dict]:
        """
        將 MinIO 節目與資料庫中的節目進行匹配，並獲取相關標籤
        """
        try:
            conn = self.get_db_connection()
            matched_episodes = []
            used_episode_ids = set()  # 用於追蹤已使用的 episode_id
            used_podcast_ids = set()  # 用於追蹤已使用的 podcast_id
            
            with conn.cursor() as cursor:
                for minio_ep in minio_episodes:
                    rss_id = minio_ep['rss_id']
                    episode_title = minio_ep['episode_title']
                    category = minio_ep.get('category', 'business')
                    
                    # 在資料庫中查找對應的節目
                    cursor.execute("""
                        SELECT e.episode_id, e.episode_title, p.podcast_name, p.podcast_id, p.category
                        FROM episodes e 
                        JOIN podcasts p ON e.podcast_id = p.podcast_id 
                        WHERE p.podcast_id = %s AND e.episode_title LIKE %s
                    """, (rss_id, f"%{episode_title}%"))
                    
                    db_episode = cursor.fetchone()
                    if db_episode:
                        episode_id, db_title, podcast_name, podcast_id, podcast_category = db_episode
                        
                        # 檢查是否已經使用過這個 episode_id 或 podcast_id
                        if episode_id in used_episode_ids:
                            logger.info(f"跳過重複的節目: Episode ID {episode_id}, Title: {db_title}")
                            continue
                        
                        if podcast_id in used_podcast_ids:
                            logger.info(f"跳過重複的頻道: Podcast ID {podcast_id}, Name: {podcast_name}")
                            continue
                        
                        used_episode_ids.add(episode_id)
                        used_podcast_ids.add(podcast_id)
                        
                        # 獲取節目的標籤
                        cursor.execute("""
                            SELECT DISTINCT topic_tag 
                            FROM episode_topics 
                            WHERE episode_id = %s
                        """, (episode_id,))
                        
                        tags = [row[0] for row in cursor.fetchall()]
                        
                        # 如果沒有標籤，根據 podcast category 生成預設標籤
                        if not tags:
                            tags = self.get_default_tags_by_category(podcast_category or category)
                        
                        # 根據類別選擇正確的資料夾
                        folder_map = {
                            "business": "business-one-min-audio",
                            "education": "education-one-min-audio"
                        }
                        folder = folder_map.get(category, "business-one-min-audio")
                        
                        matched_episodes.append({
                            'episode_id': episode_id,
                            'episode_title': db_title,
                            'podcast_name': podcast_name,
                            'podcast_id': podcast_id,
                            'podcast_category': podcast_category,
                            'rss_id': rss_id,
                            'category': category,
                            'tags': tags,
                            'minio_filename': minio_ep['filename'],
                            'audio_url': f"http://{self.minio_config['endpoint']}/{folder}/{minio_ep['filename']}",
                            'image_url': f"http://{self.minio_config['endpoint']}/podcast-images/RSS_{rss_id}_300.jpg"
                        })
                    else:
                        logger.warning(f"未找到對應的資料庫記錄: RSS_ID={rss_id}, Title={episode_title}")
            
            conn.close()
            logger.info(f"成功匹配 {len(matched_episodes)} 個節目")
            return matched_episodes
            
        except Exception as e:
            logger.error(f"匹配節目失敗: {e}")
            return []
    
    def get_default_tags_by_category(self, category: str) -> List[str]:
        """
        根據類別獲取預設標籤
        """
        tag_mapping = {
            "商業": ["投資理財", "股票分析", "經濟分析", "財務規劃"],
            "投資": ["投資理財", "股票分析", "經濟分析", "財務規劃"],
            "創業": ["創業管理", "商業策略", "市場分析", "領導力"],
            "職業": ["職涯發展", "工作技能", "領導力", "溝通技巧"],
            "教育": ["學習方法", "教育理念", "知識分享", "個人成長"],
            "自我成長": ["個人成長", "心理學", "生活哲學", "目標設定"],
            "語言學習": ["語言學習", "外語技巧", "文化交流", "學習方法"]
        }
        
        return tag_mapping.get(category, ["一般", "知識分享", "學習", "成長"])
    
    def get_available_episodes(self) -> List[Dict]:
        """
        獲取所有可用的節目（MinIO + 資料庫匹配）
        """
        # 獲取所有支援類別的節目
        all_episodes = []
        for category in ["business", "education"]:
            minio_episodes = self.get_minio_episodes(category)
            matched_episodes = self.match_episodes_with_database(minio_episodes)
            all_episodes.extend(matched_episodes)
        return all_episodes
    
    def get_episodes_by_category(self, category: str = "business") -> List[Dict]:
        """
        根據類別獲取節目
        支援 business 和 education 類別
        """
        minio_episodes = self.get_minio_episodes(category)
        matched_episodes = self.match_episodes_with_database(minio_episodes)
        return matched_episodes
    
    def get_category_tags(self, category: str = "business") -> List[str]:
        """
        根據類別獲取相關標籤
        """
        tag_mapping = {
            "business": ["投資理財", "股票分析", "經濟分析", "財務規劃"],
            "education": ["學習方法", "教育理念", "知識分享", "個人成長"]
        }
        
        return tag_mapping.get(category, ["一般", "知識分享", "學習", "成長"])

def main():
    """測試函數"""
    service = MinioEpisodeService()
    
    print("=== 測試 MinIO 節目服務 ===")
    
    # 獲取所有可用節目
    episodes = service.get_available_episodes()
    
    print(f"找到 {len(episodes)} 個可用節目:")
    for i, ep in enumerate(episodes[:5], 1):  # 只顯示前5個
        print(f"{i}. {ep['episode_title']}")
        print(f"   節目: {ep['podcast_name']}")
        print(f"   Episode ID: {ep['episode_id']}")
        print(f"   RSS ID: {ep['rss_id']}")
        print(f"   MinIO 檔案: {ep['minio_filename']}")
        print()

if __name__ == "__main__":
    main() 