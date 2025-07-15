#!/usr/bin/env python3
"""
修正 Milvus 中的 episode_id 並補充缺少的欄位
將 MongoDB ObjectId 替換為 PostgreSQL 的整數 ID
使用 BGE-M3 模型生成 embedding
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
import logging
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from pymilvus import connections, Collection, utility
import numpy as np

# 載入環境變數
load_dotenv('backend/.env')

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BGE_M3_Embedding:
    """BGE-M3 embedding 生成器"""
    
    def __init__(self):
        try:
            from sentence_transformers import SentenceTransformer
            # 載入 BGE-M3 模型
            self.model = SentenceTransformer('BAAI/bge-m3')
            logger.info("成功載入 BGE-M3 模型")
        except ImportError:
            logger.error("請先安裝 sentence-transformers: pip install sentence-transformers")
            self.model = None
        except Exception as e:
            logger.error(f"載入 BGE-M3 模型失敗: {str(e)}")
            self.model = None
    
    def generate_embedding(self, text: str) -> List[float]:
        """生成 BGE-M3 embedding"""
        if not self.model:
            logger.warning("BGE-M3 模型未載入，使用零向量")
            return [0.0] * 1024
        
        try:
            # 生成 embedding
            embedding = self.model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"生成 embedding 失敗: {str(e)}")
            return [0.0] * 1024

class MilvusEpisodeIdFixer:
    """修正 Milvus 中的 episode_id 並補充缺少的欄位"""
    
    def __init__(self):
        self.stage3_path = Path("backend/vector_pipeline/data/stage3_tagging")
        
        # PostgreSQL 連接設定
        self.pg_config = {
            'host': os.getenv('POSTGRES_HOST', 'postgres.podwise.svc.cluster.local'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'podcast'),
            'user': os.getenv('POSTGRES_USER', 'bdse37'),
            'password': os.getenv('POSTGRES_PASSWORD', '111111')
        }
        
        # Milvus 連接設定
        self.milvus_config = {
            'host': os.getenv('MILVUS_HOST', '192.168.32.86'),
            'port': os.getenv('MILVUS_PORT', '19530')
        }
        
        self.collection_name = "podcast_chunks"
        
        # 初始化 BGE-M3 embedding 生成器
        self.embedding_generator = BGE_M3_Embedding()
    
    def connect_postgresql(self):
        """連接 PostgreSQL"""
        try:
            conn = psycopg2.connect(**self.pg_config)
            return conn
        except Exception as e:
            logger.error(f"連接 PostgreSQL 失敗: {str(e)}")
            return None
    
    def connect_milvus(self):
        """連接 Milvus"""
        try:
            connections.connect(
                alias="default",
                host=self.milvus_config['host'],
                port=self.milvus_config['port']
            )
            logger.info("成功連接 Milvus")
            return True
        except Exception as e:
            logger.error(f"連接 Milvus 失敗: {str(e)}")
            return False
    
    def get_postgresql_episodes(self) -> Dict[str, Dict]:
        """從 PostgreSQL 取得完整的 episodes 和 podcasts 資料"""
        conn = self.connect_postgresql()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # 查詢 episodes 和 podcasts 表
            query = """
            SELECT 
                e.episode_id,
                e.episode_title,
                e.duration,
                e.published_date,
                e.apple_episodes_ranking as apple_rating,
                e.created_at,
                e.languages,
                p.podcast_id,
                p.podcast_name,
                p.author,
                p.category,
                p.apple_rating as podcast_apple_rating
            FROM episodes e
            JOIN podcasts p ON e.podcast_id = p.podcast_id
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            episodes = {}
            for row in results:
                episode_id, episode_title, duration, published_date, apple_rating, created_at, \
                languages, podcast_id, podcast_name, author, category, podcast_apple_rating = row
                
                episodes[str(episode_id)] = {
                    'episode_id': episode_id,
                    'episode_title': episode_title,
                    'duration': duration,
                    'published_date': published_date,
                    'apple_rating': apple_rating,
                    'created_at': created_at,
                    'languages': languages,
                    'podcast_id': podcast_id,
                    'podcast_name': podcast_name,
                    'author': author,
                    'category': category,
                    'podcast_apple_rating': podcast_apple_rating
                }
            
            cursor.close()
            conn.close()
            
            logger.info(f"從 PostgreSQL 取得 {len(episodes)} 筆 episodes 資料")
            return episodes
            
        except Exception as e:
            logger.error(f"查詢 PostgreSQL 失敗: {str(e)}")
            if conn:
                conn.close()
            return {}
    
    def extract_info_from_filename(self, filename: str) -> Tuple[Optional[int], Optional[str], Optional[str]]:
        """從檔案名稱中提取 podcast_id 和 episode_title"""
        # 檔案名稱格式: RSS_1776077547_podcast_1321_EP39 最好研究公司的做法親身使用公司的產品.json
        try:
            # 移除 .json 副檔名
            name = filename.replace('.json', '')
            
            # 分割檔案名稱
            parts = name.split('_')
            
            if len(parts) >= 3 and parts[0] == 'RSS':
                # 提取 podcast_id (RSS_1776077547 中的 1776077547)
                podcast_id = int(parts[1])
                
                # 提取 episode_title (從 podcast_1321_EP39 開始到結尾)
                episode_title_parts = parts[2:]
                episode_title = '_'.join(episode_title_parts)
                
                # 提取 EP 編號用於匹配
                ep_match = None
                for part in episode_title_parts:
                    if part.startswith('EP'):
                        ep_match = part.split()[0]  # 只取 EP39 部分
                        break
                
                return podcast_id, episode_title, ep_match
            
            return None, None, None
        except Exception as e:
            logger.error(f"解析檔案名稱失敗 {filename}: {str(e)}")
            return None, None, None
    
    def find_postgresql_episode(self, podcast_id: int, ep_match: str, pg_episodes: Dict) -> Optional[Dict]:
        """根據 podcast_id 和 EP 編號找到對應的 PostgreSQL episode"""
        try:
            # 查詢 PostgreSQL
            conn = psycopg2.connect(**self.pg_config)
            cursor = conn.cursor()
            
            query = """
            SELECT 
                e.episode_id,
                e.episode_title,
                e.duration,
                e.published_date,
                e.apple_episodes_ranking as apple_rating,
                e.created_at,
                e.languages,
                p.podcast_id,
                p.podcast_name,
                p.author,
                p.category,
                p.apple_rating as podcast_apple_rating
            FROM episodes e
            JOIN podcasts p ON e.podcast_id = p.podcast_id
            WHERE p.podcast_id = %s AND e.episode_title LIKE %s
            """
            
            cursor.execute(query, (podcast_id, f'%{ep_match}%'))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                episode_id, episode_title, duration, published_date, apple_rating, created_at, \
                languages, podcast_id, podcast_name, author, category, podcast_apple_rating = result
                
                return {
                    'episode_id': episode_id,
                    'episode_title': episode_title,
                    'duration': duration,
                    'published_date': published_date,
                    'apple_rating': apple_rating,
                    'created_at': created_at,
                    'languages': languages,
                    'podcast_id': podcast_id,
                    'podcast_name': podcast_name,
                    'author': author,
                    'category': category,
                    'podcast_apple_rating': podcast_apple_rating
                }
            
            return None
            
        except Exception as e:
            logger.error(f"查詢 PostgreSQL episode 失敗: {str(e)}")
            return None
    
    def process_json_file(self, file_path: Path, pg_episodes: Dict) -> List[Dict]:
        """處理單一 JSON 檔案，補充缺少的欄位"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取檔案資訊
            podcast_id, episode_title, ep_match = self.extract_info_from_filename(file_path.name)
            
            if podcast_id is None or ep_match is None:
                logger.warning(f"無法解析檔案名稱: {file_path.name}")
                return []
            
            # 找到對應的 PostgreSQL episode
            pg_episode = self.find_postgresql_episode(podcast_id, ep_match, pg_episodes)
            
            if not pg_episode:
                logger.warning(f"找不到對應的 PostgreSQL episode: {file_path.name}")
                return []
            
            # 處理 chunks
            chunks = data.get('chunks', [])
            processed_chunks = []
            
            for i, chunk in enumerate(chunks):
                # 生成 BGE-M3 embedding
                chunk_text = chunk.get('chunk_text', '')
                embedding = self.embedding_generator.generate_embedding(chunk_text)
                
                # 補充缺少的欄位
                processed_chunk = {
                    'chunk_id': chunk.get('chunk_id', f"{pg_episode['episode_id']}_{i}"),
                    'chunk_index': chunk.get('chunk_index', i),
                    'episode_id': str(pg_episode['episode_id']),  # 使用 PostgreSQL 的 episode_id
                    'podcast_id': str(pg_episode['podcast_id']),
                    'podcast_name': pg_episode['podcast_name'],
                    'author': pg_episode['author'],
                    'category': pg_episode['category'],
                    'episode_title': pg_episode['episode_title'],
                    'duration': pg_episode['duration'],
                    'published_date': pg_episode['published_date'],
                    'apple_rating': pg_episode['apple_rating'],
                    'chunk_text': chunk_text,
                    'embedding': embedding,  # 使用 BGE-M3 生成的 embedding
                    'language': pg_episode['languages'],
                    'created_at': pg_episode['created_at'].isoformat() if pg_episode['created_at'] else None,
                    'source_model': 'bge-m3',  # 使用 BGE-M3 模型
                    'tags': chunk.get('enhanced_tags', [])  # 使用 enhanced_tags 作為 tags
                }
                
                processed_chunks.append(processed_chunk)
            
            logger.info(f"處理檔案 {file_path.name}: {len(processed_chunks)} 個 chunks")
            return processed_chunks
            
        except Exception as e:
            logger.error(f"處理檔案 {file_path} 失敗: {str(e)}")
            return []
    
    def update_milvus_collection(self, processed_chunks: List[Dict]):
        """更新 Milvus 集合"""
        try:
            # 連接 Milvus
            if not self.connect_milvus():
                return False
            
            # 取得集合
            collection = Collection(self.collection_name)
            collection.load()
            
            # 準備插入資料
            insert_data = {
                'chunk_id': [],
                'chunk_index': [],
                'episode_id': [],
                'podcast_id': [],
                'podcast_name': [],
                'author': [],
                'category': [],
                'episode_title': [],
                'duration': [],
                'published_date': [],
                'apple_rating': [],
                'chunk_text': [],
                'embedding': [],
                'language': [],
                'created_at': [],
                'source_model': [],
                'tags': []
            }
            
            for chunk in processed_chunks:
                for key in insert_data.keys():
                    if key == 'embedding':
                        # 確保 embedding 是正確的格式
                        embedding = chunk.get(key, [])
                        if isinstance(embedding, list) and len(embedding) > 0:
                            insert_data[key].append(embedding)
                        else:
                            # 如果沒有 embedding，使用零向量 (1024 維度)
                            insert_data[key].append([0.0] * 1024)
                    elif key == 'tags':
                        # 將 tags 轉換為字串
                        tags = chunk.get(key, [])
                        if isinstance(tags, list):
                            insert_data[key].append(','.join(tags))
                        else:
                            insert_data[key].append('')
                    else:
                        value = chunk.get(key, '')
                        if value is None:
                            value = ''
                        insert_data[key].append(value)
            
            # 插入資料
            collection.insert(insert_data)
            collection.flush()
            
            logger.info(f"成功插入 {len(processed_chunks)} 個 chunks 到 Milvus")
            return True
            
        except Exception as e:
            logger.error(f"更新 Milvus 集合失敗: {str(e)}")
            return False
    
    def process_all_files(self):
        """處理所有 JSON 檔案"""
        if not self.stage3_path.exists():
            logger.error(f"目錄不存在: {self.stage3_path}")
            return
        
        # 取得 PostgreSQL 資料
        pg_episodes = self.get_postgresql_episodes()
        
        if not pg_episodes:
            logger.error("無法取得 PostgreSQL 資料")
            return
        
        # 處理所有 JSON 檔案
        all_processed_chunks = []
        rss_dirs = [d for d in self.stage3_path.iterdir() if d.is_dir() and d.name.startswith("RSS_")]
        
        for rss_dir in rss_dirs:
            logger.info(f"處理目錄: {rss_dir.name}")
            json_files = list(rss_dir.glob("*.json"))
            
            for json_file in json_files:
                processed_chunks = self.process_json_file(json_file, pg_episodes)
                all_processed_chunks.extend(processed_chunks)
        
        logger.info(f"總共處理了 {len(all_processed_chunks)} 個 chunks")
        
        # 更新 Milvus 集合
        if all_processed_chunks:
            success = self.update_milvus_collection(all_processed_chunks)
            if success:
                logger.info("✅ 成功更新 Milvus 集合")
            else:
                logger.error("❌ 更新 Milvus 集合失敗")
        else:
            logger.warning("沒有找到可處理的 chunks")

def main():
    """主函數"""
    fixer = MilvusEpisodeIdFixer()
    fixer.process_all_files()

if __name__ == "__main__":
    main() 