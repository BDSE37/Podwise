#!/usr/bin/env python3
"""
修正 stage3_tagging 中的所有 JSON 檔案，使其符合 Milvus collection 的正確欄位形式
將 MongoDB ObjectId 替換為 PostgreSQL 的整數 ID
使用 BGE-M3 模型生成 embedding
補充所有缺少的欄位
輸出到 stage4_embedding_prep 目錄
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

class Stage3TaggingFixer:
    """修正 stage3_tagging 中的所有 JSON 檔案"""
    
    def __init__(self):
        self.stage3_path = Path("../vector_pipeline/data/stage3_tagging")
        self.output_path = Path("../vector_pipeline/data/stage4_embedding_prep")
        
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
        
        # 建立輸出目錄
        self.output_path.mkdir(exist_ok=True)
    
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
                e.apple_episodes_ranking,
                e.created_at,
                e.languages,
                p.podcast_id,
                p.podcast_name,
                p.author,
                p.category,
                p.apple_rating as apple_rating
            FROM episodes e
            JOIN podcasts p ON e.podcast_id = p.podcast_id
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            episodes = {}
            for row in results:
                episode_id, episode_title, duration, published_date, apple_episodes_ranking, created_at, \
                languages, podcast_id, podcast_name, author, category, apple_rating = row
                
                episodes[str(episode_id)] = {
                    'episode_id': episode_id,
                    'episode_title': episode_title,
                    'duration': duration,
                    'published_date': published_date,
                    'apple_episodes_ranking': apple_episodes_ranking,
                    'created_at': created_at,
                    'languages': languages,
                    'podcast_id': podcast_id,
                    'podcast_name': podcast_name,
                    'author': author,
                    'category': category,
                    'apple_rating': apple_rating
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
    
    def get_podcast_info(self, podcast_id: int) -> Optional[Dict]:
        """從 PostgreSQL 取得 podcast 的基本資訊"""
        try:
            conn = psycopg2.connect(**self.pg_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT podcast_id, podcast_name, author, category, apple_rating
                FROM podcasts
                WHERE podcast_id = %s
            """, (podcast_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                podcast_id, podcast_name, author, category, apple_rating = result
                return {
                    'podcast_id': podcast_id,
                    'podcast_name': podcast_name,
                    'author': author,
                    'category': category,
                    'apple_rating': apple_rating
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"查詢 podcast 資訊失敗: {str(e)}")
            return None

    def get_podcast_stats(self, podcast_id: int) -> Optional[Dict]:
        """取得 podcast 的統計資訊（平均 duration 等）"""
        try:
            conn = psycopg2.connect(**self.pg_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(duration) as episodes_with_duration,
                    AVG(duration) as avg_duration,
                    MIN(published_date) as earliest_date,
                    MAX(published_date) as latest_date
                FROM episodes
                WHERE podcast_id = %s AND duration IS NOT NULL
            """, (podcast_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result and result[0] > 0:
                episodes_with_duration, avg_duration, earliest_date, latest_date = result
                return {
                    'avg_duration': int(avg_duration) if avg_duration else None,
                    'earliest_date': earliest_date,
                    'latest_date': latest_date,
                    'episodes_with_duration': episodes_with_duration
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"取得 podcast 統計資訊失敗: {str(e)}")
            return None

    def extract_info_from_filename(self, filename: str) -> Tuple[Optional[int], Optional[str], Optional[str], Optional[str]]:
        """從檔案名稱中提取 podcast_id、episode_title、ep_match、主標題"""
        try:
            name = filename.replace('.json', '')
            parts = name.split('_')
            if len(parts) >= 3 and parts[0] == 'RSS':
                podcast_id = int(parts[1])
                episode_title_parts = parts[2:]
                episode_title = '_'.join(episode_title_parts)
                ep_match = None
                for part in episode_title_parts:
                    if part.startswith('EP'):
                        ep_match = part.split()[0]
                        break
                main_title = episode_title
                if episode_title.startswith('podcast_'):
                    main_title = episode_title.split('_', 2)[-1]
                if main_title.startswith('EP'):
                    main_title = main_title.split(' ', 1)[-1] if ' ' in main_title else main_title
                return podcast_id, episode_title, ep_match, main_title
            return None, None, None, None
        except Exception as e:
            logger.error(f"解析檔案名稱失敗 {filename}: {str(e)}")
            return None, None, None, None

    def find_postgresql_episode(self, podcast_id: int, ep_match: Optional[str], main_title: Optional[str]) -> Optional[Dict]:
        """根據 podcast_id、EP 編號或主標題找到對應的 PostgreSQL episode"""
        try:
            conn = psycopg2.connect(**self.pg_config)
            cursor = conn.cursor()
            results = []
            
            # 1. 先用 EPxx 查詢
            if ep_match:
                query = """
                SELECT e.episode_id, e.episode_title, e.duration, e.published_date, e.apple_episodes_ranking, e.created_at, e.languages, p.podcast_id, p.podcast_name, p.author, p.category, p.apple_rating as apple_rating
                FROM episodes e
                JOIN podcasts p ON e.podcast_id = p.podcast_id
                WHERE p.podcast_id = %s AND e.episode_title LIKE %s
                ORDER BY e.published_date DESC
                """
                cursor.execute(query, (podcast_id, f'%{ep_match}%'))
                results = cursor.fetchall()
            
            # 2. 若沒找到且有主標題，則用主標題模糊查詢
            if not results and main_title:
                # 提取關鍵詞（去除日期和特殊符號）
                import re
                keywords = re.sub(r'[0-9_/()年月日]', ' ', main_title)
                keywords = ' '.join([word for word in keywords.split() if len(word) > 1])
                
                if keywords:
                    # 用關鍵詞進行模糊查詢，優先選擇有 duration 和 published_date 的
                    query = """
                    SELECT e.episode_id, e.episode_title, e.duration, e.published_date, e.apple_episodes_ranking, e.created_at, e.languages, p.podcast_id, p.podcast_name, p.author, p.category, p.apple_rating as apple_rating
                    FROM episodes e
                    JOIN podcasts p ON e.podcast_id = p.podcast_id
                    WHERE p.podcast_id = %s AND (
                        e.episode_title ILIKE %s OR
                        e.episode_title ILIKE %s OR
                        e.episode_title ILIKE %s
                    )
                    ORDER BY 
                        CASE WHEN e.duration IS NOT NULL AND e.published_date IS NOT NULL THEN 0 ELSE 1 END,
                        e.published_date DESC
                    LIMIT 5
                    """
                    
                    # 嘗試多個關鍵詞組合
                    keyword_parts = keywords.split()[:3]  # 取前3個關鍵詞
                    search_terms = [
                        f'%{keywords}%',
                        f'%{keyword_parts[0]}%' if keyword_parts else '%',
                        f'%{keyword_parts[1]}%' if len(keyword_parts) > 1 else '%'
                    ]
                    
                    cursor.execute(query, (podcast_id, *search_terms))
                    results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            if results:
                # 優先選擇有完整資料的 episode
                for row in results:
                    episode_id, episode_title, duration, published_date, apple_episodes_ranking, created_at, \
                    languages, podcast_id, podcast_name, author, category, apple_rating = row
                    
                    # 如果這個 episode 有 duration 和 published_date，優先使用
                    if duration is not None and published_date is not None:
                        return {
                            'episode_id': episode_id,
                            'episode_title': episode_title,
                            'duration': duration,
                            'published_date': published_date,
                            'apple_episodes_ranking': apple_episodes_ranking,
                            'created_at': created_at,
                            'languages': languages,
                            'podcast_id': podcast_id,
                            'podcast_name': podcast_name,
                            'author': author,
                            'category': category,
                            'apple_rating': apple_rating
                        }
                
                # 如果沒有完整資料的，使用第一個結果
                row = results[0]
                episode_id, episode_title, duration, published_date, apple_episodes_ranking, created_at, \
                languages, podcast_id, podcast_name, author, category, apple_rating = row
                return {
                    'episode_id': episode_id,
                    'episode_title': episode_title,
                    'duration': duration,
                    'published_date': published_date,
                    'apple_episodes_ranking': apple_episodes_ranking,
                    'created_at': created_at,
                    'languages': languages,
                    'podcast_id': podcast_id,
                    'podcast_name': podcast_name,
                    'author': author,
                    'category': category,
                    'apple_rating': apple_rating
                }
            else:
                return None
        except Exception as e:
            logger.error(f"查詢 PostgreSQL episode 失敗: {str(e)}")
            return None
    
    def ensure_field_has_value(self, value: Any, field_name: str, default_value: Any, max_length: Optional[int] = None) -> Any:
        """確保欄位有值，如果沒有則使用預設值"""
        if value is None or value == '' or value == 'null' or value == 'None':
            return default_value
        
        # 處理 Decimal 類型
        if hasattr(value, '__class__') and value.__class__.__name__ == 'Decimal':
            value = float(value)
        
        # 特殊處理 published_date
        if field_name == 'published_date' and value is not None:
            if isinstance(value, str):
                return str(value)[:64]
            elif hasattr(value, 'isoformat'):
                return value.isoformat()[:64]
            else:
                return str(value)[:64]
        
        # 如果是字串且超過最大長度，截斷
        if isinstance(value, str) and max_length:
            return str(value)[:max_length]
        
        return value
    
    def process_json_file(self, file_path: Path, pg_episodes: Dict) -> Tuple[List[Dict], Dict]:
        """處理單一 JSON 檔案，修正為符合 Milvus 的格式"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 優化後的檔名解析
            podcast_id, episode_title, ep_match, main_title = self.extract_info_from_filename(file_path.name)
            
            if podcast_id is None:
                logger.warning(f"無法解析檔案名稱: {file_path.name}")
                return [], {}
            
            # 根據檔案名稱設定固定 category
            fixed_category = "unknown"
            if "podcast_1321" in file_path.name:
                fixed_category = "商業"
            elif "podcast_1304" in file_path.name:
                fixed_category = "教育"
            
            # 優化後的查詢
            pg_episode = self.find_postgresql_episode(podcast_id, ep_match, main_title)
            
            # 取得 podcast 基本資訊（即使找不到 episode）
            podcast_info = self.get_podcast_info(podcast_id)
            
            # 取得 podcast 統計資訊（用於 fallback）
            podcast_stats = self.get_podcast_stats(podcast_id)
            
            # 處理 chunks
            chunks = data.get('chunks', [])
            processed_chunks = []
            
            for i, chunk in enumerate(chunks):
                chunk_text = chunk.get('chunk_text', '')
                if not chunk_text or chunk_text.strip() == '':
                    chunk_text = '無內容'
                
                embedding = self.embedding_generator.generate_embedding(chunk_text)
                
                enhanced_tags = chunk.get('enhanced_tags', [])
                if isinstance(enhanced_tags, list):
                    tags_str = ','.join(enhanced_tags)
                else:
                    tags_str = str(enhanced_tags) if enhanced_tags else '無標籤'
                
                # 確保 tags 不超過 1024 字元
                if len(tags_str) > 1024:
                    tags_str = tags_str[:1021] + "..."
                
                if pg_episode:
                    # 有找到 episode，使用 episode 資料，但 category 用固定的
                    processed_chunk = {
                        'chunk_id': self.ensure_field_has_value(chunk.get('chunk_id', f"{pg_episode['episode_id']}_{i}"), 'chunk_id', f"{pg_episode['episode_id']}_{i}", 64),
                        'chunk_index': self.ensure_field_has_value(chunk.get('chunk_index', i), 'chunk_index', i),
                        'episode_id': self.ensure_field_has_value(pg_episode['episode_id'], 'episode_id', 0),
                        'podcast_id': self.ensure_field_has_value(pg_episode['podcast_id'], 'podcast_id', 0),
                        'podcast_name': self.ensure_field_has_value(pg_episode['podcast_name'], 'podcast_name', '未知播客', 255),
                        'author': self.ensure_field_has_value(pg_episode['author'], 'author', '未知作者', 255),
                        'category': self.ensure_field_has_value(fixed_category, 'category', '未知分類', 64),
                        'episode_title': self.ensure_field_has_value(pg_episode['episode_title'], 'episode_title', '未知標題', 255),
                        'duration': self.ensure_field_has_value(pg_episode['duration'], 'duration', '未知時長', 255),
                        'published_date': self.ensure_field_has_value(pg_episode['published_date'], 'published_date', '未知日期', 64),
                        'apple_rating': self.ensure_field_has_value(pg_episode['apple_rating'], 'apple_rating', 0),
                        'chunk_text': self.ensure_field_has_value(chunk_text, 'chunk_text', '無內容', 1024),
                        'embedding': embedding,
                        'language': self.ensure_field_has_value(pg_episode['languages'], 'language', 'zh', 16),
                        'created_at': self.ensure_field_has_value(pg_episode['created_at'].isoformat() if pg_episode['created_at'] else datetime.now().isoformat(), 'created_at', datetime.now().isoformat(), 64),
                        'source_model': 'bge-m3',
                        'tags': self.ensure_field_has_value(tags_str, 'tags', '無標籤', 1024)
                    }
                else:
                    # 沒找到 episode，使用 podcast 基本資訊和統計資訊
                    if podcast_info:
                        # 使用 podcast 統計資訊作為 fallback
                        fallback_duration = podcast_stats['avg_duration'] if podcast_stats and podcast_stats['avg_duration'] else '未知時長'
                        fallback_date = str(podcast_stats['earliest_date']) if podcast_stats and podcast_stats['earliest_date'] else '未知日期'
                        
                        processed_chunk = {
                            'chunk_id': self.ensure_field_has_value(chunk.get('chunk_id', f"unknown_{i}"), 'chunk_id', f"unknown_{i}", 64),
                            'chunk_index': self.ensure_field_has_value(chunk.get('chunk_index', i), 'chunk_index', i),
                            'episode_id': 0,  # INT64 (unknown)
                            'podcast_id': self.ensure_field_has_value(podcast_id, 'podcast_id', 0),
                            'podcast_name': self.ensure_field_has_value(podcast_info['podcast_name'], 'podcast_name', '未知播客', 255),
                            'author': self.ensure_field_has_value(podcast_info['author'], 'author', '未知作者', 255),
                            'category': self.ensure_field_has_value(fixed_category, 'category', '未知分類', 64),
                            'episode_title': self.ensure_field_has_value(main_title, 'episode_title', '未知標題', 255),
                            'duration': self.ensure_field_has_value(fallback_duration, 'duration', '未知時長', 255),
                            'published_date': self.ensure_field_has_value(fallback_date, 'published_date', '未知日期', 64),
                            'apple_rating': self.ensure_field_has_value(podcast_info['apple_rating'], 'apple_rating', 0),
                            'chunk_text': self.ensure_field_has_value(chunk_text, 'chunk_text', '無內容', 1024),
                            'embedding': embedding,
                            'language': 'zh',
                            'created_at': datetime.now().isoformat(),
                            'source_model': 'bge-m3',
                            'tags': self.ensure_field_has_value(tags_str, 'tags', '無標籤', 1024)
                        }
                    else:
                        # 連 podcast 資訊都找不到，使用完全 fallback
                        processed_chunk = {
                            'chunk_id': self.ensure_field_has_value(chunk.get('chunk_id', f"unknown_{i}"), 'chunk_id', f"unknown_{i}", 64),
                            'chunk_index': self.ensure_field_has_value(chunk.get('chunk_index', i), 'chunk_index', i),
                            'episode_id': 0,  # INT64 (unknown)
                            'podcast_id': self.ensure_field_has_value(podcast_id, 'podcast_id', 0),
                            'podcast_name': '未知播客',
                            'author': '未知作者',
                            'category': self.ensure_field_has_value(fixed_category, 'category', '未知分類', 64),
                            'episode_title': self.ensure_field_has_value(main_title, 'episode_title', '未知標題', 255),
                            'duration': '未知時長',
                            'published_date': '未知日期',
                            'apple_rating': 0,
                            'chunk_text': self.ensure_field_has_value(chunk_text, 'chunk_text', '無內容', 1024),
                            'embedding': embedding,
                            'language': 'zh',
                            'created_at': datetime.now().isoformat(),
                            'source_model': 'bge-m3',
                            'tags': self.ensure_field_has_value(tags_str, 'tags', '無標籤', 1024)
                        }
                
                processed_chunks.append(processed_chunk)
            
            # 建立修正後的 JSON 結構
            fixed_data = {
                'filename': file_path.name,
                'episode_id': str(pg_episode['episode_id']) if pg_episode else 'unknown',
                'collection_name': f"RSS_{podcast_id}" if podcast_id else 'unknown',
                'total_chunks': len(processed_chunks),
                'chunks': processed_chunks,
                'fixed_at': datetime.now().isoformat(),
                'source_model': 'bge-m3'
            }
            
            logger.info(f"處理檔案 {file_path.name}: {len(processed_chunks)} 個 chunks")
            return processed_chunks, fixed_data
            
        except Exception as e:
            logger.error(f"處理檔案 {file_path} 失敗: {str(e)}")
            return [], {}
    
    def save_fixed_json(self, fixed_data: Dict, original_file_path: Path):
        """儲存修正後的 JSON 檔案到 stage4_embedding_prep"""
        try:
            # 建立對應的輸出目錄
            output_dir = self.output_path / original_file_path.parent.name
            output_dir.mkdir(exist_ok=True)
            
            # 儲存修正後的檔案
            output_file = output_dir / original_file_path.name
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(fixed_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"儲存修正後的檔案到 stage4_embedding_prep: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"儲存修正後的檔案失敗: {str(e)}")
            return False
    
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
                # 確保資料類型正確
                insert_data['chunk_id'].append(str(chunk.get('chunk_id', ''))[:64])
                insert_data['chunk_index'].append(int(chunk.get('chunk_index', 0)))
                insert_data['episode_id'].append(int(chunk.get('episode_id', 0)))
                insert_data['podcast_id'].append(int(chunk.get('podcast_id', 0)))
                insert_data['podcast_name'].append(str(chunk.get('podcast_name', ''))[:255])
                insert_data['author'].append(str(chunk.get('author', ''))[:255])
                insert_data['category'].append(str(chunk.get('category', ''))[:64])
                insert_data['episode_title'].append(str(chunk.get('episode_title', ''))[:255])
                insert_data['duration'].append(str(chunk.get('duration', ''))[:255])
                insert_data['published_date'].append(str(chunk.get('published_date', ''))[:64])
                insert_data['apple_rating'].append(int(chunk.get('apple_rating', 0)))
                insert_data['chunk_text'].append(str(chunk.get('chunk_text', ''))[:1024])
                
                # 確保 embedding 是正確的格式
                embedding = chunk.get('embedding', [])
                if isinstance(embedding, list) and len(embedding) == 1024:
                    insert_data['embedding'].append(embedding)
                else:
                    # 如果沒有正確的 embedding，使用零向量
                    insert_data['embedding'].append([0.0] * 1024)
                
                insert_data['language'].append(str(chunk.get('language', ''))[:16])
                insert_data['created_at'].append(str(chunk.get('created_at', ''))[:64])
                insert_data['source_model'].append(str(chunk.get('source_model', ''))[:64])
                insert_data['tags'].append(str(chunk.get('tags', ''))[:1024])
            
            # 插入資料
            collection.insert(insert_data)
            collection.flush()
            
            logger.info(f"成功插入 {len(processed_chunks)} 個 chunks 到 Milvus")
            return True
            
        except Exception as e:
            logger.error(f"更新 Milvus 集合失敗: {str(e)}")
            return False
    
    def process_all_files(self, save_fixed_json: bool = True, update_milvus: bool = True):
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
        
        total_files = 0
        processed_files = 0
        
        for rss_dir in rss_dirs:
            logger.info(f"處理目錄: {rss_dir.name}")
            json_files = list(rss_dir.glob("*.json"))
            total_files += len(json_files)
            
            for json_file in json_files:
                processed_chunks, fixed_data = self.process_json_file(json_file, pg_episodes)
                
                if processed_chunks and fixed_data:
                    all_processed_chunks.extend(processed_chunks)
                    processed_files += 1
                    
                    # 儲存修正後的 JSON 檔案
                    if save_fixed_json:
                        self.save_fixed_json(fixed_data, json_file)
        
        logger.info(f"總共處理了 {processed_files}/{total_files} 個檔案，{len(all_processed_chunks)} 個 chunks")
        
        # 更新 Milvus 集合
        if update_milvus and all_processed_chunks:
            success = self.update_milvus_collection(all_processed_chunks)
            if success:
                logger.info("✅ 成功更新 Milvus 集合")
            else:
                logger.error("❌ 更新 Milvus 集合失敗")
        elif not all_processed_chunks:
            logger.warning("沒有找到可處理的 chunks")

def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='修正 stage3_tagging 中的所有 JSON 檔案')
    parser.add_argument('--no-save-json', action='store_true', help='不儲存修正後的 JSON 檔案')
    parser.add_argument('--no-update-milvus', action='store_true', help='不更新 Milvus 集合')
    
    args = parser.parse_args()
    
    fixer = Stage3TaggingFixer()
    fixer.process_all_files(
        save_fixed_json=not args.no_save_json,
        update_milvus=not args.no_update_milvus
    )

if __name__ == "__main__":
    main() 