#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL 資料匯入器

整合所有 PostgreSQL 匯入功能，提供統一的介面。
支援直接連接、SSH 隧道、遠端執行等多種連接方式。
"""

import os
import sys
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from abc import ABC, abstractmethod

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BasePostgreSQLInserter(ABC):
    """PostgreSQL 匯入器基礎類別"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化匯入器
        
        Args:
            config: 資料庫配置
        """
        self.config = config
        self.conn: Optional[psycopg2.extensions.connection] = None
    
    @abstractmethod
    def connect(self) -> bool:
        """建立資料庫連接"""
        pass
    
    def disconnect(self):
        """關閉資料庫連接"""
        if self.conn:
            self.conn.close()
            logger.info("資料庫連接已關閉")
    
    def ensure_tables_exist(self) -> bool:
        """確保必要的表格存在"""
        if not self.conn:
            logger.error("資料庫連接未建立")
            return False
            
        try:
            with self.conn.cursor() as cursor:
                # 檢查 podcasts 表格
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'podcasts'
                    )
                """)
                
                result = cursor.fetchone()
                if not result or not result[0]:
                    logger.info("建立 podcasts 表格...")
                    cursor.execute("""
                        CREATE TABLE podcasts (
                            podcast_id SERIAL PRIMARY KEY,
                            spotify_id VARCHAR(255) UNIQUE,
                            name VARCHAR(500) NOT NULL,
                            description TEXT,
                            publisher VARCHAR(255),
                            languages VARCHAR(50),
                            explicit BOOLEAN DEFAULT FALSE,
                            total_episodes INTEGER DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    logger.info("podcasts 表格建立完成")
                
                # 檢查 episodes 表格
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'episodes'
                    )
                """)
                
                result = cursor.fetchone()
                if not result or not result[0]:
                    logger.info("建立 episodes 表格...")
                    cursor.execute("""
                        CREATE TABLE episodes (
                            episode_id SERIAL PRIMARY KEY,
                            podcast_id INTEGER REFERENCES podcasts(podcast_id),
                            spotify_episode_id VARCHAR(255) UNIQUE,
                            title VARCHAR(500) NOT NULL,
                            description TEXT,
                            published_date TIMESTAMP,
                            duration_ms INTEGER DEFAULT 0,
                            audio_preview_url TEXT,
                            external_urls JSONB,
                            explicit BOOLEAN DEFAULT FALSE,
                            languages VARCHAR(50),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    logger.info("episodes 表格建立完成")
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"表格建立失敗: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def insert_podcast(self, podcast_data: Dict[str, Any]) -> int:
        """插入 Podcast 資料
        
        Args:
            podcast_data: Podcast 資料
            
        Returns:
            podcast_id: 插入的 Podcast ID
        """
        if not self.conn:
            raise Exception("資料庫連接未建立")
            
        try:
            with self.conn.cursor() as cursor:
                # 先檢查是否已存在
                cursor.execute("SELECT podcast_id FROM podcasts WHERE spotify_id = %s", 
                             (podcast_data.get('id'),))
                existing = cursor.fetchone()
                
                if existing and existing[0]:
                    podcast_id = existing[0]
                    logger.info(f"Podcast 已存在: {podcast_data.get('name', 'Unknown')} (ID: {podcast_id})")
                    return podcast_id
                
                # 插入新資料
                cursor.execute("""
                    INSERT INTO podcasts (
                        spotify_id, name, description, publisher, 
                        languages, explicit, total_episodes, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING podcast_id
                """, (
                    podcast_data.get('id'),
                    podcast_data.get('name', ''),
                    podcast_data.get('description', ''),
                    podcast_data.get('publisher', ''),
                    ','.join(podcast_data.get('languages', ['zh-TW'])),
                    podcast_data.get('explicit', False),
                    podcast_data.get('total_episodes', 0),
                    datetime.now(),
                    datetime.now()
                ))
                
                podcast_id = cursor.fetchone()[0]
                self.conn.commit()
                logger.info(f"Podcast 插入成功: {podcast_data.get('name', 'Unknown')} (ID: {podcast_id})")
                return podcast_id
                
        except Exception as e:
            logger.error(f"Podcast 插入失敗: {e}")
            if self.conn:
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
        if not self.conn:
            raise Exception("資料庫連接未建立")
            
        try:
            with self.conn.cursor() as cursor:
                # 先檢查是否已存在
                cursor.execute("SELECT episode_id FROM episodes WHERE spotify_episode_id = %s", 
                             (episode_data.get('id'),))
                existing = cursor.fetchone()
                
                if existing and existing[0]:
                    episode_id = existing[0]
                    logger.info(f"Episode 已存在: {episode_data.get('name', 'Unknown')} (ID: {episode_id})")
                    return episode_id
                
                # 插入新資料
                cursor.execute("""
                    INSERT INTO episodes (
                        podcast_id, spotify_episode_id, title, description,
                        published_date, duration_ms, audio_preview_url,
                        external_urls, explicit, languages, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING episode_id
                """, (
                    podcast_id,
                    episode_data.get('id'),
                    episode_data.get('name', ''),
                    episode_data.get('description', ''),
                    episode_data.get('release_date'),
                    episode_data.get('duration_ms', 0),
                    episode_data.get('audio_preview_url', ''),
                    json.dumps(episode_data.get('external_urls', {})),
                    episode_data.get('explicit', False),
                    ','.join(episode_data.get('languages', ['zh-TW'])),
                    datetime.now(),
                    datetime.now()
                ))
                
                episode_id = cursor.fetchone()[0]
                self.conn.commit()
                logger.info(f"Episode 插入成功: {episode_data.get('name', 'Unknown')} (ID: {episode_id})")
                return episode_id
                
        except Exception as e:
            logger.error(f"Episode 插入失敗: {e}")
            if self.conn:
                self.conn.rollback()
            raise

class PostgreSQLInserter(BasePostgreSQLInserter):
    """標準 PostgreSQL 匯入器
    
    支援直接連接和 SSH 隧道連接。
    """
    
    def connect(self) -> bool:
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
            return True
            
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            return False
    
    def process_episodes_data(self, episodes_data: List[Dict[str, Any]], 
                            podcast_data: Dict[str, Any]) -> Dict[str, Any]:
        """處理 episodes 資料並匯入資料庫
        
        Args:
            episodes_data: episodes 資料列表
            podcast_data: podcast 資料
            
        Returns:
            處理結果統計
        """
        try:
            # 確保表格存在
            if not self.ensure_tables_exist():
                raise Exception("表格建立失敗")
            
            # 插入 podcast
            podcast_id = self.insert_podcast(podcast_data)
            
            # 批次插入 episodes
            success_count = 0
            for episode in episodes_data:
                try:
                    self.insert_episode(episode, podcast_id)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Episode 插入失敗: {e}")
                    continue
            
            result = {
                'total_episodes': len(episodes_data),
                'successful_inserts': success_count,
                'failed_inserts': len(episodes_data) - success_count,
                'podcast_id': podcast_id
            }
            
            logger.info(f"資料匯入完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"資料處理失敗: {e}")
            raise

class BatchPostgreSQLInserter(BasePostgreSQLInserter):
    """批次 PostgreSQL 匯入器
    
    專門處理 batch_input 資料夾中的資料。
    """
    
    def connect(self) -> bool:
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
            logger.info("PostgreSQL 批次匯入器連接成功")
            return True
            
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            return False
    
    def process_batch_input_folder(self, folder_path: str) -> List[Dict[str, Any]]:
        """處理 batch_input 資料夾
        
        Args:
            folder_path: batch_input 資料夾路徑
            
        Returns:
            處理結果列表
        """
        try:
            if not self.ensure_tables_exist():
                raise Exception("表格建立失敗")
            
            results = []
            
            # 處理所有 JSON 檔案
            for file in os.listdir(folder_path):
                if file.endswith('.json') and not file.startswith('._'):
                    file_path = os.path.join(folder_path, file)
                    result = self.process_file(file_path)
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"批次處理失敗: {e}")
            raise
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """處理單個檔案
        
        Args:
            file_path: 檔案路徑
            
        Returns:
            處理結果
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"處理檔案: {file_path}")
            
            # 根據檔案類型處理
            if 'episodes' in data:
                # Spotify 格式
                episodes = data['episodes']
                podcast_data = {
                    'id': '1500839292',
                    'name': 'Gooaye 股癌',
                    'description': '晦澀金融投資知識直白講，重要海內外時事輕鬆談',
                    'publisher': '謝孟恭',
                    'languages': ['zh-TW'],
                    'explicit': False,
                    'total_episodes': len(episodes)
                }
                
                result = self.process_episodes_data(episodes, podcast_data)
                result['file'] = file_path
                return result
            
            else:
                logger.warning(f"未知檔案格式: {file_path}")
                return {'file': file_path, 'total': 0, 'success': 0}
                
        except Exception as e:
            logger.error(f"檔案處理失敗 {file_path}: {e}")
            return {'file': file_path, 'total': 0, 'success': 0, 'error': str(e)}
    
    def process_episodes_data(self, episodes_data: List[Dict[str, Any]], 
                            podcast_data: Dict[str, Any]) -> Dict[str, Any]:
        """處理 episodes 資料並匯入資料庫
        
        Args:
            episodes_data: episodes 資料列表
            podcast_data: podcast 資料
            
        Returns:
            處理結果統計
        """
        try:
            # 插入 podcast
            podcast_id = self.insert_podcast(podcast_data)
            
            # 批次插入 episodes
            success_count = 0
            for episode in episodes_data:
                try:
                    self.insert_episode(episode, podcast_id)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Episode 插入失敗: {e}")
                    continue
            
            result = {
                'total': len(episodes_data),
                'success': success_count,
                'podcast_id': podcast_id
            }
            
            return result
            
        except Exception as e:
            logger.error(f"資料處理失敗: {e}")
            raise 