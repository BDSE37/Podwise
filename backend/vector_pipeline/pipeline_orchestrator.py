"""
Pipeline Orchestrator
整合所有核心組件，實現完整的資料處理流程
MongoDB 長文本 → 切分 chunks → 標籤貼標 → PostgreSQL metadata mapping → 向量化 → 寫入 Milvus

遵循 Google Clean Code Style 和 OOP 原則
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import sys
from pathlib import Path
from abc import ABC, abstractmethod

# 添加父目錄到路徑以支援絕對 import
sys.path.append(str(Path(__file__).parent.parent))

from .core import (
    MongoDBProcessor, MongoDocument,
    PostgreSQLMapper, EpisodeMetadata,
    TextChunker, TextChunk,
    VectorProcessor,
    MilvusWriter,
    UnifiedTagManager,
    TagExtractionResult
)
from .error_logger import ErrorLogger, ErrorHandler

logger = logging.getLogger(__name__)


@dataclass
class ProcessedChunk:
    """處理後的文本塊資料類別"""
    chunk_id: str
    chunk_index: int
    chunk_text: str
    chunk_length: int
    episode_id: int
    podcast_id: int
    episode_title: str
    podcast_name: str
    author: str
    category: str
    created_at: str
    source_model: str
    language: str
    embedding: List[float]
    tag_1: List[float]
    tag_2: List[float]
    tag_3: List[float]
    tags: List[str]


class MetadataValidator(ABC):
    """Metadata 驗證器抽象類別"""
    
    @abstractmethod
    def validate(self, metadata: EpisodeMetadata) -> bool:
        """驗證 metadata 完整性"""
        pass
    
    @abstractmethod
    def get_missing_fields(self, metadata: EpisodeMetadata) -> List[str]:
        """獲取缺失的欄位"""
        pass


class EpisodeMetadataValidator(MetadataValidator):
    """Episode Metadata 驗證器"""
    
    def __init__(self):
        self.required_fields = [
            'episode_id',
            'podcast_id', 
            'episode_title',
            'podcast_name',
            'author',
            'category'
        ]
    
    def validate(self, metadata: EpisodeMetadata) -> bool:
        """驗證 metadata 完整性"""
        try:
            for field in self.required_fields:
                value = getattr(metadata, field, None)
                if value is None or (isinstance(value, str) and not value.strip()):
                    logger.warning(f"metadata 欄位 {field} 為空或 None")
                    return False
            
            # 檢查 episode_id 和 podcast_id 不為 0
            if metadata.episode_id == 0 or metadata.podcast_id == 0:
                logger.warning(f"episode_id 或 podcast_id 為 0")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"檢查 metadata 完整性失敗: {e}")
            return False
    
    def get_missing_fields(self, metadata: EpisodeMetadata) -> List[str]:
        """獲取缺失的欄位"""
        missing_fields = []
        
        for field in self.required_fields:
            value = getattr(metadata, field, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing_fields.append(field)
        
        if metadata.episode_id == 0 or metadata.podcast_id == 0:
            missing_fields.extend(['episode_id', 'podcast_id'])
        
        return missing_fields


class TagProcessorManager:
    """標籤處理器管理器 - 使用統一標籤管理器"""
    
    def __init__(self, tag_csv_path: str):
        self.tag_csv_path = tag_csv_path
        self.tag_manager = UnifiedTagManager(tag_csv_path)
    
    def extract_tags(self, chunk_text: str) -> List[str]:
        """
        提取標籤（使用統一標籤管理器）
        
        Args:
            chunk_text: 文本內容
            
        Returns:
            標籤列表（最多3個）
        """
        return self.tag_manager.extract_tags(chunk_text)
    
    def extract_tags_with_details(self, chunk_text: str) -> TagExtractionResult:
        """
        提取標籤並返回詳細資訊
        
        Args:
            chunk_text: 文本內容
            
        Returns:
            標籤提取結果
        """
        return self.tag_manager.extract_tags_with_details(chunk_text)
    
    def get_extractor_status(self) -> Dict[str, bool]:
        """獲取提取器狀態"""
        return self.tag_manager.get_extractor_status()


class PipelineOrchestrator:
    """Pipeline 協調器 - 遵循 Google Clean Code Style"""
    
    def __init__(self, 
                 mongo_config: Dict[str, Any],
                 postgres_config: Dict[str, Any],
                 milvus_config: Dict[str, Any],
                 tag_csv_path: str = "TAG_info.csv",
                 embedding_model: str = "BAAI/bge-m3",
                 max_chunk_size: int = 1024,
                 batch_size: int = 100):
        """
        初始化 Pipeline 協調器
        
        Args:
            mongo_config: MongoDB 配置
            postgres_config: PostgreSQL 配置
            milvus_config: Milvus 配置
            tag_csv_path: 標籤 CSV 檔案路徑
            embedding_model: 嵌入模型名稱
            max_chunk_size: 最大分塊大小
            batch_size: 批次處理大小
        """
        self.mongo_config = mongo_config
        self.postgres_config = postgres_config
        self.milvus_config = milvus_config
        self.tag_csv_path = tag_csv_path
        self.embedding_model = embedding_model
        self.max_chunk_size = max_chunk_size
        self.batch_size = batch_size
        
        # 初始化核心組件
        self._initialize_core_components()
        
        # 初始化驗證器和管理器
        self.metadata_validator = EpisodeMetadataValidator()
        self.tag_processor_manager = TagProcessorManager(tag_csv_path)
    
    def _initialize_core_components(self):
        """初始化核心組件"""
        self.mongo_processor = MongoDBProcessor(self.mongo_config)
        self.postgres_mapper = PostgreSQLMapper(self.postgres_config)
        self.text_chunker = TextChunker(max_chunk_size=self.max_chunk_size)
        self.vector_processor = VectorProcessor(embedding_model=self.embedding_model)
        self.milvus_writer = MilvusWriter(self.milvus_config)
    
    def process_single_document(self, mongo_doc: MongoDocument) -> int:
        """
        處理單個文檔並返回處理的 chunk 數量
        
        Args:
            mongo_doc: MongoDB 文檔
            
        Returns:
            處理的 chunk 數量
        """
        try:
            processed_chunks = self._process_single_document_internal(mongo_doc)
            
            if processed_chunks:
                # 批次寫入 Milvus
                self._write_chunks_to_milvus(processed_chunks)
                return len(processed_chunks)
            else:
                return 0
                
        except Exception as e:
            logger.error(f"處理文檔 {mongo_doc.episode_id} 失敗: {e}")
            return 0
    
    def process_collection(self, mongo_collection: str, milvus_collection: str, 
                          limit: Optional[int] = None) -> Dict[str, Any]:
        """
        處理整個 MongoDB collection
        
        Args:
            mongo_collection: MongoDB collection 名稱
            milvus_collection: Milvus collection 名稱
            limit: 處理文檔數量限制
            
        Returns:
            處理結果統計
        """
        try:
            # 設定 Milvus collection 名稱
            self.milvus_config["collection_name"] = milvus_collection
            
            # 初始化錯誤記錄器
            error_logger = ErrorLogger()
            error_handler = ErrorHandler(error_logger)
            
            # 獲取 MongoDB 文檔
            documents = self.mongo_processor.process_collection(
                collection_name=mongo_collection,
                limit=limit
            )
            
            if not documents:
                logger.warning(f"Collection {mongo_collection} 沒有找到任何文檔")
                return {
                    "collection_name": mongo_collection,
                    "processed_documents": 0,
                    "processed_chunks": 0,
                    "status": "no_documents"
                }
            
            # 批次處理文檔
            total_chunks = 0
            processed_docs = 0
            
            for i, doc in enumerate(documents):
                try:
                    chunks_processed = self.process_single_document(doc)
                    if chunks_processed > 0:
                        processed_docs += 1
                        total_chunks += chunks_processed
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"已處理 {i + 1}/{len(documents)} 個文檔")
                        
                except Exception as e:
                    # 記錄錯誤
                    rss_id = self._extract_rss_id_from_collection(mongo_collection)
                    error_handler.handle_general_error(
                        collection_id=mongo_collection,
                        rss_id=rss_id,
                        title=doc.title if hasattr(doc, 'title') else '',
                        error=e,
                        stage="document_processing"
                    )
                    logger.error(f"處理文檔 {i + 1} 失敗: {e}")
                    continue
            
            # 儲存錯誤報告
            if error_logger.errors:
                error_reports = error_logger.save_errors()
                logger.warning(f"處理過程中發現 {len(error_logger.errors)} 個錯誤，報告已儲存至: {error_reports}")
            
            result = {
                "collection_name": mongo_collection,
                "milvus_collection": milvus_collection,
                "total_documents": len(documents),
                "processed_documents": processed_docs,
                "processed_chunks": total_chunks,
                "status": "completed",
                "error_count": len(error_logger.errors)
            }
            
            logger.info(f"Collection {mongo_collection} 處理完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"處理 collection {mongo_collection} 失敗: {e}")
            return {
                "collection_name": mongo_collection,
                "status": "failed",
                "error": str(e)
            }
    
    def _extract_rss_id_from_collection(self, collection_name: str) -> str:
        """從 collection 名稱提取 RSS ID"""
        import re
        match = re.search(r'RSS_(\d+)', collection_name)
        return match.group(1) if match else ""
    
    def _process_single_document_internal(self, mongo_doc: MongoDocument) -> List[ProcessedChunk]:
        """處理單個 MongoDB 文檔"""
        try:
            # 1. 文本切分
            chunks = self.text_chunker.split_text_into_chunks(
                text=mongo_doc.content,
                document_id=mongo_doc.episode_id
            )
            
            if not chunks:
                logger.warning(f"文檔 {mongo_doc.episode_id} 沒有產生任何 chunks")
                return []
            
            # 2. 獲取 PostgreSQL metadata
            episode_metadata = self._get_episode_metadata(mongo_doc)
            
            # 3. 驗證 metadata 完整性
            if not self._validate_metadata(episode_metadata, mongo_doc):
                raise Exception(f"Metadata 不完整，無法處理文檔: {mongo_doc.episode_id}")
            
            # 4. 處理每個 chunk
            processed_chunks = []
            for chunk in chunks:
                processed_chunk = self._process_single_chunk(chunk, episode_metadata, mongo_doc)
                if processed_chunk:
                    processed_chunks.append(processed_chunk)
            
            return processed_chunks
            
        except Exception as e:
            logger.error(f"處理文檔 {mongo_doc.episode_id} 失敗: {e}")
            return []
    
    def _validate_metadata(self, metadata: Optional[EpisodeMetadata], mongo_doc: MongoDocument) -> bool:
        """驗證 metadata 完整性"""
        if not metadata:
            logger.error(f"找不到文檔 {mongo_doc.episode_id} 的 metadata")
            return False
        
        if not self.metadata_validator.validate(metadata):
            missing_fields = self.metadata_validator.get_missing_fields(metadata)
            logger.error(f"Metadata 不完整，缺失欄位: {missing_fields}")
            return False
        
        return True
    
    def _get_episode_metadata(self, mongo_doc: MongoDocument) -> Optional[EpisodeMetadata]:
        """獲取 episode metadata"""
        try:
            # 解析 file 欄位來提取 RSS_ID 和 episode 資訊
            if mongo_doc.file_path:
                rss_id, episode_title = self._parse_file_field(mongo_doc.file_path)
                
                if rss_id and episode_title:
                    # 根據 RSS_ID 和 episode_title 查詢 PostgreSQL
                    metadata = self.postgres_mapper.search_episode_by_rss_and_title(
                        rss_id=rss_id,
                        episode_title=episode_title
                    )
                    if metadata:
                        return metadata
            
            # 如果找不到，返回預設值
            logger.warning(f"找不到文檔 {mongo_doc.episode_id} 的 metadata，使用預設值")
            return None
            
        except Exception as e:
            logger.error(f"獲取 episode metadata 失敗: {e}")
            return None
    
    def _parse_file_field(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """解析 file 欄位，提取 RSS_ID 和 episode_title"""
        try:
            import re
            
            # 移除副檔名
            file_path = re.sub(r'\.(mp3|wav|m4a|aac)$', '', file_path, flags=re.IGNORECASE)
            
            # 解析格式: RSS_{RSS_ID}_podcast_{PODCAST_ID}_EP{EPISODE_NUMBER} {EPISODE_TITLE}
            # 支援多種分隔符和格式
            patterns = [
                r'RSS_(\d+)_podcast_\d+_EP\d+\s*(.+)',  # 標準格式
                r'RSS_(\d+)_podcast_\d+_(.+)',  # 無 EP 前綴
                r'RSS_(\d+)_podcast_\d+_EP\d+([^_]+)',  # 下劃線分隔
            ]
            
            for pattern in patterns:
                match = re.match(pattern, file_path)
                if match:
                    break
            
            if match:
                rss_id = match.group(1)
                episode_title = match.group(2).strip()
                return rss_id, episode_title
            
            return None, None
            
        except Exception as e:
            logger.error(f"解析檔案路徑失敗: {file_path}, 錯誤: {e}")
            return None, None
    
    def _process_single_chunk(self, chunk: TextChunk, 
                             episode_metadata: Optional[EpisodeMetadata],
                             mongo_doc: MongoDocument) -> Optional[ProcessedChunk]:
        """處理單個文本塊"""
        try:
            # 1. 生成主要嵌入向量
            embedding = self.vector_processor.generate_single_embedding(chunk.chunk_text)
            
            # 2. 標籤處理
            tags = self.tag_processor_manager.extract_tags(chunk.chunk_text)
            
            # 3. 生成標籤向量
            tag_vectors = self._generate_tag_vectors(tags, embedding)
            
            # 4. 準備 metadata
            metadata = self._prepare_metadata(episode_metadata, mongo_doc)
            
            # 5. 建立 ProcessedChunk
            processed_chunk = ProcessedChunk(
                chunk_id=chunk.chunk_id,
                chunk_index=chunk.chunk_index,
                chunk_text=chunk.chunk_text,
                chunk_length=chunk.chunk_length,
                episode_id=metadata.get('episode_id', 0),
                podcast_id=metadata.get('podcast_id', 0),
                episode_title=metadata.get('episode_title', ''),
                podcast_name=metadata.get('podcast_name', ''),
                author=metadata.get('author', ''),
                category=metadata.get('category', ''),
                created_at=metadata.get('created_at', ''),
                source_model=self.embedding_model,
                language=metadata.get('language', 'zh'),
                embedding=embedding.tolist(),
                tag_1=tag_vectors[0].tolist(),
                tag_2=tag_vectors[1].tolist(),
                tag_3=tag_vectors[2].tolist(),
                tags=tags
            )
            
            return processed_chunk
            
        except Exception as e:
            logger.error(f"處理 chunk {chunk.chunk_id} 失敗: {e}")
            return None
    
    def _generate_tag_vectors(self, tags: List[str], 
                            default_embedding) -> List:
        """生成標籤向量"""
        tag_vectors = []
        
        for i in range(3):  # 最多 3 個標籤向量
            if i < len(tags):
                # 為標籤生成向量
                tag_vector = self.vector_processor.generate_single_embedding(tags[i])
                tag_vectors.append(tag_vector)
            else:
                # 使用預設向量
                tag_vectors.append(default_embedding)
        
        return tag_vectors
    
    def _prepare_metadata(self, episode_metadata: Optional[EpisodeMetadata],
                         mongo_doc: MongoDocument) -> Dict[str, Any]:
        """準備 metadata"""
        if episode_metadata:
            return {
                'episode_id': episode_metadata.episode_id,
                'podcast_id': episode_metadata.podcast_id,
                'episode_title': episode_metadata.episode_title,
                'podcast_name': episode_metadata.podcast_name,
                'author': episode_metadata.author,
                'category': episode_metadata.category,
                'created_at': episode_metadata.created_at.isoformat() if episode_metadata.created_at and hasattr(episode_metadata.created_at, 'isoformat') else str(episode_metadata.created_at) if episode_metadata.created_at else '',
                'language': episode_metadata.languages or 'zh'
            }
        else:
            # 使用預設值
            return {
                'episode_id': 0,
                'podcast_id': 0,
                'episode_title': mongo_doc.title or '',
                'podcast_name': '',
                'author': '',
                'category': '',
                'created_at': datetime.now().isoformat(),
                'language': 'zh'
            }
    
    def _write_chunks_to_milvus(self, processed_chunks: List[ProcessedChunk]) -> None:
        """將處理後的 chunks 寫入 Milvus"""
        try:
            if not processed_chunks:
                return
            
            # 將 ProcessedChunk 轉換為字典列表
            data_list = []
            for chunk in processed_chunks:
                chunk_dict = {
                    "chunk_id": chunk.chunk_id,
                    "chunk_index": chunk.chunk_index,
                    "episode_id": chunk.episode_id,
                    "podcast_id": chunk.podcast_id,
                    "episode_title": chunk.episode_title,
                    "chunk_text": chunk.chunk_text,
                    "embedding": chunk.embedding,
                    "language": chunk.language,
                    "created_at": chunk.created_at,
                    "source_model": chunk.source_model,
                    "podcast_name": chunk.podcast_name,
                    "author": chunk.author,
                    "category": chunk.category,
                    "tag_1": chunk.tag_1,
                    "tag_2": chunk.tag_2,
                    "tag_3": chunk.tag_3
                }
                data_list.append(chunk_dict)
            
            # 使用批次插入方法
            inserted_count = self.milvus_writer.batch_insert(
                self.milvus_config["collection_name"], 
                data_list,
                batch_size=len(data_list)  # 一次性插入所有 chunks
            )
            
            logger.info(f"成功寫入 {inserted_count} 個 chunks 到 Milvus")
            
        except Exception as e:
            logger.error(f"寫入 Milvus 失敗: {e}")
            raise
    
    def close(self) -> None:
        """關閉所有連接"""
        try:
            if hasattr(self.mongo_processor, 'disconnect'):
                self.mongo_processor.disconnect()
            if hasattr(self.postgres_mapper, 'close'):
            self.postgres_mapper.close()
            if hasattr(self.milvus_writer, 'close'):
            self.milvus_writer.close()
            logger.info("所有連接已關閉")
        except Exception as e:
            logger.error(f"關閉連接時發生錯誤: {e}") 