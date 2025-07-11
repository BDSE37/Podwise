"""
Milvus 向量化處理器
將 stage3_tagging 目錄下的 chunk 檔案轉換為向量並存入 Milvus
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
from core.vector_processor import VectorProcessor

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Milvus 連線設定
MILVUS_CONFIG = {
    'host': '192.168.32.86',  # worker3 IP
    'port': '19530'
}

# 集合名稱
COLLECTION_NAME = 'podwise_chunks'

# 向量維度 (BGE-M3 預設為 1024)
VECTOR_DIM = 1024


class MilvusVectorProcessor:
    """Milvus 向量化處理器"""
    
    def __init__(self, milvus_config: Dict[str, str], collection_name: str = COLLECTION_NAME):
        """
        初始化 Milvus 向量化處理器
        
        Args:
            milvus_config: Milvus 連線設定
            collection_name: 集合名稱
        """
        self.milvus_config = milvus_config
        self.collection_name = collection_name
        self.vector_processor = VectorProcessor(embedding_model="BAAI/bge-m3")
        
    def connect_milvus(self) -> None:
        """連線到 Milvus"""
        try:
            connections.connect(
                alias="default",
                host=self.milvus_config['host'],
                port=self.milvus_config['port']
            )
            logger.info("成功連線到 Milvus")
        except Exception as e:
            logger.error(f"連線 Milvus 失敗: {e}")
            raise
    
    def create_collection(self) -> None:
        """建立 Milvus 集合"""
        try:
            # 檢查集合是否已存在
            if utility.has_collection(self.collection_name):
                logger.info(f"集合 {self.collection_name} 已存在")
                return
            
            # 定義欄位結構
            fields = [
                FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
                FieldSchema(name="chunk_index", dtype=DataType.INT64),
                FieldSchema(name="episode_id", dtype=DataType.INT64),
                FieldSchema(name="podcast_id", dtype=DataType.INT64),
                FieldSchema(name="podcast_name", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="author", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="episode_title", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="duration", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="published_date", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="apple_rating", dtype=DataType.INT64),
                FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=1024),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=VECTOR_DIM),
                FieldSchema(name="language", dtype=DataType.VARCHAR, max_length=16),
                FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="source_model", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=1024)
            ]
            
            schema = CollectionSchema(fields, description="Podcast chunks with embeddings")
            collection = Collection(self.collection_name, schema)
            
            # 建立索引
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            collection.create_index(field_name="embedding", index_params=index_params)
            
            logger.info(f"成功建立集合 {self.collection_name}")
            
        except Exception as e:
            logger.error(f"建立集合失敗: {e}")
            raise
    
    def load_collection(self) -> Collection:
        """載入集合"""
        try:
            collection = Collection(self.collection_name)
            collection.load()
            logger.info(f"成功載入集合 {self.collection_name}")
            return collection
        except Exception as e:
            logger.error(f"載入集合失敗: {e}")
            raise
    
    def process_chunk_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        處理單個 chunk 檔案
        
        Args:
            file_path: 檔案路徑
            
        Returns:
            處理後的資料列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            chunks = data.get('chunks', [])
            if not chunks:
                logger.warning(f"檔案 {file_path.name} 沒有 chunks")
                return []
            
            # 生成所有 chunk 的嵌入向量
            chunk_texts = [chunk.get('chunk_text', '') for chunk in chunks]
            embeddings = self.vector_processor.generate_embeddings(chunk_texts)
            
            # 準備插入資料
            insert_data = []
            for i, chunk in enumerate(chunks):
                # 轉換 podcast_id 為整數
                podcast_id_str = chunk.get('podcast_id', '0')
                if podcast_id_str is None or podcast_id_str == '':
                    podcast_id = 0
                else:
                    try:
                        podcast_id = int(podcast_id_str)
                    except (ValueError, TypeError):
                        podcast_id = 0
                
                # 轉換 episode_id 為整數（使用 hash 處理十六進位字串）
                episode_id_str = chunk.get('episode_id', '0')
                if episode_id_str is None or episode_id_str == '':
                    episode_id = 0
                else:
                    try:
                        # 先嘗試直接轉換為整數
                        episode_id = int(episode_id_str)
                    except (ValueError, TypeError):
                        # 如果是十六進位字串或其他格式，使用 hash 生成數字 ID
                        episode_id = abs(hash(str(episode_id_str))) % (2**63)  # 確保在 INT64 範圍內
                
                # 處理日期格式
                published_date = chunk.get('published_date', '')
                if published_date is None or published_date == '未知':
                    published_date = ''
                
                # 處理標籤
                tags = chunk.get('enhanced_tags', [])
                tags_str = json.dumps(tags, ensure_ascii=False) if tags else '[]'
                
                # 確保所有欄位都有預設值
                insert_data.append({
                    'chunk_id': chunk.get('chunk_id', ''),
                    'chunk_index': chunk.get('chunk_index', 0),
                    'episode_id': episode_id,
                    'podcast_id': podcast_id,
                    'podcast_name': chunk.get('podcast_name', '') or '',
                    'author': chunk.get('author', '') or '',
                    'category': chunk.get('category', '') or '',
                    'episode_title': chunk.get('episode_title', '') or '',
                    'duration': chunk.get('duration', '') or '',
                    'published_date': published_date,
                    'apple_rating': chunk.get('apple_rating', 0) or 0,
                    'chunk_text': (chunk.get('chunk_text', '') or '')[:1024],  # 限制長度
                    'embedding': embeddings[i].tolist(),
                    'language': chunk.get('language', 'zh') or 'zh',
                    'created_at': chunk.get('created_at', datetime.now().isoformat()) or datetime.now().isoformat(),
                    'source_model': chunk.get('source_model', 'BAAI/bge-m3') or 'BAAI/bge-m3',
                    'tags': tags_str
                })
            
            return insert_data
            
        except Exception as e:
            logger.error(f"處理檔案 {file_path.name} 失敗: {e}")
            return []
    
    def insert_data_to_milvus(self, collection: Collection, data: List[Dict[str, Any]]) -> None:
        """
        將資料插入 Milvus
        
        Args:
            collection: Milvus 集合
            data: 要插入的資料
        """
        if not data:
            return
        
        try:
            # pymilvus 2.5.x 需要單一值格式，不是列表格式
            for item in data:
                # 直接插入單筆資料
                collection.insert([item])
            
            logger.info(f"成功插入 {len(data)} 筆資料")
            
        except Exception as e:
            logger.error(f"插入資料失敗: {e}")
            raise
    
    def process_stage3_tagging(self, base_folder: str = "data/stage3_tagging") -> None:
        """
        處理 stage3_tagging 目錄下的所有檔案
        
        Args:
            base_folder: 基礎目錄路徑
        """
        base_path = Path(base_folder)
        if not base_path.exists():
            logger.error(f"目錄不存在: {base_folder}")
            return
        
        # 連線 Milvus
        self.connect_milvus()
        
        # 建立集合
        self.create_collection()
        
        # 載入集合
        collection = self.load_collection()
        
        total_files = 0
        total_chunks = 0
        total_success = 0
        total_failed = 0
        
        # 遍歷所有子資料夾
        for subfolder in base_path.iterdir():
            if subfolder.is_dir():
                logger.info(f"處理資料夾: {subfolder.name}")
                
                # 處理該資料夾下的所有 JSON 檔案
                for json_file in subfolder.glob("*.json"):
                    total_files += 1
                    
                    try:
                        # 處理檔案
                        chunk_data = self.process_chunk_file(json_file)
                        
                        if chunk_data:
                            # 插入到 Milvus
                            self.insert_data_to_milvus(collection, chunk_data)
                            total_chunks += len(chunk_data)
                            total_success += 1
                            logger.info(f"成功處理檔案: {json_file.name} ({len(chunk_data)} chunks)")
                        else:
                            total_failed += 1
                            logger.warning(f"檔案無效: {json_file.name}")
                            
                    except Exception as e:
                        total_failed += 1
                        logger.error(f"處理檔案失敗 {json_file.name}: {e}")
        
        # 輸出統計結果
        logger.info("處理完成:")
        logger.info(f"  總檔案數: {total_files}")
        logger.info(f"  成功檔案: {total_success}")
        logger.info(f"  失敗檔案: {total_failed}")
        logger.info(f"  總 chunk 數: {total_chunks}")
        
        # 釋放集合
        collection.release()


def main():
    """主函數"""
    processor = MilvusVectorProcessor(MILVUS_CONFIG)
    processor.process_stage3_tagging()


if __name__ == "__main__":
    main() 