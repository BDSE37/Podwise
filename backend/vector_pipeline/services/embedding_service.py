"""
嵌入服務
整合所有向量化和 Milvus 操作功能
符合 Google Clean Code 原則
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np

from pymilvus import connections, Collection, utility
from ..core.vector_processor import VectorProcessor
from ..config.settings import config

logger = logging.getLogger(__name__)


class EmbeddingService:
    """嵌入服務 - 整合向量化和 Milvus 操作"""
    
    def __init__(self, milvus_config: Optional[Dict[str, Any]] = None):
        """
        初始化嵌入服務
        
        Args:
            milvus_config: Milvus 配置，如果為 None 則使用預設配置
        """
        self.milvus_config = milvus_config or {
            'host': config.milvus_host,
            'port': config.milvus_port
        }
        self.collection_name = config.collection_name
        self.vector_processor = VectorProcessor(
            embedding_model=config.embedding_model
        )
        self.connected = False
        
    def connect_milvus(self) -> bool:
        """連線到 Milvus"""
        try:
            connections.connect(
                alias="default",
                host=self.milvus_config['host'],
                port=self.milvus_config['port']
            )
            self.connected = True
            logger.info(f"✅ 成功連線到 Milvus: {self.milvus_config['host']}:{self.milvus_config['port']}")
            return True
        except Exception as e:
            logger.error(f"❌ Milvus 連線失敗: {e}")
            return False
    
    def disconnect_milvus(self) -> None:
        """斷開 Milvus 連線"""
        if self.connected:
            connections.disconnect("default")
            self.connected = False
            logger.info("🔌 Milvus 連線已斷開")
    
    def check_collection_exists(self) -> bool:
        """檢查集合是否存在"""
        try:
            return utility.has_collection(self.collection_name)
        except Exception as e:
            logger.error(f"檢查集合存在性失敗: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """獲取集合統計資訊"""
        try:
            if not self.check_collection_exists():
                return {"error": "集合不存在"}
            
            collection = Collection(self.collection_name)
            collection.load()
            
            stats = {
                "collection_name": self.collection_name,
                "num_entities": collection.num_entities,
                "schema": collection.schema.to_dict()
            }
            
            collection.release()
            return stats
            
        except Exception as e:
            logger.error(f"獲取集合統計失敗: {e}")
            return {"error": str(e)}
    
    def embed_stage3_data(self, stage3_dir: str = None) -> Dict[str, Any]:
        """
        將 stage3_tagging 資料嵌入到 Milvus
        
        Args:
            stage3_dir: stage3 目錄路徑
            
        Returns:
            嵌入結果統計
        """
        stage3_path = Path(stage3_dir or config.stage3_dir)
        
        if not stage3_path.exists():
            return {"error": f"目錄不存在: {stage3_path}"}
        
        # 連線到 Milvus
        if not self.connect_milvus():
            return {"error": "Milvus 連線失敗"}
        
        try:
            # 檢查集合是否存在
            if not self.check_collection_exists():
                return {"error": "Milvus 集合不存在，請先創建集合"}
            
            # 載入集合
            collection = Collection(self.collection_name)
            collection.load()
            
            # 處理所有檔案
            results = self._process_stage3_files(stage3_path, collection)
            
            # 釋放集合
            collection.release()
            
            return results
            
        except Exception as e:
            logger.error(f"嵌入過程失敗: {e}")
            return {"error": str(e)}
        finally:
            self.disconnect_milvus()
    
    def _process_stage3_files(self, stage3_path: Path, collection: Collection) -> Dict[str, Any]:
        """處理 stage3 檔案"""
        total_files = 0
        successful_files = 0
        failed_files = 0
        total_chunks = 0
        failed_files_list = []
        
        # 遍歷所有子資料夾
        for subfolder in stage3_path.iterdir():
            if not subfolder.is_dir():
                continue
                
            logger.info(f"處理資料夾: {subfolder.name}")
            
            # 處理該資料夾下的所有 JSON 檔案
            json_files = list(subfolder.glob("*.json"))
            
            for json_file in json_files:
                total_files += 1
                
                try:
                    # 讀取檔案
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 處理 chunks
                    chunks = data.get('chunks', [])
                    if not chunks:
                        failed_files += 1
                        failed_files_list.append(str(json_file))
                        continue
                    
                    # 過濾有效的 chunks
                    valid_chunks = []
                    for chunk in chunks:
                        chunk_text = chunk.get('chunk_text', '')
                        if chunk_text and chunk_text.strip() != '' and chunk_text.strip() != '!':
                            valid_chunks.append(chunk)
                    
                    if not valid_chunks:
                        failed_files += 1
                        failed_files_list.append(str(json_file))
                        continue
                    
                    # 生成嵌入向量
                    texts = [chunk['chunk_text'] for chunk in valid_chunks]
                    embeddings = self.vector_processor.generate_embeddings(texts)
                    
                    # 準備插入資料
                    insert_data = self._prepare_insert_data(data, valid_chunks, embeddings)
                    
                    # 插入到 Milvus
                    collection.insert(insert_data)
                    
                    successful_files += 1
                    total_chunks += len(valid_chunks)
                    
                    if total_files % 100 == 0:
                        logger.info(f"已處理 {total_files} 個檔案，成功 {successful_files} 個")
                    
                except Exception as e:
                    logger.error(f"處理檔案失敗 {json_file}: {e}")
                    failed_files += 1
                    failed_files_list.append(str(json_file))
        
        return {
            "total_files": total_files,
            "successful_files": successful_files,
            "failed_files": failed_files,
            "total_chunks": total_chunks,
            "failed_files_list": failed_files_list,
            "success_rate": successful_files / total_files * 100 if total_files > 0 else 0
        }
    
    def _prepare_insert_data(self, data: Dict[str, Any], chunks: List[Dict], 
                           embeddings: np.ndarray) -> Dict[str, List]:
        """準備插入資料"""
        insert_data = {
            "chunk_id": [],
            "chunk_index": [],
            "episode_id": [],
            "podcast_id": [],
            "podcast_name": [],
            "author": [],
            "category": [],
            "episode_title": [],
            "duration": [],
            "published_date": [],
            "apple_rating": [],
            "chunk_text": [],
            "embedding": [],
            "language": [],
            "created_at": [],
            "source_model": [],
            "tag": []
        }
        
        # 獲取 episode 資訊
        episode_info = data.get('episode_info', {})
        
        for i, chunk in enumerate(chunks):
            insert_data["chunk_id"].append(chunk.get('chunk_id', ''))
            insert_data["chunk_index"].append(chunk.get('chunk_index', 0))
            insert_data["episode_id"].append(episode_info.get('episode_id', 0))
            insert_data["podcast_id"].append(episode_info.get('podcast_id', 0))
            insert_data["podcast_name"].append(episode_info.get('podcast_name', ''))
            insert_data["author"].append(episode_info.get('author', ''))
            insert_data["category"].append(episode_info.get('category', ''))
            insert_data["episode_title"].append(episode_info.get('episode_title', ''))
            insert_data["duration"].append(episode_info.get('duration', ''))
            insert_data["published_date"].append(episode_info.get('published_date', ''))
            insert_data["apple_rating"].append(episode_info.get('apple_rating', 0))
            insert_data["chunk_text"].append(chunk.get('chunk_text', ''))
            insert_data["embedding"].append(embeddings[i].tolist())
            insert_data["language"].append(episode_info.get('language', 'zh'))
            insert_data["created_at"].append(datetime.now().isoformat())
            insert_data["source_model"].append(config.embedding_model)
            insert_data["tag"].append(json.dumps(chunk.get('enhanced_tags', []), ensure_ascii=False))
        
        return insert_data
    
    def search_similar_chunks(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        搜尋相似的 chunks
        
        Args:
            query_text: 查詢文本
            top_k: 返回結果數量
            
        Returns:
            相似 chunks 列表
        """
        try:
            if not self.connect_milvus():
                return []
            
            # 載入集合
            collection = Collection(self.collection_name)
            collection.load()
            
            # 生成查詢向量
            query_embedding = self.vector_processor.generate_single_embedding(query_text)
            
            # 執行搜尋
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["chunk_id", "chunk_text", "episode_title", "podcast_name", "tag"]
            )
            
            # 處理結果
            search_results = []
            if results and len(results) > 0:
                hits = results[0]
                for hit in hits:
                    search_results.append({
                        "score": hit.score,
                        "chunk_id": hit.entity.get('chunk_id'),
                        "chunk_text": hit.entity.get('chunk_text'),
                        "episode_title": hit.entity.get('episode_title'),
                        "podcast_name": hit.entity.get('podcast_name'),
                        "tags": json.loads(hit.entity.get('tag', '[]'))
                    })
            
            collection.release()
            return search_results
            
        except Exception as e:
            logger.error(f"搜尋失敗: {e}")
            return []
        finally:
            self.disconnect_milvus() 