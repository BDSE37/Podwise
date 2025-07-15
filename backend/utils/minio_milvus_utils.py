#!/usr/bin/env python3
"""
MinIO 和 Milvus 工具函數
提供 MinIO 客戶端、標籤獲取和 URL 生成功能
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from minio import Minio
from minio.error import S3Error

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MinIO 配置
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "192.168.32.66:30090")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "bdse37")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "11111111")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
MINIO_URL = f"http://{MINIO_ENDPOINT}"

def get_minio_client() -> Minio:
    """獲取 MinIO 客戶端"""
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        return client
    except Exception as e:
        logger.error(f"創建 MinIO 客戶端失敗: {e}")
        raise

def get_tags_for_audio(podcast_id: str, episode_title: str) -> List[str]:
    """根據 podcast_id 和 episode_title 獲取標籤"""
    try:
        # 商業類別預設標籤
        business_tags = [
            "投資理財", "股票分析", "經濟分析", "財務規劃", 
            "市場趨勢", "企業管理", "創業", "商業策略",
            "風險管理", "資產配置", "基金投資", "房地產投資"
        ]
        
        # 教育類別預設標籤
        education_tags = [
            "學習方法", "教育理念", "知識分享", "個人成長",
            "技能提升", "職業發展", "時間管理", "閱讀習慣",
            "思維模式", "創新思維", "領導力", "溝通技巧"
        ]
        
        # 根據 podcast_id 和 episode_title 判斷類別
        title_lower = episode_title.lower()
        podcast_lower = podcast_id.lower()
        
        # 商業類別關鍵字
        business_keywords = ["投資", "股票", "理財", "經濟", "財務", "市場", "企業", "創業", "商業", "基金", "房地產"]
        # 教育類別關鍵字
        education_keywords = ["學習", "教育", "知識", "成長", "技能", "職業", "時間", "閱讀", "思維", "創新", "領導", "溝通"]
        
        # 檢查是否包含商業關鍵字
        if any(keyword in title_lower or keyword in podcast_lower for keyword in business_keywords):
            return business_tags
        # 檢查是否包含教育關鍵字
        elif any(keyword in title_lower or keyword in podcast_lower for keyword in education_keywords):
            return education_tags
        else:
            # 預設返回商業類別
            return business_tags
            
    except Exception as e:
        logger.error(f"獲取標籤失敗: {e}")
        return ["一般", "知識分享"]

def get_podcast_name_from_db(podcast_id: str) -> str:
    """從資料庫獲取 podcast 名稱"""
    try:
        import psycopg2
        import os
        
        db_config = {
            "host": os.getenv("POSTGRES_HOST", "10.233.50.117"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "podcast"),
            "user": os.getenv("POSTGRES_USER", "bdse37"),
            "password": os.getenv("POSTGRES_PASSWORD", "111111")
        }
        
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # 查詢 podcast 名稱
        cursor.execute("SELECT name FROM podcasts WHERE podcast_id = %s", (int(podcast_id),))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return result[0]
        else:
            # 如果資料庫沒有，返回預設名稱
            podcast_names = {
                "123": "股癌 Gooaye",
                "456": "矽谷輕鬆談",
                "789": "天下學習",
                "101": "知識就是力量",
                "102": "科技新知",
                "103": "心靈成長"
            }
            return podcast_names.get(podcast_id, f"Podcast {podcast_id}")
        
    except Exception as e:
        logger.error(f"獲取 podcast 名稱失敗: {e}")
        # 如果資料庫連接失敗，返回預設名稱
        podcast_names = {
            "123": "股癌 Gooaye",
            "456": "矽谷輕鬆談",
            "789": "天下學習",
            "101": "知識就是力量",
            "102": "科技新知",
            "103": "心靈成長"
        }
        return podcast_names.get(podcast_id, f"Podcast {podcast_id}")

def get_audio_url(bucket: str, object_name: str) -> str:
    """獲取音檔 URL"""
    return f"{MINIO_URL}/{bucket}/{object_name}"

def get_image_url(podcast_id: str, size: str = "300") -> str:
    """獲取圖片 URL"""
    # 根據實際圖片命名格式：RSS_{rss_id}_{size}.jpg
    return f"{MINIO_URL}/podcast-images/RSS_{podcast_id}_{size}.jpg"

def list_bucket_objects(bucket: str, prefix: str = "") -> List[Dict[str, Any]]:
    """列出 bucket 中的物件"""
    try:
        client = get_minio_client()
        objects = client.list_objects(bucket, prefix=prefix, recursive=True)
        
        result = []
        for obj in objects:
            result.append({
                "name": obj.object_name,
                "size": obj.size,
                "last_modified": obj.last_modified,
                "etag": obj.etag
            })
        
        return result
        
    except Exception as e:
        logger.error(f"列出 bucket 物件失敗: {e}")
        return []

def check_bucket_exists(bucket: str) -> bool:
    """檢查 bucket 是否存在"""
    try:
        client = get_minio_client()
        return client.bucket_exists(bucket)
    except Exception as e:
        logger.error(f"檢查 bucket 存在性失敗: {e}")
        return False

def get_presigned_url(bucket: str, object_name: str, expires: int = 3600) -> str:
    """獲取預簽名 URL"""
    try:
        from datetime import timedelta
        client = get_minio_client()
        return client.presigned_get_object(bucket, object_name, expires=timedelta(seconds=expires))
    except Exception as e:
        logger.error(f"獲取預簽名 URL 失敗: {e}")
        return get_audio_url(bucket, object_name) 