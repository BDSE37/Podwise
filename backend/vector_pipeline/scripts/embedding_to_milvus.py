"""
Milvus Embedding 處理器
將 stage4_embedding_prep 目錄下的資料進行 embedding 並寫入 Milvus
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
import sys
import os
import time
from tqdm import tqdm

# 添加父目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接定義 VectorProcessor 類別，避免依賴問題
import logging
from typing import List, Optional, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class VectorProcessor:
    """向量化處理器"""
    
    def __init__(self, embedding_model: str = "BAAI/bge-m3", device: Optional[str] = None):
        """
        初始化向量化處理器
        
        Args:
            embedding_model: 嵌入模型名稱
            device: 設備 (cpu/cuda)
        """
        self.embedding_model = embedding_model
        self.device = device
        self.model: Optional[SentenceTransformer] = None
        
    def load_model(self) -> None:
        """載入嵌入模型"""
        if self.model is None:
            try:
                logging.info(f"載入嵌入模型: {self.embedding_model}")
                self.model = SentenceTransformer(self.embedding_model, device=self.device)
                logging.info("嵌入模型載入成功")
            except Exception as e:
                logging.error(f"載入嵌入模型失敗: {e}")
                raise
    
    def generate_embeddings(self, texts: List[str], normalize: bool = True, 
                          show_progress_bar: bool = True) -> np.ndarray:
        """
        生成文本嵌入向量
        
        Args:
            texts: 文本列表
            normalize: 是否正規化
            show_progress_bar: 是否顯示進度條
            
        Returns:
            嵌入向量陣列
        """
        self.load_model()
        
        if self.model is None:
            raise RuntimeError("模型未正確載入")
        
        try:
            embeddings = self.model.encode(
                texts, 
                normalize_embeddings=normalize,
                show_progress_bar=show_progress_bar
            )
            logging.info(f"生成 {len(embeddings)} 個嵌入向量，維度: {embeddings.shape[1]}")
            return embeddings
        except Exception as e:
            logging.error(f"生成嵌入向量失敗: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        獲取模型資訊
        
        Returns:
            模型資訊字典
        """
        self.load_model()
        
        if self.model is None:
            raise RuntimeError("模型未正確載入")
        
        return {
            'model_name': self.embedding_model,
            'max_seq_length': self.model.max_seq_length,
            'embedding_dimension': self.model.get_sentence_embedding_dimension(),
            'device': str(self.model.device)
        }

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('embedding_process.log', encoding='utf-8')
    ]
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


class MilvusEmbeddingProcessor:
    """Milvus Embedding 處理器"""
    
    def __init__(self, milvus_config: Dict[str, str], collection_name: str = COLLECTION_NAME):
        """
        初始化 Milvus Embedding 處理器
        
        Args:
            milvus_config: Milvus 連線設定
            collection_name: 集合名稱
        """
        self.milvus_config = milvus_config
        self.collection_name = collection_name
        self.vector_processor = None
        self.model_loaded = False
        
    def initialize_vector_processor(self) -> None:
        """初始化向量處理器並載入模型"""
        try:
            logger.info("🔄 正在初始化向量處理器...")
            self.vector_processor = VectorProcessor(embedding_model="BAAI/bge-m3")
            
            logger.info("🔄 正在載入 BGE-M3 模型...")
            self.vector_processor.load_model()
            
            # 獲取模型資訊
            model_info = self.vector_processor.get_model_info()
            logger.info(f"✅ 模型載入成功!")
            logger.info(f"   模型名稱: {model_info['model_name']}")
            logger.info(f"   向量維度: {model_info['embedding_dimension']}")
            logger.info(f"   最大序列長度: {model_info['max_seq_length']}")
            logger.info(f"   設備: {model_info['device']}")
            
            self.model_loaded = True
            
        except Exception as e:
            logger.error(f"❌ 模型載入失敗: {e}")
            raise
        
    def connect_milvus(self) -> None:
        """連線到 Milvus"""
        try:
            logger.info(f"🔄 正在連線到 Milvus ({self.milvus_config['host']}:{self.milvus_config['port']})...")
            connections.connect(
                alias="default",
                host=self.milvus_config['host'],
                port=self.milvus_config['port']
            )
            logger.info("✅ 成功連線到 Milvus")
        except Exception as e:
            logger.error(f"❌ 連線 Milvus 失敗: {e}")
            raise
    
    def create_collection(self) -> None:
        """建立 Milvus 集合"""
        try:
            # 檢查集合是否已存在
            if utility.has_collection(self.collection_name):
                logger.info(f"ℹ️ 集合 {self.collection_name} 已存在")
                return
            
            logger.info(f"🔄 正在建立集合 {self.collection_name}...")
            
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
                FieldSchema(name="published_date", dtype=DataType.VARCHAR, max_length=64),  # 保持 VARCHAR 以兼容現有資料
                FieldSchema(name="apple_rating", dtype=DataType.FLOAT),
                FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=1024),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=VECTOR_DIM),
                FieldSchema(name="language", dtype=DataType.VARCHAR, max_length=16),
                FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=64),  # 保持 VARCHAR 以兼容現有資料
                FieldSchema(name="source_model", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=1024)
            ]
            
            schema = CollectionSchema(fields, description="Podcast chunks with embeddings")
            collection = Collection(self.collection_name, schema)
            
            # 建立索引
            logger.info("🔄 正在建立向量索引...")
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            collection.create_index(field_name="embedding", index_params=index_params)
            
            logger.info(f"✅ 成功建立集合 {self.collection_name}")
            
        except Exception as e:
            logger.error(f"❌ 建立集合失敗: {e}")
            raise
    
    def load_collection(self) -> Collection:
        """載入集合"""
        try:
            logger.info(f"🔄 正在載入集合 {self.collection_name}...")
            collection = Collection(self.collection_name)
            collection.load()
            logger.info(f"✅ 成功載入集合 {self.collection_name}")
            return collection
        except Exception as e:
            logger.error(f"❌ 載入集合失敗: {e}")
            raise
    
    def process_milvus_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        處理單個 Milvus 格式檔案
        
        Args:
            file_path: 檔案路徑
            
        Returns:
            處理後的資料列表
        """
        file_start_time = time.time()
        try:
            logger.info(f"📄 開始處理檔案: {file_path.name}")
            
            # 讀取檔案
            read_start_time = time.time()
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            read_time = time.time() - read_start_time
            logger.info(f"📖 檔案讀取完成，耗時: {read_time:.2f}秒")
            
            chunks = data.get('chunks', [])
            if not chunks:
                logger.warning(f"⚠️ 檔案 {file_path.name} 沒有 chunks")
                return []
            
            logger.info(f"📊 檔案 {file_path.name}: 找到 {len(chunks)} 個 chunks")
            
            # 生成所有 chunk 的嵌入向量
            chunk_texts = [chunk.get('chunk_text', '') for chunk in chunks]
            
            # 過濾空文本
            valid_texts = []
            valid_indices = []
            for i, text in enumerate(chunk_texts):
                if text and text.strip():
                    valid_texts.append(text)
                    valid_indices.append(i)
            
            if not valid_texts:
                logger.warning(f"⚠️ 檔案 {file_path.name}: 沒有有效的文本內容")
                return []
            
            logger.info(f"🔄 正在生成 {len(valid_texts)} 個嵌入向量...")
            embedding_start_time = time.time()
            
            if self.vector_processor is None:
                raise RuntimeError("向量處理器未初始化")
                
            embeddings = self.vector_processor.generate_embeddings(
                valid_texts, 
                normalize=True, 
                show_progress_bar=True
            )
            
            embedding_time = time.time() - embedding_start_time
            logger.info(f"✅ 嵌入向量生成完成，耗時: {embedding_time:.2f}秒")
            
            # 準備插入資料
            data_prep_start_time = time.time()
            logger.info(f"🔄 正在準備資料格式...")
            
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
                
                # 轉換 episode_id 為整數
                episode_id_str = chunk.get('episode_id', '0')
                if episode_id_str is None or episode_id_str == '':
                    episode_id = 0
                else:
                    try:
                        episode_id = int(episode_id_str)
                    except (ValueError, TypeError):
                        episode_id = 0
                
                # 處理日期格式
                published_date = chunk.get('published_date', '')
                if published_date is None or published_date == '未知':
                    published_date = ''
                
                # 處理 apple_rating，確保為 float 型別
                apple_rating = chunk.get('apple_rating', 0.0)
                try:
                    apple_rating = float(apple_rating)
                except (ValueError, TypeError):
                    apple_rating = 0.0
                
                # 處理標籤
                tags = chunk.get('tags', [])
                if isinstance(tags, str):
                    try:
                        tags = json.loads(tags)
                    except:
                        tags = []
                tags_str = json.dumps(tags, ensure_ascii=False) if tags else '[]'
                
                # 獲取對應的嵌入向量
                if i in valid_indices:
                    embedding_idx = valid_indices.index(i)
                    embedding = embeddings[embedding_idx].tolist()
                else:
                    # 如果文本為空，使用零向量
                    embedding = [0.0] * VECTOR_DIM
                
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
                    'apple_rating': apple_rating,
                    'chunk_text': (chunk.get('chunk_text', '') or '')[:1024],  # 限制長度
                    'embedding': embedding,
                    'language': chunk.get('language', 'zh') or 'zh',
                    'created_at': chunk.get('created_at', datetime.now().isoformat()) or datetime.now().isoformat(),
                    'source_model': chunk.get('source_model', 'BAAI/bge-m3') or 'BAAI/bge-m3',
                    'tags': tags_str
                })
            
            data_prep_time = time.time() - data_prep_start_time
            total_file_time = time.time() - file_start_time
            logger.info(f"✅ 資料準備完成，耗時: {data_prep_time:.2f}秒")
            logger.info(f"✅ 檔案 {file_path.name} 總處理時間: {total_file_time:.2f}秒")
            logger.info(f"📊 處理統計: 讀取 {read_time:.2f}s | 嵌入 {embedding_time:.2f}s | 準備 {data_prep_time:.2f}s")
            
            return insert_data
            
        except Exception as e:
            logger.error(f"❌ 處理檔案 {file_path.name} 失敗: {e}")
            return []
    
    def insert_data_to_milvus(self, collection: Collection, data: List[Dict[str, Any]]) -> None:
        """
        將資料插入 Milvus
        
        Args:
            collection: Milvus 集合
            data: 要插入的資料
        """
        if not data:
            logger.warning("⚠️ 沒有資料需要插入")
            return
        
        try:
            logger.info(f"🔄 正在插入 {len(data)} 筆資料到 Milvus...")
            insert_start_time = time.time()
            
            # 批次插入資料
            collection.insert(data)
            
            insert_time = time.time() - insert_start_time
            logger.info(f"✅ 成功插入 {len(data)} 筆資料，耗時: {insert_time:.2f}秒")
            logger.info(f"📊 平均每筆資料插入時間: {insert_time/len(data):.3f}秒")
            
        except Exception as e:
            logger.error(f"❌ 插入資料失敗: {e}")
            logger.error(f"❌ 錯誤詳情: {str(e)}")
            raise
    
    def process_stage4_embedding_prep(self, base_folder: str = "data/stage4_embedding_prep") -> None:
        """
        處理 stage4_embedding_prep 目錄下的所有檔案
        
        Args:
            base_folder: 基礎目錄路徑
        """
        logger.info("🚀 開始 Milvus Embedding 處理流程")
        logger.info("=" * 60)
        
        # 使用絕對路徑
        script_dir = Path(__file__).parent
        base_path = script_dir.parent / base_folder
        if not base_path.exists():
            logger.error(f"❌ 目錄不存在: {base_folder}")
            return
        
        # 初始化向量處理器
        self.initialize_vector_processor()
        
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
        total_embedding_time = 0
        total_insert_time = 0
        total_read_time = 0
        total_prep_time = 0
        
        # 處理所有 JSON 檔案
        json_files = [f for f in base_path.glob("*.json") if f.name != 'conversion_stats.json']
        logger.info(f"📁 找到 {len(json_files)} 個檔案需要處理")
        logger.info("=" * 60)
        
        overall_start_time = time.time()
        
        # 使用 tqdm 顯示進度條
        for json_file in tqdm(json_files, desc="處理檔案", unit="file"):
            file_start_time = time.time()
            total_files += 1
            
            try:
                logger.info(f"📄 處理檔案 {total_files}/{len(json_files)}: {json_file.name}")
                
                # 處理檔案
                chunk_data = self.process_milvus_file(json_file)
                
                if chunk_data:
                    # 插入到 Milvus
                    insert_start_time = time.time()
                    self.insert_data_to_milvus(collection, chunk_data)
                    insert_time = time.time() - insert_start_time
                    total_insert_time += insert_time
                    
                    total_chunks += len(chunk_data)
                    total_success += 1
                    
                    file_time = time.time() - file_start_time
                    logger.info(f"✅ 成功處理 {json_file.name}: {len(chunk_data)} chunks")
                    logger.info(f"📊 檔案處理時間: {file_time:.2f}秒 (插入: {insert_time:.2f}秒)")
                else:
                    total_failed += 1
                    logger.warning(f"⚠️ 檔案無效: {json_file.name}")
                    
            except Exception as e:
                total_failed += 1
                logger.error(f"❌ 處理檔案失敗 {json_file.name}: {e}")
        
        overall_time = time.time() - overall_start_time
        
        # 輸出統計結果
        logger.info("=" * 60)
        logger.info("🎉 處理完成!")
        logger.info(f"📊 統計結果:")
        logger.info(f"   總檔案數: {total_files}")
        logger.info(f"   成功檔案: {total_success}")
        logger.info(f"   失敗檔案: {total_failed}")
        logger.info(f"   總 chunk 數: {total_chunks}")
        logger.info(f"   成功率: {(total_success/total_files*100):.1f}%")
        logger.info(f"   總處理時間: {overall_time:.2f}秒")
        logger.info(f"   平均每檔案: {overall_time/total_files:.2f}秒")
        logger.info(f"   平均每 chunk: {overall_time/total_chunks:.3f}秒")
        logger.info(f"   總插入時間: {total_insert_time:.2f}秒")
        
        # 釋放集合
        collection.release()
        logger.info("✅ 集合已釋放")


def main():
    """主函數"""
    try:
        processor = MilvusEmbeddingProcessor(MILVUS_CONFIG)
        processor.process_stage4_embedding_prep()
    except KeyboardInterrupt:
        logger.info("⚠️ 使用者中斷處理")
    except Exception as e:
        logger.error(f"❌ 處理過程中發生錯誤: {e}")
        raise


if __name__ == "__main__":
    main() 