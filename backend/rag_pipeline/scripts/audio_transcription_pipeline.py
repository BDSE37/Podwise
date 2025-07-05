#!/usr/bin/env python3
"""
音檔轉錄管線系統
整合 STT 服務、標籤處理和 RAG 搜尋
"""

import os
import sys
import json
import logging
import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# 添加專案路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure
except ImportError:
    print("請安裝 pymongo: pip install pymongo")
    sys.exit(1)

try:
    from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
except ImportError:
    print("請安裝 pymilvus: pip install pymilvus")
    sys.exit(1)

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("請安裝 sentence-transformers: pip install sentence-transformers")
    sys.exit(1)

from tag_processor import TagProcessor

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AudioTranscriptionPipeline:
    """音檔轉錄管線系統"""
    
    def __init__(self, 
                 stt_service_url: str = "http://localhost:8001",
                 mongodb_uri: str = "mongodb://localhost:27017/",
                 mongodb_db: str = "podwise",
                 mongodb_collection: str = "podcast",
                 milvus_host: str = "localhost",
                 milvus_port: str = "19530",
                 embedding_model: str = "BAAI/bge-m3",
                 tag_excel_path: str = "TAG參考資料.xlsx",
                 audio_dir: str = "../../../data/raw/music"):
        """
        初始化音檔轉錄管線
        
        Args:
            stt_service_url: STT 服務 URL
            mongodb_uri: MongoDB 連接 URI
            mongodb_db: MongoDB 資料庫名稱
            mongodb_collection: MongoDB 集合名稱
            milvus_host: Milvus 主機
            milvus_port: Milvus 端口
            embedding_model: 嵌入模型名稱
            tag_excel_path: 標籤 Excel 檔案路徑
            audio_dir: 音檔目錄路徑
        """
        self.stt_service_url = stt_service_url
        self.mongodb_uri = mongodb_uri
        self.mongodb_db = mongodb_db
        self.mongodb_collection = mongodb_collection
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.embedding_model = embedding_model
        self.audio_dir = Path(audio_dir)
        
        # 初始化連接
        self.mongo_client = None
        self.mongo_db = None
        self.mongo_collection = None
        self.milvus_connected = False
        
        # 初始化標籤處理器
        self.tag_processor = TagProcessor(tag_excel_path)
        
        # 初始化嵌入模型
        self.embedding_model_instance = None
        
        # 連接資料庫
        self.connect_databases()
        self.load_embedding_model()
    
    def connect_databases(self):
        """連接資料庫"""
        # 連接 MongoDB
        try:
            self.mongo_client = MongoClient(self.mongodb_uri)
            self.mongo_db = self.mongo_client[self.mongodb_db]
            self.mongo_collection = self.mongo_db[self.mongodb_collection]
            
            # 測試連接
            self.mongo_client.admin.command('ping')
            logger.info("✅ MongoDB 連接成功")
            
        except ConnectionFailure as e:
            logger.error(f"❌ MongoDB 連接失敗: {e}")
            raise
        
        # 連接 Milvus
        try:
            connections.connect(
                alias="default",
                host=self.milvus_host,
                port=self.milvus_port
            )
            self.milvus_connected = True
            logger.info("✅ Milvus 連接成功")
            
        except Exception as e:
            logger.error(f"❌ Milvus 連接失敗: {e}")
            raise
    
    def load_embedding_model(self):
        """載入嵌入模型"""
        try:
            logger.info(f"🔧 載入嵌入模型: {self.embedding_model}")
            self.embedding_model_instance = SentenceTransformer(self.embedding_model)
            logger.info("✅ 嵌入模型載入成功")
            
        except Exception as e:
            logger.error(f"❌ 載入嵌入模型失敗: {e}")
            raise
    
    def check_stt_service(self) -> bool:
        """檢查 STT 服務狀態"""
        try:
            response = requests.get(f"{self.stt_service_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ STT 服務正常運行")
                return True
            else:
                logger.warning(f"⚠️ STT 服務狀態異常: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ STT 服務連接失敗: {e}")
            return False
    
    def transcribe_audio_file(self, audio_file_path: Path) -> Optional[Dict]:
        """
        使用 STT 服務轉錄音檔
        
        Args:
            audio_file_path: 音檔路徑
            
        Returns:
            轉錄結果
        """
        if not self.check_stt_service():
            logger.error("STT 服務不可用")
            return None
        
        try:
            logger.info(f"🎵 開始轉錄音檔: {audio_file_path.name}")
            
            # 準備檔案
            with open(audio_file_path, 'rb') as audio_file:
                files = {'file': (audio_file_path.name, audio_file, 'audio/mpeg')}
                data = {'language': 'zh'}
                
                # 發送轉錄請求
                response = requests.post(
                    f"{self.stt_service_url}/transcribe",
                    files=files,
                    data=data,
                    timeout=300  # 5分鐘超時
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ 轉錄完成: {audio_file_path.name}")
                logger.info(f"📝 轉錄文本長度: {len(result.get('text', ''))}")
                return result
            else:
                logger.error(f"❌ 轉錄失敗: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 轉錄過程中發生錯誤: {e}")
            return None
    
    def save_transcription_to_mongodb(self, audio_file_path: Path, transcription_result: Dict) -> Optional[str]:
        """
        將轉錄結果儲存到 MongoDB
        
        Args:
            audio_file_path: 音檔路徑
            transcription_result: 轉錄結果
            
        Returns:
            文件 ID
        """
        try:
            # 準備文件資料
            document = {
                'audio_file': audio_file_path.name,
                'audio_file_path': str(audio_file_path),
                'content': transcription_result.get('text', ''),
                'language': transcription_result.get('language', 'zh'),
                'confidence': transcription_result.get('confidence', 0.0),
                'model_used': transcription_result.get('model_used', 'faster-whisper-medium'),
                'processing_time': transcription_result.get('processing_time', 0),
                'segments': transcription_result.get('segments', []),
                'language_probability': transcription_result.get('language_probability', 0),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # 插入到 MongoDB
            result = self.mongo_collection.insert_one(document)
            document_id = str(result.inserted_id)
            
            logger.info(f"💾 轉錄結果已儲存到 MongoDB: {document_id}")
            return document_id
            
        except Exception as e:
            logger.error(f"❌ 儲存到 MongoDB 失敗: {e}")
            return None
    
    def create_milvus_collection(self, collection_name: str = "podcast_chunks"):
        """
        建立 Milvus 集合
        
        Args:
            collection_name: 集合名稱
        """
        if not self.milvus_connected:
            raise Exception("Milvus 未連接")
        
        # 檢查集合是否已存在
        if utility.has_collection(collection_name):
            logger.info(f"📋 集合 {collection_name} 已存在")
            return collection_name
        
        # 定義集合結構
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024),  # bge-m3 維度
            FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=2048),
            FieldSchema(name="source_document_id", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
            FieldSchema(name="chunk_length", dtype=DataType.INT64),
            FieldSchema(name="tag_count", dtype=DataType.INT64),
            FieldSchema(name="audio_file", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=64)
        ]
        
        schema = CollectionSchema(fields, description="Podcast chunks with embeddings and tags")
        
        # 建立集合
        collection = Collection(collection_name, schema)
        
        # 建立索引
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        
        logger.info(f"✅ 成功建立 Milvus 集合: {collection_name}")
        return collection_name
    
    def process_transcription_with_tags(self, document_id: str, content: str) -> List[Dict]:
        """
        處理轉錄文本，切斷並標記標籤
        
        Args:
            document_id: MongoDB 文件 ID
            content: 轉錄文本內容
            
        Returns:
            處理後的 chunks 列表
        """
        # 建立模擬文件結構
        document = {
            '_id': document_id,
            'content': content
        }
        
        # 使用標籤處理器處理
        chunks = self.tag_processor.process_mongodb_document(document, 'content')
        
        logger.info(f"🏷️ 文本處理完成，產生 {len(chunks)} 個 chunks")
        return chunks
    
    def vectorize_and_store_chunks(self, chunks: List[Dict], audio_file: str, collection_name: str = "podcast_chunks"):
        """
        向量化並儲存 chunks 到 Milvus
        
        Args:
            chunks: 處理後的 chunks
            audio_file: 音檔名稱
            collection_name: Milvus 集合名稱
        """
        if not chunks:
            logger.warning("沒有 chunks 需要處理")
            return
        
        # 建立集合
        self.create_milvus_collection(collection_name)
        collection = Collection(collection_name)
        
        try:
            # 準備批次資料
            batch_data = []
            
            for chunk in chunks:
                # 生成嵌入向量
                embedding = self.embedding_model_instance.encode(
                    chunk['chunk_text'], 
                    normalize_embeddings=True
                )
                
                # 準備 Milvus 資料
                milvus_data = {
                    'chunk_id': chunk['chunk_id'],
                    'chunk_text': chunk['chunk_text'],
                    'embedding': embedding.tolist(),
                    'tags': json.dumps(chunk['tags'], ensure_ascii=False),
                    'source_document_id': chunk['source_document_id'],
                    'chunk_index': chunk['chunk_index'],
                    'chunk_length': chunk['chunk_length'],
                    'tag_count': chunk['tag_count'],
                    'audio_file': audio_file,
                    'created_at': datetime.now().isoformat()
                }
                
                batch_data.append(milvus_data)
            
            # 插入到 Milvus
            collection.insert(batch_data)
            logger.info(f"✅ 成功儲存 {len(batch_data)} 個向量到 Milvus")
            
        except Exception as e:
            logger.error(f"❌ 儲存到 Milvus 失敗: {e}")
        finally:
            collection.release()
    
    def search_similar_chunks(self, 
                            query_text: str, 
                            top_k: int = 10,
                            collection_name: str = "podcast_chunks") -> List[Dict]:
        """
        搜尋相似 chunks
        
        Args:
            query_text: 查詢文本
            top_k: 返回結果數量
            collection_name: 集合名稱
            
        Returns:
            相似 chunks 列表
        """
        if not self.milvus_connected:
            raise Exception("Milvus 未連接")
        
        collection = Collection(collection_name)
        collection.load()
        
        try:
            # 生成查詢向量
            query_embedding = self.embedding_model_instance.encode(
                query_text, 
                normalize_embeddings=True
            )
            
            # 搜尋參數
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            # 執行搜尋
            results = collection.search(
                data=[query_embedding.tolist()],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["chunk_id", "chunk_text", "tags", "source_document_id", "chunk_index", "audio_file"]
            )
            
            # 格式化結果
            similar_chunks = []
            for hits in results:
                for hit in hits:
                    chunk_data = {
                        'chunk_id': hit.entity.get('chunk_id'),
                        'chunk_text': hit.entity.get('chunk_text'),
                        'tags': json.loads(hit.entity.get('tags', '[]')),
                        'source_document_id': hit.entity.get('source_document_id'),
                        'chunk_index': hit.entity.get('chunk_index'),
                        'audio_file': hit.entity.get('audio_file'),
                        'score': hit.score
                    }
                    similar_chunks.append(chunk_data)
            
            return similar_chunks
            
        finally:
            collection.release()
    
    def process_audio_directory(self, max_files: int = None) -> Dict[str, Any]:
        """
        處理音檔目錄中的所有音檔
        
        Args:
            max_files: 最大處理檔案數量（None 表示處理所有檔案）
            
        Returns:
            處理結果統計
        """
        if not self.audio_dir.exists():
            logger.error(f"❌ 音檔目錄不存在: {self.audio_dir}")
            return {}
        
        # 取得所有音檔
        audio_files = list(self.audio_dir.glob("*.mp3"))
        if not audio_files:
            logger.warning(f"⚠️ 目錄中沒有找到 MP3 檔案: {self.audio_dir}")
            return {}
        
        # 限制處理檔案數量
        if max_files:
            audio_files = audio_files[:max_files]
        
        logger.info(f"🎵 找到 {len(audio_files)} 個音檔")
        
        # 統計資訊
        stats = {
            'total_files': len(audio_files),
            'processed_files': 0,
            'transcription_success': 0,
            'mongodb_success': 0,
            'milvus_success': 0,
            'errors': []
        }
        
        for i, audio_file in enumerate(audio_files, 1):
            logger.info(f"📁 處理檔案 {i}/{len(audio_files)}: {audio_file.name}")
            
            try:
                # 1. 轉錄音檔
                transcription_result = self.transcribe_audio_file(audio_file)
                if not transcription_result:
                    stats['errors'].append(f"轉錄失敗: {audio_file.name}")
                    continue
                
                stats['transcription_success'] += 1
                
                # 2. 儲存到 MongoDB
                document_id = self.save_transcription_to_mongodb(audio_file, transcription_result)
                if not document_id:
                    stats['errors'].append(f"MongoDB 儲存失敗: {audio_file.name}")
                    continue
                
                stats['mongodb_success'] += 1
                
                # 3. 處理文本並標記標籤
                chunks = self.process_transcription_with_tags(
                    document_id, 
                    transcription_result.get('text', '')
                )
                
                # 4. 向量化並儲存到 Milvus
                if chunks:
                    self.vectorize_and_store_chunks(chunks, audio_file.name)
                    stats['milvus_success'] += 1
                
                stats['processed_files'] += 1
                
                # 避免過度負載
                time.sleep(1)
                
            except Exception as e:
                error_msg = f"處理檔案 {audio_file.name} 失敗: {e}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
        
        return stats
    
    def test_rag_search(self, test_queries: List[str] = None):
        """
        測試 RAG 搜尋功能
        
        Args:
            test_queries: 測試查詢列表
        """
        if not test_queries:
            # 預設測試查詢
            test_queries = [
                "人工智慧在企業中的應用",
                "如何提升工作效率",
                "創業需要注意什麼",
                "時間管理的方法",
                "領導力的重要性",
                "台灣半導體產業發展",
                "雲端運算的優勢",
                "區塊鏈技術應用",
                "教育創新與學習",
                "商業模式創新"
            ]
        
        logger.info("🧪 開始測試 RAG 搜尋功能")
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n🔍 測試查詢 {i}: {query}")
            
            try:
                similar_chunks = self.search_similar_chunks(query, top_k=3)
                
                if similar_chunks:
                    logger.info(f"✅ 找到 {len(similar_chunks)} 個相關結果:")
                    
                    for j, chunk in enumerate(similar_chunks, 1):
                        logger.info(f"  結果 {j}:")
                        logger.info(f"    相似度: {chunk['score']:.4f}")
                        logger.info(f"    標籤: {chunk['tags']}")
                        logger.info(f"    音檔: {chunk['audio_file']}")
                        logger.info(f"    文本: {chunk['chunk_text'][:150]}...")
                        logger.info("")
                else:
                    logger.warning("⚠️ 沒有找到相關結果")
                    
            except Exception as e:
                logger.error(f"❌ 搜尋失敗: {e}")
    
    def close_connections(self):
        """關閉連接"""
        if self.mongo_client:
            self.mongo_client.close()
            logger.info("MongoDB 連接已關閉")
        
        if self.milvus_connected:
            connections.disconnect("default")
            logger.info("Milvus 連接已關閉")

def main():
    """主函數"""
    # 初始化管線
    pipeline = AudioTranscriptionPipeline(
        stt_service_url="http://localhost:8001",
        mongodb_uri="mongodb://localhost:27017/",
        mongodb_db="podwise",
        mongodb_collection="podcast",
        milvus_host="localhost",
        milvus_port="19530",
        embedding_model="BAAI/bge-m3",
        tag_excel_path="TAG參考資料.xlsx",
        audio_dir="../../../data/raw/music"
    )
    
    try:
        # 處理音檔目錄
        print("🎵 開始處理音檔目錄...")
        stats = pipeline.process_audio_directory(max_files=3)  # 先處理 3 個檔案測試
        
        print("\n📊 處理結果統計:")
        print(f"總檔案數: {stats['total_files']}")
        print(f"已處理檔案數: {stats['processed_files']}")
        print(f"轉錄成功: {stats['transcription_success']}")
        print(f"MongoDB 儲存成功: {stats['mongodb_success']}")
        print(f"Milvus 儲存成功: {stats['milvus_success']}")
        print(f"錯誤數: {len(stats['errors'])}")
        
        if stats['errors']:
            print("\n❌ 錯誤列表:")
            for error in stats['errors']:
                print(f"- {error}")
        
        # 測試 RAG 搜尋
        print("\n🧪 測試 RAG 搜尋功能...")
        pipeline.test_rag_search()
        
    except Exception as e:
        logger.error(f"❌ 執行過程中發生錯誤: {e}")
    
    finally:
        pipeline.close_connections()

if __name__ == "__main__":
    main() 