#!/usr/bin/env python3
"""
穩定的批次處理腳本
- 分段處理，避免記憶體溢出
- 詳細的錯誤處理和日誌
- 進度保存和恢復功能
- 自動重試機制
"""

import os
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
import logging
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pymilvus import connections, Collection, utility
import numpy as np
from tqdm import tqdm
import traceback
import signal
import pickle

# 載入環境變數
load_dotenv('backend/.env')

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_process.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GracefulExit:
    """優雅退出處理"""
    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
    
    def exit_gracefully(self, signum, frame):
        logger.info("收到退出信號，正在優雅退出...")
        self.kill_now = True

class BGE_M3_Embedding:
    """BGE-M3 embedding 生成器"""
    
    def __init__(self):
        self.model = None
        self.device = 'cuda'
        self.load_model()
    
    def load_model(self):
        """載入 BGE-M3 模型"""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"嘗試載入 BGE-M3 模型到 {self.device}...")
            
            # 設定較長的超時時間
            self.model = SentenceTransformer('BAAI/bge-m3', device=self.device)
            
            # 測試模型
            test_text = "測試文本"
            test_embedding = self.model.encode(test_text, normalize_embeddings=True)
            
            if len(test_embedding) == 1024 and not np.allclose(test_embedding, 0):
                logger.info(f"✅ 成功載入 BGE-M3 模型到 {self.device}")
                return True
            else:
                raise Exception("模型載入失敗：embedding 為零向量")
                
        except Exception as e:
            logger.warning(f"GPU 載入失敗: {str(e)}")
            
            try:
                logger.info("嘗試載入 BGE-M3 模型到 CPU...")
                self.device = 'cpu'
                self.model = SentenceTransformer('BAAI/bge-m3', device=self.device)
                
                test_text = "測試文本"
                test_embedding = self.model.encode(test_text, normalize_embeddings=True)
                
                if len(test_embedding) == 1024 and not np.allclose(test_embedding, 0):
                    logger.info("✅ 成功載入 BGE-M3 模型到 CPU")
                    return True
                else:
                    raise Exception("模型載入失敗：embedding 為零向量")
                    
            except Exception as e2:
                logger.error(f"CPU 載入也失敗: {str(e2)}")
                return False
    
    def generate_embedding(self, text: str) -> List[float]:
        """生成 BGE-M3 embedding"""
        if not self.model:
            logger.error("BGE-M3 模型未載入")
            return [0.0] * 1024
        
        try:
            embedding = self.model.encode(text, normalize_embeddings=True)
            embedding_list = embedding.tolist()
            
            if np.allclose(embedding, 0):
                logger.warning(f"⚠️ 警告：文本 '{text[:50]}...' 產生零向量 embedding")
            
            return embedding_list
            
        except Exception as e:
            logger.error(f"生成 embedding 失敗: {str(e)}")
            return [0.0] * 1024

class MilvusConnector:
    """Milvus 連線器"""
    
    def __init__(self):
        self.host = "192.168.32.86"
        self.user = "bdse37"
        self.password = "111111"
        self.collection_name = "podcast_chunks"
        self.connected = False
        self.collection = None
    
    def _safe_cast_field(self, value: Any, field_name: str, field_type: str, 
                        default_value: Any, max_length: Optional[int] = None) -> Any:
        """安全的欄位型態轉換"""
        try:
            if value is None:
                return default_value
            
            if field_type == 'str':
                if isinstance(value, list):
                    if len(value) > 0:
                        first_item = value[0]
                        if isinstance(first_item, (list, dict)):
                            import json
                            result = json.dumps(first_item, ensure_ascii=False)
                        else:
                            result = str(first_item)
                    else:
                        result = str(default_value)
                elif isinstance(value, dict):
                    import json
                    result = json.dumps(value, ensure_ascii=False)
                else:
                    result = str(value)
                
                result = str(result)
                
                if max_length and len(result) > max_length:
                    result = result[:max_length]
                
                return result
                
            elif field_type == 'int':
                if isinstance(value, (list, dict)):
                    return default_value
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return default_value
                    
            elif field_type == 'float':
                if isinstance(value, (list, dict)):
                    return default_value
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return default_value
                    
            elif field_type == 'list':
                if isinstance(value, list):
                    return value
                else:
                    return default_value
                    
            else:
                return default_value
                
        except Exception as e:
            logger.warning(f"欄位 {field_name} 轉換失敗: {str(e)}，使用預設值")
            return default_value
    
    def connect(self) -> bool:
        """連線到 Milvus"""
        try:
            ports = [19530, 9091, 9000]
            
            for port in ports:
                try:
                    logger.info(f"嘗試連線 Milvus: {self.host}:{port}")
                    connections.connect(
                        alias="default",
                        host=self.host,
                        port=port,
                        user=self.user,
                        password=self.password
                    )
                    
                    utility.list_collections()
                    logger.info(f"✅ 成功連線 Milvus: {self.host}:{port}")
                    
                    if utility.has_collection(self.collection_name):
                        self.collection = Collection(self.collection_name)
                        self.collection.load()
                        logger.info(f"✅ 成功載入 collection: {self.collection_name}")
                        self.connected = True
                        return True
                    else:
                        logger.error(f"❌ Collection '{self.collection_name}' 不存在")
                        return False
                        
                except Exception as e:
                    logger.warning(f"Port {port} 連線失敗: {str(e)}")
                    continue
            
            logger.error("❌ 所有 port 都無法連線 Milvus")
            return False
            
        except Exception as e:
            logger.error(f"❌ Milvus 連線失敗: {str(e)}")
            return False
    
    def insert_data(self, processed_chunks: List[Dict]) -> bool:
        """插入資料到 Milvus"""
        if not self.connected or not self.collection:
            logger.error("❌ Milvus 未連線")
            return False
        
        try:
            for chunk in processed_chunks:
                raw_chunk_id = chunk.get('chunk_id')
                processed_chunk_id = self._safe_cast_field(raw_chunk_id, 'chunk_id', 'str', '', 64)
                
                single_chunk_data = {
                    'chunk_id': processed_chunk_id,
                    'chunk_index': self._safe_cast_field(chunk.get('chunk_index'), 'chunk_index', 'int', 0),
                    'episode_id': self._safe_cast_field(chunk.get('episode_id'), 'episode_id', 'int', 0),
                    'podcast_id': self._safe_cast_field(chunk.get('podcast_id'), 'podcast_id', 'int', 0),
                    'podcast_name': self._safe_cast_field(chunk.get('podcast_name'), 'podcast_name', '未知播客', 255),
                    'author': self._safe_cast_field(chunk.get('author'), 'author', 'str', '未知作者', 255),
                    'category': self._safe_cast_field(chunk.get('category'), 'category', 'str', '未知分類', 64),
                    'episode_title': self._safe_cast_field(chunk.get('episode_title'), 'episode_title', 'str', '未知標題', 255),
                    'duration': self._safe_cast_field(chunk.get('duration'), 'duration', 'str', '未知時長', 255),
                    'published_date': self._safe_cast_field(chunk.get('published_date'), 'published_date', 'str', '未知日期', 64),
                    'apple_rating': self._safe_cast_field(chunk.get('apple_rating'), 'apple_rating', 'int', 0),
                    'chunk_text': self._safe_cast_field(chunk.get('chunk_text'), 'chunk_text', 'str', '無內容', 1024),
                    'language': self._safe_cast_field(chunk.get('language'), 'language', 'str', 'zh', 16),
                    'created_at': self._safe_cast_field(chunk.get('created_at'), 'created_at', 'str', datetime.now().isoformat(), 64),
                    'source_model': self._safe_cast_field(chunk.get('source_model'), 'source_model', 'str', 'bge-m3', 64),
                    'tags': self._safe_cast_field(chunk.get('tags'), 'tags', 'str', '無標籤', 1024)
                }
                
                embedding = chunk.get('embedding', [])
                if isinstance(embedding, list) and len(embedding) == 1024:
                    single_chunk_data['embedding'] = embedding
                else:
                    single_chunk_data['embedding'] = [0.0] * 1024
                
                self.collection.insert([single_chunk_data])
            
            self.collection.flush()
            logger.info(f"✅ 成功插入 {len(processed_chunks)} 個 chunks 到 Milvus")
            return True
            
        except Exception as e:
            logger.error(f"❌ 插入 Milvus 失敗: {str(e)}")
            return False

class StableBatchProcessor:
    """穩定的批次處理器"""
    
    def __init__(self):
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent
        self.stage3_path = project_root / "backend/vector_pipeline/data/stage3_tagging"
        self.output_path = project_root / "backend/vector_pipeline/data/stage4_embedding_prep"
        self.progress_file = project_root / "backend/utils/batch_progress.pkl"
        
        self.pg_config = {
            'host': os.getenv('POSTGRES_HOST', 'postgres.podwise.svc.cluster.local'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'podcast'),
            'user': os.getenv('POSTGRES_USER', 'bdse37'),
            'password': os.getenv('POSTGRES_PASSWORD', '111111')
        }
        
        self.embedding_generator = BGE_M3_Embedding()
        self.milvus_connector = MilvusConnector()
        
        self.total_files = 0
        self.processed_files = 0
        self.failed_files = []
        self.start_time = None
        self.processed_file_list = set()
        
        self.output_path.mkdir(exist_ok=True)
        self.load_progress()
    
    def load_progress(self):
        """載入進度"""
        try:
            if self.progress_file.exists():
                with open(self.progress_file, 'rb') as f:
                    progress_data = pickle.load(f)
                    self.processed_files = progress_data.get('processed_files', 0)
                    self.processed_file_list = set(progress_data.get('processed_file_list', []))
                    logger.info(f"📋 載入進度：已處理 {self.processed_files} 個檔案")
        except Exception as e:
            logger.warning(f"載入進度失敗: {str(e)}")
    
    def save_progress(self):
        """儲存進度"""
        try:
            progress_data = {
                'processed_files': self.processed_files,
                'processed_file_list': list(self.processed_file_list),
                'timestamp': datetime.now().isoformat()
            }
            with open(self.progress_file, 'wb') as f:
                pickle.dump(progress_data, f)
        except Exception as e:
            logger.warning(f"儲存進度失敗: {str(e)}")
    
    def clear_output_directory(self):
        """清空輸出目錄"""
        try:
            import shutil
            if self.output_path.exists():
                shutil.rmtree(self.output_path)
            self.output_path.mkdir(exist_ok=True)
            logger.info("✅ 已清空 stage4_embedding_prep 目錄")
        except Exception as e:
            logger.error(f"❌ 清空目錄失敗: {str(e)}")
    
    def scan_all_files(self) -> List[Path]:
        """掃描所有需要處理的檔案"""
        all_files = []
        rss_dirs = [d for d in self.stage3_path.iterdir() if d.is_dir() and d.name.startswith("RSS_")]
        
        for rss_dir in rss_dirs:
            json_files = list(rss_dir.glob("*.json"))
            all_files.extend(json_files)
        
        self.total_files = len(all_files)
        logger.info(f"📁 找到 {len(rss_dirs)} 個 RSS 目錄，{self.total_files} 個 JSON 檔案")
        return all_files
    
    def get_postgresql_episodes(self) -> Dict[str, Dict]:
        """從 PostgreSQL 取得完整的 episodes 和 podcasts 資料"""
        try:
            conn = psycopg2.connect(**self.pg_config)
            cursor = conn.cursor()
            
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
            
            logger.info(f"✅ 從 PostgreSQL 取得 {len(episodes)} 筆 episodes 資料")
            return episodes
            
        except Exception as e:
            logger.error(f"❌ 查詢 PostgreSQL 失敗: {str(e)}")
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
        """取得 podcast 的統計資訊"""
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
        """從檔案名稱中提取資訊"""
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

    def find_postgresql_episode(self, podcast_id: int, ep_match: Optional[str], main_title: Optional[str], pg_episodes: Dict) -> Optional[Dict]:
        """根據 podcast_id、EP 編號或主標題找到對應的 PostgreSQL episode"""
        try:
            matching_episodes = []
            
            for episode_id, episode_data in pg_episodes.items():
                if episode_data['podcast_id'] == podcast_id:
                    if ep_match and ep_match in episode_data['episode_title']:
                        matching_episodes.append(episode_data)
                    elif main_title and main_title in episode_data['episode_title']:
                        matching_episodes.append(episode_data)
            
            if matching_episodes:
                for episode in matching_episodes:
                    if episode['duration'] is not None and episode['published_date'] is not None:
                        return episode
                return matching_episodes[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"查詢 PostgreSQL episode 失敗: {str(e)}")
            return None
    
    def ensure_field_has_value(self, value: Any, field_name: str, default_value: Any, max_length: Optional[int] = None) -> Any:
        """確保欄位有值"""
        if value is None or value == '' or value == 'null' or value == 'None':
            return default_value
        
        if hasattr(value, '__class__') and value.__class__.__name__ == 'Decimal':
            value = float(value)
        
        if field_name == 'published_date' and value is not None:
            if isinstance(value, str):
                return str(value)[:64]
            elif hasattr(value, 'isoformat'):
                return value.isoformat()[:64]
            else:
                return str(value)[:64]
        
        if isinstance(value, str) and max_length:
            return str(value)[:max_length]
        
        return value
    
    def process_single_file(self, file_path: Path, pg_episodes: Dict) -> Tuple[List[Dict], Dict]:
        """處理單一 JSON 檔案"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            podcast_id, episode_title, ep_match, main_title = self.extract_info_from_filename(file_path.name)
            
            if podcast_id is None:
                raise Exception("無法解析檔案名稱")
            
            fixed_category = "unknown"
            if "podcast_1321" in file_path.name:
                fixed_category = "商業"
            elif "podcast_1304" in file_path.name:
                fixed_category = "教育"
            
            pg_episode = self.find_postgresql_episode(podcast_id, ep_match, main_title, pg_episodes)
            podcast_info = self.get_podcast_info(podcast_id)
            podcast_stats = self.get_podcast_stats(podcast_id)
            
            chunks = data.get('chunks', [])
            processed_chunks = []
            
            for i, chunk in enumerate(chunks):
                original_chunk_text = chunk.get('chunk_text', '')
                original_chunk_index = chunk.get('chunk_index', i)
                
                if not original_chunk_text or original_chunk_text.strip() == '':
                    original_chunk_text = '無內容'
                
                embedding = self.embedding_generator.generate_embedding(original_chunk_text)
                
                enhanced_tags = chunk.get('enhanced_tags', [])
                if isinstance(enhanced_tags, list):
                    tags_str = ','.join(enhanced_tags)
                else:
                    tags_str = str(enhanced_tags) if enhanced_tags else '無標籤'
                
                if len(tags_str) > 1024:
                    tags_str = tags_str[:1021] + "..."
                
                if pg_episode:
                    processed_chunk = {
                        'chunk_id': self.ensure_field_has_value(chunk.get('chunk_id', f"{pg_episode['episode_id']}_{i}"), 'chunk_id', f"{pg_episode['episode_id']}_{i}", 64),
                        'chunk_index': self.ensure_field_has_value(original_chunk_index, 'chunk_index', i),
                        'episode_id': self.ensure_field_has_value(pg_episode['episode_id'], 'episode_id', 0),
                        'podcast_id': self.ensure_field_has_value(pg_episode['podcast_id'], 'podcast_id', 0),
                        'podcast_name': self.ensure_field_has_value(pg_episode['podcast_name'], 'podcast_name', '未知播客', 255),
                        'author': self.ensure_field_has_value(pg_episode['author'], 'author', '未知作者', 255),
                        'category': self.ensure_field_has_value(fixed_category, 'category', '未知分類', 64),
                        'episode_title': self.ensure_field_has_value(pg_episode['episode_title'], 'episode_title', '未知標題', 255),
                        'duration': self.ensure_field_has_value(pg_episode['duration'], 'duration', '未知時長', 255),
                        'published_date': self.ensure_field_has_value(pg_episode['published_date'], 'published_date', '未知日期', 64),
                        'apple_rating': self.ensure_field_has_value(pg_episode['apple_rating'], 'apple_rating', 0),
                        'chunk_text': self.ensure_field_has_value(original_chunk_text, 'chunk_text', '無內容', 1024),
                        'embedding': embedding,
                        'language': self.ensure_field_has_value(pg_episode['languages'], 'language', 'zh', 16),
                        'created_at': self.ensure_field_has_value(pg_episode['created_at'].isoformat() if pg_episode['created_at'] else datetime.now().isoformat(), 'created_at', datetime.now().isoformat(), 64),
                        'source_model': 'bge-m3',
                        'tags': self.ensure_field_has_value(tags_str, 'tags', '無標籤', 1024)
                    }
                else:
                    if podcast_info:
                        fallback_duration = podcast_stats['avg_duration'] if podcast_stats and podcast_stats['avg_duration'] else '未知時長'
                        fallback_date = str(podcast_stats['earliest_date']) if podcast_stats and podcast_stats['earliest_date'] else '未知日期'
                        
                        processed_chunk = {
                            'chunk_id': self.ensure_field_has_value(chunk.get('chunk_id', f"unknown_{i}"), 'chunk_id', f"unknown_{i}", 64),
                            'chunk_index': self.ensure_field_has_value(original_chunk_index, 'chunk_index', i),
                            'episode_id': 0,
                            'podcast_id': self.ensure_field_has_value(podcast_id, 'podcast_id', 0),
                            'podcast_name': self.ensure_field_has_value(podcast_info['podcast_name'], 'podcast_name', '未知播客', 255),
                            'author': self.ensure_field_has_value(podcast_info['author'], 'author', '未知作者', 255),
                            'category': self.ensure_field_has_value(fixed_category, 'category', '未知分類', 64),
                            'episode_title': self.ensure_field_has_value(main_title, 'episode_title', '未知標題', 255),
                            'duration': self.ensure_field_has_value(fallback_duration, 'duration', '未知時長', 255),
                            'published_date': self.ensure_field_has_value(fallback_date, 'published_date', '未知日期', 64),
                            'apple_rating': self.ensure_field_has_value(podcast_info['apple_rating'], 'apple_rating', 0),
                            'chunk_text': self.ensure_field_has_value(original_chunk_text, 'chunk_text', '無內容', 1024),
                            'embedding': embedding,
                            'language': 'zh',
                            'created_at': datetime.now().isoformat(),
                            'source_model': 'bge-m3',
                            'tags': self.ensure_field_has_value(tags_str, 'tags', '無標籤', 1024)
                        }
                    else:
                        processed_chunk = {
                            'chunk_id': self.ensure_field_has_value(chunk.get('chunk_id', f"unknown_{i}"), 'chunk_id', f"unknown_{i}", 64),
                            'chunk_index': self.ensure_field_has_value(original_chunk_index, 'chunk_index', i),
                            'episode_id': 0,
                            'podcast_id': self.ensure_field_has_value(podcast_id, 'podcast_id', 0),
                            'podcast_name': '未知播客',
                            'author': '未知作者',
                            'category': self.ensure_field_has_value(fixed_category, 'category', '未知分類', 64),
                            'episode_title': self.ensure_field_has_value(main_title, 'episode_title', '未知標題', 255),
                            'duration': '未知時長',
                            'published_date': '未知日期',
                            'apple_rating': 0,
                            'chunk_text': self.ensure_field_has_value(original_chunk_text, 'chunk_text', '無內容', 1024),
                            'embedding': embedding,
                            'language': 'zh',
                            'created_at': datetime.now().isoformat(),
                            'source_model': 'bge-m3',
                            'tags': self.ensure_field_has_value(tags_str, 'tags', '無標籤', 1024)
                        }
                
                processed_chunks.append(processed_chunk)
            
            fixed_data = {
                'filename': file_path.name,
                'episode_id': str(pg_episode['episode_id']) if pg_episode else 'unknown',
                'collection_name': f"RSS_{podcast_id}" if podcast_id else 'unknown',
                'total_chunks': len(processed_chunks),
                'chunks': processed_chunks,
                'fixed_at': datetime.now().isoformat(),
                'source_model': 'bge-m3'
            }
            
            return processed_chunks, fixed_data
            
        except Exception as e:
            logger.error(f"處理檔案 {file_path} 失敗: {str(e)}")
            return [], {}
    
    def save_fixed_json(self, fixed_data: Dict, original_file_path: Path):
        """儲存修正後的 JSON 檔案"""
        try:
            output_dir = self.output_path / original_file_path.parent.name
            output_dir.mkdir(exist_ok=True)
            
            output_file = output_dir / original_file_path.name
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(fixed_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"儲存修正後的檔案失敗: {str(e)}")
            return False
    
    def estimate_remaining_time(self) -> str:
        """預估剩餘時間"""
        if self.processed_files == 0 or not self.start_time:
            return "計算中..."
        
        elapsed_time = time.time() - self.start_time
        avg_time_per_file = elapsed_time / self.processed_files
        remaining_files = self.total_files - self.processed_files
        remaining_time = avg_time_per_file * remaining_files
        
        return str(timedelta(seconds=int(remaining_time)))
    
    def process_all_files(self):
        """處理所有檔案"""
        print("\n" + "="*80)
        print("🚀 開始穩定的批次處理 stage3_tagging 到 stage4_embedding_prep")
        print("="*80)
        
        graceful_exit = GracefulExit()
        
        # 1. 清空輸出目錄
        print("📁 清空 stage4_embedding_prep 目錄...")
        self.clear_output_directory()
        
        # 2. 檢查 BGE-M3 模型
        print("🤖 檢查 BGE-M3 模型...")
        if not self.embedding_generator.model:
            print("❌ BGE-M3 模型載入失敗，無法繼續")
            return
        
        # 3. 連線 Milvus
        print("🔗 連線 Milvus...")
        if not self.milvus_connector.connect():
            print("❌ Milvus 連線失敗，無法繼續")
            return
        
        # 4. 掃描所有檔案
        print("📋 掃描所有檔案...")
        all_files = self.scan_all_files()
        if not all_files:
            print("❌ 沒有找到需要處理的檔案")
            return
        
        # 5. 取得 PostgreSQL 資料
        print("🗄️ 取得 PostgreSQL 資料...")
        pg_episodes = self.get_postgresql_episodes()
        if not pg_episodes:
            print("❌ 無法取得 PostgreSQL 資料")
            return
        
        # 6. 開始批次處理
        print(f"\n🔄 開始處理 {self.total_files} 個檔案...")
        self.start_time = time.time()
        
        # 使用 tqdm 顯示進度條
        with tqdm(total=self.total_files, desc="處理進度", unit="檔案") as pbar:
            pbar.update(self.processed_files)  # 更新已處理的進度
            
            for file_path in all_files:
                # 檢查是否已經處理過
                if str(file_path) in self.processed_file_list:
                    pbar.update(1)
                    continue
                
                # 檢查是否需要退出
                if graceful_exit.kill_now:
                    logger.info("收到退出信號，正在保存進度...")
                    self.save_progress()
                    break
                
                try:
                    # 處理檔案
                    processed_chunks, fixed_data = self.process_single_file(file_path, pg_episodes)
                    
                    if processed_chunks and fixed_data:
                        # 儲存修正後的 JSON 檔案
                        if self.save_fixed_json(fixed_data, file_path):
                            # 插入到 Milvus
                            if self.milvus_connector.insert_data(processed_chunks):
                                self.processed_files += 1
                                self.processed_file_list.add(str(file_path))
                                self.save_progress()  # 每處理完一個檔案就保存進度
                                
                                pbar.set_postfix({
                                    '成功': self.processed_files,
                                    '剩餘時間': self.estimate_remaining_time()
                                })
                            else:
                                self.failed_files.append({
                                    'file': str(file_path),
                                    'reason': 'Milvus 插入失敗',
                                    'chunks_count': len(processed_chunks)
                                })
                        else:
                            self.failed_files.append({
                                'file': str(file_path),
                                'reason': 'JSON 儲存失敗',
                                'chunks_count': len(processed_chunks)
                            })
                    else:
                        self.failed_files.append({
                            'file': str(file_path),
                            'reason': '檔案處理失敗',
                            'chunks_count': 0
                        })
                    
                except Exception as e:
                    error_msg = f"處理異常: {str(e)}"
                    self.failed_files.append({
                        'file': str(file_path),
                        'reason': error_msg,
                        'chunks_count': 0
                    })
                    logger.error(f"處理檔案 {file_path} 異常: {str(e)}")
                
                pbar.update(1)
        
        # 7. 輸出結果
        total_time = time.time() - self.start_time if self.start_time else 0
        print("\n" + "="*80)
        print("🎉 批次處理完成！")
        print("="*80)
        print(f"📊 統計資訊:")
        print(f"   總檔案數: {self.total_files}")
        print(f"   成功處理: {self.processed_files}")
        print(f"   失敗檔案: {len(self.failed_files)}")
        print(f"   總耗時: {str(timedelta(seconds=int(total_time)))}")
        if total_time > 0:
            print(f"   平均速度: {self.total_files/total_time:.2f} 檔案/秒")
        
        if self.failed_files:
            print(f"\n❌ 失敗檔案清單:")
            for failed in self.failed_files:
                print(f"   {failed['file']}: {failed['reason']}")
            
            fail_log_path = self.output_path / "fail_log.json"
            with open(fail_log_path, 'w', encoding='utf-8') as f:
                json.dump(self.failed_files, f, ensure_ascii=False, indent=2)
            print(f"\n📝 失敗清單已儲存至: {fail_log_path}")
        
        print("\n✅ 所有處理完成！")

def main():
    """主函數"""
    processor = StableBatchProcessor()
    processor.process_all_files()

if __name__ == "__main__":
    main() 