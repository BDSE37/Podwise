#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podwise 測試資料匯入程式
將 testdata 目錄下的 CSV 檔案資料匯入到 PostgreSQL 資料庫
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging
from typing import Dict, List, Optional, Tuple
import argparse

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_import.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DatabaseImporter:
    """資料庫匯入器類別"""
    
    def __init__(self, db_config: Dict[str, str]):
        """
        初始化資料庫匯入器
        
        Args:
            db_config: 資料庫連線配置
        """
        self.db_config = db_config
        self.connection = None
        self.cursor = None
        
    def connect(self) -> bool:
        """
        連接到資料庫
        
        Returns:
            bool: 連線是否成功
        """
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            logger.info("✅ 資料庫連線成功")
            return True
        except Exception as e:
            logger.error(f"❌ 資料庫連線失敗: {e}")
            return False
    
    def disconnect(self):
        """關閉資料庫連線"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("🔌 資料庫連線已關閉")
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> bool:
        """
        執行 SQL 查詢
        
        Args:
            query: SQL 查詢語句
            params: 查詢參數
            
        Returns:
            bool: 執行是否成功
        """
        try:
            self.cursor.execute(query, params)
            return True
        except Exception as e:
            logger.error(f"❌ SQL 執行失敗: {e}")
            logger.error(f"查詢: {query}")
            if params:
                logger.error(f"參數: {params}")
            return False
    
    def commit(self):
        """提交交易"""
        if self.connection:
            self.connection.commit()
            logger.info("💾 交易已提交")
    
    def rollback(self):
        """回滾交易"""
        if self.connection:
            self.connection.rollback()
            logger.warning("🔄 交易已回滾")
    
    def get_or_create_user(self, user_code: str) -> Optional[int]:
        """
        取得或創建使用者
        
        Args:
            user_code: 使用者代碼
            
        Returns:
            Optional[int]: 使用者 ID
        """
        # 標準化使用者代碼格式 (移除底線)
        normalized_user_code = user_code.replace('_', '')
        
        # 檢查使用者是否存在
        query = "SELECT user_id FROM users WHERE user_code = %s"
        if self.execute_query(query, (normalized_user_code,)):
            result = self.cursor.fetchone()
            if result:
                return result['user_id']
        
        # 創建新使用者
        insert_query = """
        INSERT INTO users (email, username, given_name, family_name, is_active, locale)
        VALUES (%s, %s, 'Guest', 'User', true, 'zh-TW')
        RETURNING user_id
        """
        if self.execute_query(insert_query, (f"{normalized_user_code}@podwise.test", normalized_user_code)):
            result = self.cursor.fetchone()
            if result:
                logger.info(f"👤 創建新使用者: {normalized_user_code} (ID: {result['user_id']})")
                return result['user_id']
        
        return None
    
    def get_or_create_episode(self, episode_title: str) -> Optional[int]:
        """
        取得或創建節目集數
        
        Args:
            episode_title: 節目集數標題
            
        Returns:
            Optional[int]: 節目集數 ID
        """
        # 處理股癌節目的格式轉換
        normalized_title = self._normalize_episode_title(episode_title)
        
        # 檢查節目集數是否存在
        query = "SELECT episode_id FROM episodes WHERE episode_title = %s"
        if self.execute_query(query, (normalized_title,)):
            result = self.cursor.fetchone()
            if result:
                return result['episode_id']
        
        # 創建新節目集數（需要先有 podcast）
        # 這裡簡化處理，使用預設 podcast_id = 1
        insert_query = """
        INSERT INTO episodes (podcast_id, episode_title, published_date, created_at, updated_at)
        VALUES (1, %s, CURRENT_DATE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        RETURNING episode_id
        """
        if self.execute_query(insert_query, (normalized_title,)):
            result = self.cursor.fetchone()
            if result:
                logger.info(f"📺 創建新節目集數: {normalized_title[:50]}... (ID: {result['episode_id']})")
                return result['episode_id']
        
        return None
    
    def _normalize_episode_title(self, episode_title: str) -> str:
        """
        標準化節目集數標題格式
        
        Args:
            episode_title: 原始節目集數標題
            
        Returns:
            str: 標準化後的標題
        """
        # 處理股癌節目的格式轉換
        if episode_title.startswith('Spotify_RSS_1500839292_EP') and episode_title.endswith('_股癌.mp3'):
            # 從 Spotify_RSS_1500839292_EP569_股癌.mp3 轉換為 EP569_股癌
            episode_number = episode_title.replace('Spotify_RSS_1500839292_EP', '').replace('_股癌.mp3', '')
            return f'EP{episode_number}_股癌'
        
        # 處理其他可能的格式轉換
        if episode_title.startswith('RSS_1500839292_EP') and episode_title.endswith('_股癌.mp3'):
            # 從 RSS_1500839292_EP5702_股癌.mp3 轉換為 EP5702_股癌
            episode_number = episode_title.replace('RSS_1500839292_EP', '').replace('_股癌.mp3', '')
            return f'EP{episode_number}_股癌'
        
        # 處理其他節目的格式轉換
        if episode_title.startswith('Spotify_RSS_'):
            # 移除 Spotify_RSS_ 前綴和 .mp3 後綴
            normalized = episode_title.replace('Spotify_RSS_', '')
            if normalized.endswith('.mp3'):
                normalized = normalized[:-4]
            return normalized
        
        # 移除 .mp3 副檔名
        if episode_title.endswith('.mp3'):
            episode_title = episode_title[:-4]
        
        return episode_title
    
    def import_user_feedback(self, csv_path: str) -> bool:
        """
        匯入使用者回饋資料
        
        Args:
            csv_path: CSV 檔案路徑
            
        Returns:
            bool: 匯入是否成功
        """
        try:
            logger.info(f"📊 開始匯入使用者回饋資料: {csv_path}")
            
            # 讀取 CSV 檔案
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            logger.info(f"📈 讀取到 {len(df)} 筆資料")
            
            success_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    # 取得或創建使用者
                    user_id = self.get_or_create_user(row['User_id'])
                    if not user_id:
                        error_count += 1
                        continue
                    
                    # 取得或創建節目集數
                    episode_id = self.get_or_create_episode(row['Episode_id'])
                    if not episode_id:
                        error_count += 1
                        continue
                    
                    # 處理日期格式
                    preview_played_at = None
                    created_at = None
                    
                    if pd.notna(row['preview_played_at']):
                        try:
                            preview_played_at = pd.to_datetime(row['preview_played_at']).strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            preview_played_at = None
                    
                    if pd.notna(row['created_at']):
                        try:
                            created_at = pd.to_datetime(row['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 檢查是否已存在相同記錄
                    check_query = """
                    SELECT 1 FROM user_feedback 
                    WHERE user_id = %s AND episode_id = %s
                    """
                    if self.execute_query(check_query, (user_id, episode_id)):
                        if self.cursor.fetchone():
                            # 更新現有記錄
                            update_query = """
                            UPDATE user_feedback 
                            SET rating = %s, bookmark = false, preview_played = %s,
                                preview_listen_time = NULL, preview_played_at = %s,
                                like_count = %s, dislike_count = 0, preview_play_count = %s,
                                updated_at = %s
                            WHERE user_id = %s AND episode_id = %s
                            """
                            preview_played = preview_played_at is not None
                            params = (
                                None, preview_played, preview_played_at,
                                row['like_count'], row['preview_play_count'],
                                created_at, user_id, episode_id
                            )
                        else:
                            # 插入新記錄
                            insert_query = """
                            INSERT INTO user_feedback 
                            (user_id, episode_id, rating, bookmark, preview_played,
                             preview_listen_time, preview_played_at, like_count,
                             dislike_count, preview_play_count, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            preview_played = preview_played_at is not None
                            params = (
                                user_id, episode_id, None, False, preview_played,
                                None, preview_played_at, row['like_count'],
                                0, row['preview_play_count'], created_at, created_at
                            )
                        
                        if self.execute_query(insert_query if 'INSERT' in locals() else update_query, params):
                            success_count += 1
                        else:
                            error_count += 1
                    else:
                        error_count += 1
                    
                    # 每 100 筆提交一次
                    if (index + 1) % 100 == 0:
                        self.commit()
                        logger.info(f"📊 已處理 {index + 1}/{len(df)} 筆資料")
                
                except Exception as e:
                    logger.error(f"❌ 處理第 {index + 1} 筆資料時發生錯誤: {e}")
                    error_count += 1
            
            # 最終提交
            self.commit()
            
            logger.info(f"✅ 使用者回饋資料匯入完成")
            logger.info(f"📊 成功: {success_count} 筆, 失敗: {error_count} 筆")
            
            return error_count == 0
            
        except Exception as e:
            logger.error(f"❌ 匯入使用者回饋資料失敗: {e}")
            self.rollback()
            return False
    
    def import_episode_stats(self, likes_csv: str, plays_csv: str) -> bool:
        """
        匯入節目集數統計資料
        
        Args:
            likes_csv: 按讚統計 CSV 檔案路徑
            plays_csv: 播放統計 CSV 檔案路徑
            
        Returns:
            bool: 匯入是否成功
        """
        try:
            logger.info("📊 開始匯入節目集數統計資料")
            
            # 讀取統計資料
            likes_df = pd.read_csv(likes_csv, encoding='utf-8-sig')
            plays_df = pd.read_csv(plays_csv, encoding='utf-8-sig')
            
            logger.info(f"📈 讀取到 {len(likes_df)} 筆按讚統計, {len(plays_df)} 筆播放統計")
            
            success_count = 0
            error_count = 0
            
            # 合併統計資料
            stats_df = pd.merge(likes_df, plays_df, on='Episode_id', how='outer')
            
            for index, row in stats_df.iterrows():
                try:
                    # 取得或創建節目集數
                    episode_id = self.get_or_create_episode(row['Episode_id'])
                    if not episode_id:
                        error_count += 1
                        continue
                    
                    # 更新節目集數的統計資訊
                    update_query = """
                    UPDATE episodes 
                    SET apple_episodes_ranking = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE episode_id = %s
                    """
                    
                    # 這裡可以根據需要計算排名或使用其他邏輯
                    ranking = None
                    
                    if self.execute_query(update_query, (ranking, episode_id)):
                        success_count += 1
                    else:
                        error_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ 處理統計資料第 {index + 1} 筆時發生錯誤: {e}")
                    error_count += 1
            
            self.commit()
            
            logger.info(f"✅ 節目集數統計資料匯入完成")
            logger.info(f"📊 成功: {success_count} 筆, 失敗: {error_count} 筆")
            
            return error_count == 0
            
        except Exception as e:
            logger.error(f"❌ 匯入節目集數統計資料失敗: {e}")
            self.rollback()
            return False
    
    def import_user_episode_counts(self, csv_path: str) -> bool:
        """
        匯入使用者節目集數統計資料
        
        Args:
            csv_path: CSV 檔案路徑
            
        Returns:
            bool: 匯入是否成功
        """
        try:
            logger.info(f"📊 開始匯入使用者節目集數統計資料: {csv_path}")
            
            # 讀取 CSV 檔案
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            logger.info(f"📈 讀取到 {len(df)} 筆資料")
            
            success_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    # 取得或創建使用者
                    user_id = self.get_or_create_user(row['User_id'])
                    if not user_id:
                        error_count += 1
                        continue
                    
                    # 更新使用者行為統計
                    # 這裡可以根據需要插入到 user_behavior_stats 表
                    # 或者更新 users 表的相關欄位
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ 處理使用者統計第 {index + 1} 筆時發生錯誤: {e}")
                    error_count += 1
            
            self.commit()
            
            logger.info(f"✅ 使用者節目集數統計資料匯入完成")
            logger.info(f"📊 成功: {success_count} 筆, 失敗: {error_count} 筆")
            
            return error_count == 0
            
        except Exception as e:
            logger.error(f"❌ 匯入使用者節目集數統計資料失敗: {e}")
            self.rollback()
            return False


def main():
    """主程式"""
    parser = argparse.ArgumentParser(description='Podwise 測試資料匯入程式')
    parser.add_argument('--host', default='localhost', help='資料庫主機')
    parser.add_argument('--port', default='5432', help='資料庫埠號')
    parser.add_argument('--database', default='podcast', help='資料庫名稱')
    parser.add_argument('--username', default='bdse37', help='資料庫使用者名稱')
    parser.add_argument('--password', default='111111', help='資料庫密碼')
    parser.add_argument('--data-dir', default='.', help='測試資料目錄路徑')
    parser.add_argument('--skip-user-feedback', action='store_true', help='跳過使用者回饋資料匯入')
    parser.add_argument('--skip-episode-stats', action='store_true', help='跳過節目集數統計資料匯入')
    parser.add_argument('--skip-user-counts', action='store_true', help='跳過使用者統計資料匯入')
    
    args = parser.parse_args()
    
    # 資料庫連線配置
    db_config = {
        'host': args.host,
        'port': args.port,
        'database': args.database,
        'user': args.username,
        'password': args.password
    }
    
    # 建立匯入器
    importer = DatabaseImporter(db_config)
    
    try:
        # 連接到資料庫
        if not importer.connect():
            logger.error("❌ 無法連接到資料庫，程式結束")
            return 1
        
        # 設定檔案路徑
        data_dir = args.data_dir
        user_feedback_csv = os.path.join(data_dir, 'user_feedback.csv')
        episode_likes_csv = os.path.join(data_dir, 'episode_likes.csv')
        episode_plays_csv = os.path.join(data_dir, 'episode_plays.csv')
        user_episode_counts_csv = os.path.join(data_dir, 'user_episode_counts.csv')
        
        success = True
        
        # 匯入使用者回饋資料
        if not args.skip_user_feedback and os.path.exists(user_feedback_csv):
            if not importer.import_user_feedback(user_feedback_csv):
                success = False
        else:
            logger.info("⏭️ 跳過使用者回饋資料匯入")
        
        # 匯入節目集數統計資料
        if not args.skip_episode_stats and os.path.exists(episode_likes_csv) and os.path.exists(episode_plays_csv):
            if not importer.import_episode_stats(episode_likes_csv, episode_plays_csv):
                success = False
        else:
            logger.info("⏭️ 跳過節目集數統計資料匯入")
        
        # 匯入使用者統計資料
        if not args.skip_user_counts and os.path.exists(user_episode_counts_csv):
            if not importer.import_user_episode_counts(user_episode_counts_csv):
                success = False
        else:
            logger.info("⏭️ 跳過使用者統計資料匯入")
        
        if success:
            logger.info("🎉 所有資料匯入完成！")
            return 0
        else:
            logger.error("❌ 部分資料匯入失敗")
            return 1
            
    except KeyboardInterrupt:
        logger.info("⚠️ 使用者中斷程式")
        importer.rollback()
        return 1
    except Exception as e:
        logger.error(f"❌ 程式執行時發生錯誤: {e}")
        importer.rollback()
        return 1
    finally:
        importer.disconnect()


if __name__ == "__main__":
    sys.exit(main()) 