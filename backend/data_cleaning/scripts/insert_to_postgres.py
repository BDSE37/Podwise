#!/usr/bin/env python3
"""
PostgreSQL 資料匯入腳本
將清整後的 episodes 資料匯入到 PostgreSQL 資料庫
"""

import os
import sys
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import List, Dict, Any, Optional

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PostgreSQLInserter:
    """PostgreSQL 資料匯入類別"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化資料庫連接
        
        Args:
            config: 資料庫配置
        """
        self.config = config
        self.conn = None
        self._connect()
    
    def _connect(self):
        """建立資料庫連接"""
        try:
            self.conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            self.conn.autocommit = False
            logger.info("PostgreSQL 連接成功")
            
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            raise
    
    def _ensure_tables_exist(self):
        """確保必要的表格存在"""
        try:
            with self.conn.cursor() as cursor:
                # 檢查 episodes 表格是否存在
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'episodes'
                    );
                """)
                
                if not cursor.fetchone()[0]:
                    logger.info("建立 episodes 表格...")
                    cursor.execute("""
                        CREATE TABLE episodes (
                            episode_id SERIAL PRIMARY KEY,
                            podcast_id INTEGER NOT NULL,
                            episode_title VARCHAR(255) NOT NULL,
                            published_date DATE,
                            audio_url VARCHAR(512),
                            duration INTEGER,
                            description TEXT,
                            audio_preview_url VARCHAR(512),
                            languages VARCHAR(64),
                            explicit BOOLEAN,
                            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            apple_episodes_ranking INTEGER
                        );
                    """)
                    
                    # 建立索引
                    cursor.execute("""
                        CREATE INDEX idx_episodes_podcast_id ON episodes(podcast_id);
                        CREATE INDEX idx_episodes_published_date ON episodes(published_date);
                    """)
                    
                    logger.info("episodes 表格建立完成")
                
                # 檢查 podcasts 表格是否存在
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'podcasts'
                    );
                """)
                
                if not cursor.fetchone()[0]:
                    logger.info("建立 podcasts 表格...")
                    cursor.execute("""
                        CREATE TABLE podcasts (
                            podcast_id INTEGER PRIMARY KEY,
                            name VARCHAR(255) NOT NULL,
                            description TEXT,
                            author VARCHAR(255),
                            rss_link VARCHAR(512) UNIQUE,
                            images_640 VARCHAR(512),
                            images_300 VARCHAR(512),
                            images_64 VARCHAR(512),
                            languages VARCHAR(64),
                            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            apple_podcasts_ranking INTEGER,
                            apple_rating DECIMAL(3,2),
                            category VARCHAR(64),
                            update_frequency VARCHAR(64)
                        );
                    """)
                    
                    logger.info("podcasts 表格建立完成")
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"表格建立失敗: {e}")
            self.conn.rollback()
            raise
    
    def insert_podcast(self, podcast_data: Dict[str, Any]) -> int:
        """插入 Podcast 資料
        
        Args:
            podcast_data: Podcast 資料
            
        Returns:
            podcast_id: 插入的 Podcast ID
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO podcasts (
                        podcast_id, name, description, author, rss_link, 
                        languages, category, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (podcast_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        author = EXCLUDED.author,
                        rss_link = EXCLUDED.rss_link,
                        languages = EXCLUDED.languages,
                        category = EXCLUDED.category,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING podcast_id
                """, (
                    podcast_data.get('podcast_id'),
                    podcast_data.get('name', ''),
                    podcast_data.get('description', ''),
                    podcast_data.get('author', ''),
                    podcast_data.get('rss_link', ''),
                    podcast_data.get('languages', 'zh-TW'),
                    podcast_data.get('category', ''),
                    datetime.now(),
                    datetime.now()
                ))
                
                podcast_id = cursor.fetchone()[0]
                self.conn.commit()
                logger.info(f"Podcast 插入成功: {podcast_data.get('name', 'Unknown')} (ID: {podcast_id})")
                return podcast_id
                
        except Exception as e:
            logger.error(f"Podcast 插入失敗: {e}")
            self.conn.rollback()
            raise
    
    def insert_episode(self, episode_data: Dict[str, Any], podcast_id: int) -> int:
        """插入 Episode 資料
        
        Args:
            episode_data: Episode 資料
            podcast_id: 對應的 Podcast ID
            
        Returns:
            episode_id: 插入的 Episode ID
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO episodes (
                        podcast_id, episode_title, published_date, audio_url, 
                        duration, description, audio_preview_url, languages, 
                        explicit, created_at, updated_at, apple_episodes_ranking
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING episode_id
                """, (
                    podcast_id,
                    episode_data.get('episode_title', ''),
                    episode_data.get('published_date'),
                    episode_data.get('audio_url', ''),
                    episode_data.get('duration', 0),
                    episode_data.get('description', ''),
                    episode_data.get('audio_preview_url', ''),
                    episode_data.get('languages', 'zh-TW'),
                    episode_data.get('explicit', False),
                    datetime.now(),
                    datetime.now(),
                    episode_data.get('apple_episodes_ranking')
                ))
                
                episode_id = cursor.fetchone()[0]
                self.conn.commit()
                logger.info(f"Episode 插入成功: {episode_data.get('episode_title', 'Unknown')} (ID: {episode_id})")
                return episode_id
                
        except Exception as e:
            logger.error(f"Episode 插入失敗: {e}")
            self.conn.rollback()
            raise
    
    def batch_insert_episodes(self, episodes_data: List[Dict[str, Any]], podcast_id: int) -> List[int]:
        """批次插入 Episode 資料
        
        Args:
            episodes_data: Episode 資料列表
            podcast_id: 對應的 Podcast ID
            
        Returns:
            episode_ids: 插入的 Episode ID 列表
        """
        episode_ids = []
        
        for i, episode_data in enumerate(episodes_data, 1):
            try:
                episode_id = self.insert_episode(episode_data, podcast_id)
                episode_ids.append(episode_id)
                logger.info(f"進度: {i}/{len(episodes_data)}")
                
            except Exception as e:
                logger.error(f"Episode {i} 插入失敗: {e}")
                continue
        
        return episode_ids
    
    def load_cleaned_data(self, file_path: str) -> List[Dict[str, Any]]:
        """載入清整後的資料
        
        Args:
            file_path: 資料檔案路徑
            
        Returns:
            清整後的資料列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"成功載入 {len(data)} 筆清整資料")
            return data
            
        except Exception as e:
            logger.error(f"資料載入失敗: {e}")
            raise
    
    def process_cleaned_data(self, cleaned_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """處理清整後的資料並匯入資料庫
        
        Args:
            cleaned_data: 清整後的資料列表
            
        Returns:
            處理結果統計
        """
        try:
            # 確保表格存在
            self._ensure_tables_exist()
            
            # 統計資訊
            stats = {
                'total_episodes': len(cleaned_data),
                'successful_inserts': 0,
                'failed_inserts': 0,
                'podcast_count': 0,
                'episode_ids': []
            }
            
            # 按 podcast_id 分組
            podcast_groups = {}
            for episode in cleaned_data:
                podcast_id = episode.get('podcast_id', 'unknown')
                if podcast_id not in podcast_groups:
                    podcast_groups[podcast_id] = []
                podcast_groups[podcast_id].append(episode)
            
            logger.info(f"發現 {len(podcast_groups)} 個不同的 Podcast")
            
            # 處理每個 Podcast
            for podcast_id, episodes in podcast_groups.items():
                try:
                    # 建立 Podcast 記錄
                    if episodes:
                        first_episode = episodes[0]
                        podcast_data = {
                            'podcast_id': podcast_id,
                            'name': first_episode.get('channel_info', {}).get('channel_name', f'Podcast {podcast_id}'),
                            'description': f'Podcast {podcast_id} 的描述',
                            'author': 'Unknown',
                            'rss_link': '',
                            'languages': 'zh-TW',
                            'category': first_episode.get('channel_info', {}).get('category', 'unknown')
                        }
                        
                        inserted_podcast_id = self.insert_podcast(podcast_data)
                        stats['podcast_count'] += 1
                        
                        # 插入 Episodes
                        episode_ids = self.batch_insert_episodes(episodes, inserted_podcast_id)
                        stats['successful_inserts'] += len(episode_ids)
                        stats['episode_ids'].extend(episode_ids)
                        
                        logger.info(f"Podcast {podcast_id} 處理完成: {len(episodes)} 個 episodes")
                    
                except Exception as e:
                    logger.error(f"Podcast {podcast_id} 處理失敗: {e}")
                    stats['failed_inserts'] += len(episodes)
                    continue
            
            logger.info("=== 資料匯入完成 ===")
            logger.info(f"總 Episodes: {stats['total_episodes']}")
            logger.info(f"成功插入: {stats['successful_inserts']}")
            logger.info(f"失敗插入: {stats['failed_inserts']}")
            logger.info(f"Podcast 數量: {stats['podcast_count']}")
            
            return stats
            
        except Exception as e:
            logger.error(f"資料處理失敗: {e}")
            raise
    
    def close(self):
        """關閉資料庫連接"""
        if self.conn:
            self.conn.close()
            logger.info("資料庫連接已關閉")

def main():
    """主程式"""
    # 資料庫配置
    config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'podcast'),
        'user': os.getenv('POSTGRES_USER', 'bdse37'),
        'password': os.getenv('POSTGRES_PASSWORD', '111111')
    }
    
    # 清整資料檔案路徑
    cleaned_data_path = "../../data/cleaned_data/processed_episodes.json"
    
    try:
        # 檢查檔案是否存在
        if not os.path.exists(cleaned_data_path):
            logger.error(f"找不到清整資料檔案: {cleaned_data_path}")
            logger.info("請先執行資料清整程式")
            return
        
        # 建立匯入器
        inserter = PostgreSQLInserter(config)
        
        # 載入清整資料
        cleaned_data = inserter.load_cleaned_data(cleaned_data_path)
        
        # 處理並匯入資料
        result = inserter.process_cleaned_data(cleaned_data)
        
        logger.info("資料匯入完成！")
        return result
        
    except Exception as e:
        logger.error(f"資料匯入失敗: {e}")
        sys.exit(1)
    finally:
        if 'inserter' in locals():
            inserter.close()

if __name__ == "__main__":
    main() 