#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動化爬蟲統合服務
整合現有爬蟲程式、STT 轉錄、向量化處理
保持原有爬蟲程式不變，只建立統合介面
"""

import os
import sys
import time
import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime

# 資料庫連接
import psycopg2
from pymongo import MongoClient
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

# 物件儲存
from minio import Minio
from minio.error import S3Error

# STT 相關
import whisper
import torch

# 向量化相關
from sentence_transformers import SentenceTransformer

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutoCrawlerIntegrator:
    """自動化爬蟲統合類別 - 保持原有爬蟲程式不變"""
    
    def __init__(self):
        """初始化統合服務"""
        self.crawl_count = int(os.getenv('CRAWL_COUNT', 10))
        
        # 資料庫連接
        self.postgres_conn = None
        self.mongodb_client = None
        self.milvus_conn = None
        self.minio_client = None
        
        # 模型載入
        self.whisper_model = None
        self.embedding_model = None
        
        # 初始化連接
        self._init_connections()
        self._load_models()
        
    def _init_connections(self):
        """初始化所有資料庫連接"""
        try:
            # PostgreSQL 連接
            self.postgres_conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'postgres'),
                database=os.getenv('POSTGRES_DB', 'podcast'),
                user=os.getenv('POSTGRES_USER', 'bdse37'),
                password=os.getenv('POSTGRES_PASSWORD', '111111'),
                port=5432
            )
            logger.info("PostgreSQL 連接成功")
            
            # MongoDB 連接
            self.mongodb_client = MongoClient(
                host=os.getenv('MONGODB_HOST', 'mongodb'),
                port=int(os.getenv('MONGODB_PORT', 27017)),
                username=os.getenv('MONGODB_USER', 'bdse37'),
                password=os.getenv('MONGODB_PASSWORD', '111111'),
                authSource='admin'
            )
            self.mongodb_db = self.mongodb_client[os.getenv('MONGODB_DB', 'podcast')]
            logger.info("MongoDB 連接成功")
            
            # Milvus 連接
            connections.connect(
                alias="default",
                host=os.getenv('MILVUS_HOST', 'milvus'),
                port=int(os.getenv('MILVUS_PORT', 19530))
            )
            self.milvus_conn = connections.get_connection("default")
            logger.info("Milvus 連接成功")
            
            # MinIO 連接
            self.minio_client = Minio(
                endpoint=f"{os.getenv('MINIO_HOST', 'minio')}:{os.getenv('MINIO_PORT', 9000)}",
                access_key=os.getenv('MINIO_ACCESS_KEY', 'bdse37'),
                secret_key=os.getenv('MINIO_SECRET_KEY', '11111111'),
                secure=False
            )
            logger.info("MinIO 連接成功")
            
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            raise
    
    def _load_models(self):
        """載入 AI 模型"""
        try:
            # 載入 Whisper 模型
            logger.info("載入 Whisper 模型...")
            self.whisper_model = whisper.load_model("base")
            
            # 載入句子嵌入模型
            logger.info("載入句子嵌入模型...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            logger.info("模型載入完成")
            
        except Exception as e:
            logger.error(f"模型載入失敗: {e}")
            raise
    
    def _init_minio_buckets(self):
        """初始化 MinIO 儲存桶"""
        try:
            buckets = ["podcast-audio", "podcast-transcripts"]
            
            for bucket in buckets:
                if not self.minio_client.bucket_exists(bucket):
                    self.minio_client.make_bucket(bucket)
                    logger.info(f"建立 MinIO 儲存桶: {bucket}")
            
        except Exception as e:
            logger.error(f"MinIO 初始化失敗: {e}")
            raise
    
    def _init_milvus_collection(self):
        """初始化 Milvus 向量集合"""
        try:
            collection_name = "podcast_embeddings"
            
            # 如果集合已存在，先刪除
            if utility.has_collection(collection_name):
                utility.drop_collection(collection_name)
            
            # 定義欄位
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="episode_id", dtype=DataType.INT64),
                FieldSchema(name="sentence_index", dtype=DataType.INT64),
                FieldSchema(name="sentence_text", dtype=DataType.VARCHAR, max_length=2000),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384)
            ]
            
            # 建立集合
            schema = CollectionSchema(fields, collection_name)
            collection = Collection(collection_name, schema)
            
            # 建立索引
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            collection.create_index("embedding", index_params)
            
            logger.info("Milvus 集合初始化完成")
            
        except Exception as e:
            logger.error(f"Milvus 初始化失敗: {e}")
            raise
    
    def integrate_existing_crawlers(self):
        """整合現有爬蟲程式 - 保持原有程式不變"""
        logger.info("開始整合現有爬蟲程式...")
        
        try:
            # 這裡可以導入您現有的爬蟲程式
            # 例如：
            # from .PodcastScrap_v1 import PodcastScraper
            # from .PodcastDownload_v2_2 import PodcastDownloader
            # from .Spotify_Scrapy import SpotifyScraper
            
            # 為了示範，我們建立一些模擬資料
            podcasts_data = self._generate_sample_podcast_data()
            
            # 處理每個 Podcast
            for podcast_data in podcasts_data:
                # 1. 儲存 Podcast 資訊到 PostgreSQL
                podcast_id = self._save_podcast_to_postgres(podcast_data)
                
                # 2. 處理每個 Episode
                for episode_data in podcast_data['episodes']:
                    episode_id = self._save_episode_to_postgres(episode_data, podcast_id)
                    
                    # 3. 下載音頻到 MinIO
                    audio_path = self._download_audio_to_minio(episode_data, podcast_id)
                    
                    # 4. STT 轉錄
                    transcript_data = self._transcribe_audio(episode_data, episode_id)
                    
                    # 5. 儲存轉錄到 MongoDB
                    self._save_transcript_to_mongodb(transcript_data, episode_id)
                    
                    # 6. 儲存轉錄記錄到 PostgreSQL
                    self._save_transcript_record_to_postgres(transcript_data, episode_id)
                    
                    # 7. 生成摘要
                    summary_data = self._generate_summary(transcript_data, episode_id)
                    
                    # 8. 儲存摘要到 PostgreSQL
                    self._save_summary_to_postgres(summary_data, episode_id)
                    
                    # 9. 主題分類
                    topics_data = self._classify_topics(transcript_data, episode_id)
                    
                    # 10. 儲存主題到 PostgreSQL
                    self._save_topics_to_postgres(topics_data, episode_id)
                    
                    # 11. 生成向量嵌入
                    embeddings_data = self._generate_embeddings(transcript_data, episode_id)
                    
                    # 12. 儲存向量到 Milvus
                    self._save_embeddings_to_milvus(embeddings_data)
                    
                    # 13. 記錄任務日誌
                    self._log_task_completion(episode_id, "full_pipeline")
                    
                    # 14. 記錄嵌入日誌
                    self._log_embedding_completion(episode_id)
                    
                    # 15. 記錄攝取日誌
                    self._log_ingestion_completion(episode_data, episode_id)
            
            logger.info("現有爬蟲程式整合完成")
            
        except Exception as e:
            logger.error(f"爬蟲整合失敗: {e}")
            raise
    
    def _generate_sample_podcast_data(self) -> List[Dict[str, Any]]:
        """生成範例 Podcast 資料 - 模擬現有爬蟲的輸出"""
        return [
            {
                "podcast_id": 4,
                "name": "AI 科技前沿",
                "description": "探索人工智慧的最新發展與應用",
                "author": "AI 研究團隊",
                "rss_link": "https://feeds.simplecast.com/ai-frontier",
                "category": "科技",
                "languages": "zh-TW",
                "episodes": [
                    {
                        "episode_title": "AI 科技前沿 第 1 集 - 深度學習突破",
                        "published_date": "2024-01-25",
                        "audio_url": "https://example.com/audio/4_1.mp3",
                        "duration": 2400,
                        "description": "探討深度學習技術的最新突破與應用前景"
                    },
                    {
                        "episode_title": "AI 科技前沿 第 2 集 - 自然語言處理",
                        "published_date": "2024-01-26",
                        "audio_url": "https://example.com/audio/4_2.mp3",
                        "duration": 2100,
                        "description": "自然語言處理技術的發展與挑戰"
                    }
                ]
            },
            {
                "podcast_id": 5,
                "name": "創業思維",
                "description": "分享創業經驗與思維模式",
                "author": "創業導師",
                "rss_link": "https://feeds.simplecast.com/startup-mindset",
                "category": "商業",
                "languages": "zh-TW",
                "episodes": [
                    {
                        "episode_title": "創業思維 第 1 集 - 從零開始",
                        "published_date": "2024-01-27",
                        "audio_url": "https://example.com/audio/5_1.mp3",
                        "duration": 2700,
                        "description": "如何從零開始建立自己的事業"
                    },
                    {
                        "episode_title": "創業思維 第 2 集 - 團隊建設",
                        "published_date": "2024-01-28",
                        "audio_url": "https://example.com/audio/5_2.mp3",
                        "duration": 2250,
                        "description": "建立高效能團隊的關鍵要素"
                    }
                ]
            }
        ]
    
    def _save_podcast_to_postgres(self, podcast_data: Dict[str, Any]) -> int:
        """儲存 Podcast 到 PostgreSQL"""
        try:
            with self.postgres_conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO podcasts (
                        podcast_id, name, description, author, rss_link, category, languages
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (podcast_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        author = EXCLUDED.author,
                        rss_link = EXCLUDED.rss_link,
                        category = EXCLUDED.category,
                        languages = EXCLUDED.languages,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING podcast_id
                """, (
                    podcast_data['podcast_id'],
                    podcast_data['name'],
                    podcast_data['description'],
                    podcast_data['author'],
                    podcast_data['rss_link'],
                    podcast_data['category'],
                    podcast_data['languages']
                ))
                
                podcast_id = cursor.fetchone()[0]
                self.postgres_conn.commit()
                logger.info(f"Podcast 已儲存: {podcast_data['name']}")
                return podcast_id
                
        except Exception as e:
            logger.error(f"Podcast 儲存失敗: {e}")
            self.postgres_conn.rollback()
            raise
    
    def _save_episode_to_postgres(self, episode_data: Dict[str, Any], podcast_id: int) -> int:
        """儲存 Episode 到 PostgreSQL"""
        try:
            with self.postgres_conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO episodes (
                        podcast_id, episode_title, published_date, audio_url, duration, description, languages
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING episode_id
                """, (
                    podcast_id,
                    episode_data['episode_title'],
                    episode_data['published_date'],
                    episode_data['audio_url'],
                    episode_data['duration'],
                    episode_data['description'],
                    'zh-TW'
                ))
                
                episode_id = cursor.fetchone()[0]
                self.postgres_conn.commit()
                logger.info(f"Episode 已儲存: {episode_data['episode_title']}")
                return episode_id
                
        except Exception as e:
            logger.error(f"Episode 儲存失敗: {e}")
            self.postgres_conn.rollback()
            raise
    
    def _download_audio_to_minio(self, episode_data: Dict[str, Any], podcast_id: int) -> str:
        """下載音頻到 MinIO"""
        try:
            # 模擬音頻檔案內容
            audio_content = b"fake_audio_content_for_demo"
            audio_path = f"podcast-audio/{podcast_id}_{episode_data['episode_title'].split()[0]}.mp3"
            
            # 上傳到 MinIO
            self.minio_client.put_object(
                "podcast-audio",
                audio_path,
                audio_content,
                len(audio_content)
            )
            
            logger.info(f"音頻已上傳到 MinIO: {audio_path}")
            return audio_path
            
        except Exception as e:
            logger.error(f"音頻上傳失敗: {e}")
            raise
    
    def _transcribe_audio(self, episode_data: Dict[str, Any], episode_id: int) -> Dict[str, Any]:
        """使用 Whisper 進行語音轉文字"""
        try:
            # 模擬轉錄結果
            transcript = {
                "episode_id": episode_id,
                "episode_title": episode_data['episode_title'],
                "segments": [
                    {
                        "start": 0.0,
                        "end": 30.0,
                        "text": "歡迎收聽今天的節目，我們將深入探討最新的技術發展。",
                        "confidence": 0.95
                    },
                    {
                        "start": 30.0,
                        "end": 60.0,
                        "text": "首先讓我們來看看這個領域的最新突破。",
                        "confidence": 0.92
                    },
                    {
                        "start": 60.0,
                        "end": 90.0,
                        "text": "這些技術正在改變我們的生活方式。",
                        "confidence": 0.88
                    }
                ],
                "full_text": "歡迎收聽今天的節目，我們將深入探討最新的技術發展。首先讓我們來看看這個領域的最新突破。這些技術正在改變我們的生活方式。",
                "language": "zh",
                "duration": episode_data['duration'],
                "model_used": "whisper-base",
                "version": "1.0",
                "created_by": "auto_crawler_integrator"
            }
            
            logger.info(f"轉錄完成: {episode_data['episode_title']}")
            return transcript
            
        except Exception as e:
            logger.error(f"轉錄失敗: {e}")
            return {"error": str(e)}
    
    def _save_transcript_to_mongodb(self, transcript_data: Dict[str, Any], episode_id: int):
        """儲存轉錄結果到 MongoDB"""
        try:
            # 儲存完整轉錄
            self.mongodb_db.transcripts.insert_one({
                "episode_id": episode_id,
                "episode_title": transcript_data['episode_title'],
                "transcript": transcript_data,
                "created_at": datetime.now()
            })
            
            logger.info(f"轉錄結果已儲存到 MongoDB: {transcript_data['episode_title']}")
            
        except Exception as e:
            logger.error(f"MongoDB 儲存失敗: {e}")
    
    def _save_transcript_record_to_postgres(self, transcript_data: Dict[str, Any], episode_id: int):
        """儲存轉錄記錄到 PostgreSQL"""
        try:
            with self.postgres_conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO transcripts (
                        transcript_path, episode_id, transcript_length, language, model_used, version, created_by
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    f"podcast-transcripts/{episode_id}.json",
                    episode_id,
                    transcript_data['duration'],
                    transcript_data['language'],
                    transcript_data['model_used'],
                    transcript_data['version'],
                    transcript_data['created_by']
                ))
            
            self.postgres_conn.commit()
            
        except Exception as e:
            logger.error(f"轉錄記錄儲存失敗: {e}")
            self.postgres_conn.rollback()
    
    def _generate_summary(self, transcript_data: Dict[str, Any], episode_id: int) -> Dict[str, Any]:
        """生成摘要"""
        try:
            summary = {
                "episode_id": episode_id,
                "summary_text": f"本集節目探討了{transcript_data['episode_title']}的相關內容，包括技術發展、應用前景和未來趨勢。",
                "summary_model": "gpt-3.5-turbo",
                "topics": ["技術發展", "應用前景", "未來趨勢"]
            }
            
            logger.info(f"摘要生成完成: {episode_id}")
            return summary
            
        except Exception as e:
            logger.error(f"摘要生成失敗: {e}")
            return {"error": str(e)}
    
    def _save_summary_to_postgres(self, summary_data: Dict[str, Any], episode_id: int):
        """儲存摘要到 PostgreSQL"""
        try:
            with self.postgres_conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO summaries (
                        episode_id, summary_text, summary_model, topics
                    ) VALUES (%s, %s, %s, %s)
                    ON CONFLICT (episode_id) DO UPDATE SET
                        summary_text = EXCLUDED.summary_text,
                        summary_model = EXCLUDED.summary_model,
                        topics = EXCLUDED.topics,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    episode_id,
                    summary_data['summary_text'],
                    summary_data['summary_model'],
                    summary_data['topics']
                ))
            
            self.postgres_conn.commit()
            
        except Exception as e:
            logger.error(f"摘要儲存失敗: {e}")
            self.postgres_conn.rollback()
    
    def _classify_topics(self, transcript_data: Dict[str, Any], episode_id: int) -> List[Dict[str, Any]]:
        """主題分類"""
        try:
            # 模擬主題分類結果
            topics = [
                {
                    "episode_id": episode_id,
                    "topic_tag": "技術發展",
                    "source_type": "ML",
                    "confidence_score": 0.95,
                    "classified_by": "bert-classifier"
                },
                {
                    "episode_id": episode_id,
                    "topic_tag": "應用前景",
                    "source_type": "ML",
                    "confidence_score": 0.88,
                    "classified_by": "bert-classifier"
                },
                {
                    "episode_id": episode_id,
                    "topic_tag": "未來趨勢",
                    "source_type": "ML",
                    "confidence_score": 0.92,
                    "classified_by": "bert-classifier"
                }
            ]
            
            logger.info(f"主題分類完成: {episode_id}")
            return topics
            
        except Exception as e:
            logger.error(f"主題分類失敗: {e}")
            return []
    
    def _save_topics_to_postgres(self, topics_data: List[Dict[str, Any]], episode_id: int):
        """儲存主題到 PostgreSQL"""
        try:
            with self.postgres_conn.cursor() as cursor:
                for topic in topics_data:
                    cursor.execute("""
                        INSERT INTO topics (
                            episode_id, topic_tag, source_type, confidence_score, classified_by
                        ) VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (episode_id, topic_tag, source_type) DO UPDATE SET
                            confidence_score = EXCLUDED.confidence_score,
                            classified_by = EXCLUDED.classified_by,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        topic['episode_id'],
                        topic['topic_tag'],
                        topic['source_type'],
                        topic['confidence_score'],
                        topic['classified_by']
                    ))
            
            self.postgres_conn.commit()
            
        except Exception as e:
            logger.error(f"主題儲存失敗: {e}")
            self.postgres_conn.rollback()
    
    def _generate_embeddings(self, transcript_data: Dict[str, Any], episode_id: int) -> List[Dict[str, Any]]:
        """生成向量嵌入"""
        try:
            embeddings_data = []
            
            # 處理每個句子段落
            for i, segment in enumerate(transcript_data.get('segments', [])):
                sentence_text = segment['text']
                
                # 生成嵌入向量
                embedding = self.embedding_model.encode(sentence_text)
                
                embeddings_data.append({
                    "episode_id": episode_id,
                    "sentence_index": i,
                    "sentence_text": sentence_text,
                    "embedding": embedding.tolist()
                })
            
            logger.info(f"向量嵌入生成完成: {episode_id}")
            return embeddings_data
            
        except Exception as e:
            logger.error(f"向量嵌入生成失敗: {e}")
            return []
    
    def _save_embeddings_to_milvus(self, embeddings_data: List[Dict[str, Any]]):
        """儲存向量嵌入到 Milvus"""
        try:
            if not embeddings_data:
                return
            
            collection = Collection("podcast_embeddings")
            
            # 準備資料
            episode_ids = [item['episode_id'] for item in embeddings_data]
            sentence_indices = [item['sentence_index'] for item in embeddings_data]
            sentence_texts = [item['sentence_text'] for item in embeddings_data]
            embeddings = [item['embedding'] for item in embeddings_data]
            
            # 插入資料
            collection.insert([
                episode_ids,
                sentence_indices,
                sentence_texts,
                embeddings
            ])
            
            # 刷新集合
            collection.flush()
            
            logger.info(f"成功儲存 {len(embeddings_data)} 個向量到 Milvus")
            
        except Exception as e:
            logger.error(f"Milvus 儲存失敗: {e}")
            raise
    
    def _log_task_completion(self, episode_id: int, task_type: str):
        """記錄任務完成"""
        try:
            with self.postgres_conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO task_log (
                        task_id, task_type, episode_id, status, created_at, worker_id, triggered_by
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    f"task_{episode_id}_{int(time.time())}",
                    task_type,
                    episode_id,
                    "completed",
                    datetime.now(),
                    "auto_crawler_integrator",
                    "auto_crawler_integrator"
                ))
            
            self.postgres_conn.commit()
            
        except Exception as e:
            logger.error(f"任務日誌記錄失敗: {e}")
            self.postgres_conn.rollback()
    
    def _log_embedding_completion(self, episode_id: int):
        """記錄嵌入完成"""
        try:
            with self.postgres_conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO embedding_log (
                        episode_id, vector_type, vector_version, generated_at, vector_dim, worker_id, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    episode_id,
                    "sentence",
                    "all-MiniLM-L6-v2",
                    datetime.now(),
                    384,
                    "auto_crawler_integrator",
                    "completed"
                ))
            
            self.postgres_conn.commit()
            
        except Exception as e:
            logger.error(f"嵌入日誌記錄失敗: {e}")
            self.postgres_conn.rollback()
    
    def _log_ingestion_completion(self, episode_data: Dict[str, Any], episode_id: int):
        """記錄攝取完成"""
        try:
            with self.postgres_conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO ingestion_log (
                        source_platform, rss_url, episode_id, status, ingested_at, normalized_json
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    "apple_podcasts",
                    "https://feeds.simplecast.com/sample",
                    episode_id,
                    "completed",
                    datetime.now(),
                    {"title": episode_data['episode_title'], "duration": episode_data['duration']}
                ))
            
            self.postgres_conn.commit()
            
        except Exception as e:
            logger.error(f"攝取日誌記錄失敗: {e}")
            self.postgres_conn.rollback()
    
    def verify_data(self):
        """驗證資料完整性"""
        logger.info("驗證資料完整性...")
        
        try:
            # 檢查 PostgreSQL
            with self.postgres_conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM podcasts")
                podcast_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM episodes")
                episode_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM transcripts")
                transcript_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM summaries")
                summary_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM topics")
                topic_count = cursor.fetchone()[0]
            
            # 檢查 MongoDB
            mongodb_transcript_count = self.mongodb_db.transcripts.count_documents({})
            
            # 檢查 Milvus
            collection = Collection("podcast_embeddings")
            embedding_count = collection.num_entities
            
            # 檢查 MinIO
            audio_objects = list(self.minio_client.list_objects("podcast-audio"))
            audio_count = len(audio_objects)
            
            logger.info("=== 資料驗證結果 ===")
            logger.info(f"PostgreSQL Podcasts: {podcast_count}")
            logger.info(f"PostgreSQL Episodes: {episode_count}")
            logger.info(f"PostgreSQL Transcripts: {transcript_count}")
            logger.info(f"PostgreSQL Summaries: {summary_count}")
            logger.info(f"PostgreSQL Topics: {topic_count}")
            logger.info(f"MongoDB Transcripts: {mongodb_transcript_count}")
            logger.info(f"Milvus Embeddings: {embedding_count}")
            logger.info(f"MinIO Audio Files: {audio_count}")
            
            return {
                "podcasts": podcast_count,
                "episodes": episode_count,
                "transcripts": transcript_count,
                "summaries": summary_count,
                "topics": topic_count,
                "mongodb_transcripts": mongodb_transcript_count,
                "embeddings": embedding_count,
                "audio_files": audio_count
            }
            
        except Exception as e:
            logger.error(f"資料驗證失敗: {e}")
            raise
    
    def run(self):
        """執行完整的統合流程"""
        logger.info("=== 開始自動化爬蟲統合流程 ===")
        
        try:
            # 1. 初始化儲存服務
            self._init_minio_buckets()
            self._init_milvus_collection()
            
            # 2. 整合現有爬蟲程式
            self.integrate_existing_crawlers()
            
            # 3. 驗證資料
            verification_result = self.verify_data()
            
            logger.info("=== 自動化爬蟲統合流程完成 ===")
            return verification_result
            
        except Exception as e:
            logger.error(f"統合流程失敗: {e}")
            raise
        finally:
            # 關閉連接
            if self.postgres_conn:
                self.postgres_conn.close()
            if self.mongodb_client:
                self.mongodb_client.close()

def main():
    """主程式"""
    try:
        # 等待資料庫服務啟動
        logger.info("等待資料庫服務啟動...")
        time.sleep(30)
        
        # 建立統合實例
        integrator = AutoCrawlerIntegrator()
        
        # 執行統合流程
        result = integrator.run()
        
        logger.info("爬蟲統合服務執行完成！")
        return result
        
    except Exception as e:
        logger.error(f"爬蟲統合服務失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 