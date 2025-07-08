#!/usr/bin/env python3
"""
統一文本處理工具模組

提供給所有模組使用的文本處理功能：
- 文本分塊 (Chunking)
- 標籤處理 (Tagging)
- 文本清理和標準化
- 嵌入向量處理

符合 OOP 原則和 Google Clean Code 標準
作者: Podwise Team
版本: 1.0.0
"""

import re
import logging
from typing import List, Dict, Any, Optional, Protocol, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from pathlib import Path
import pandas as pd
import numpy as np

from .common_utils import normalize_text, create_logger

logger = create_logger(__name__)


@dataclass
class TextChunk:
    """文本分塊數據類"""
    chunk_id: str
    chunk_index: int
    chunk_text: str
    start_pos: int
    end_pos: int
    metadata: Dict[str, Any]
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class TagInfo:
    """標籤資訊數據類"""
    tag_name: str
    synonyms: List[str]
    category: str
    weight: float = 1.0
    description: str = ""


class TextChunker(Protocol):
    """文本分塊器協議"""
    
    def chunk_text(self, text: str, **kwargs) -> List[TextChunk]:
        """分塊文本"""
        ...


class TagExtractor(Protocol):
    """標籤提取器協議"""
    
    def extract_tags(self, text: str) -> List[str]:
        """提取標籤"""
        ...


class BaseTextChunker(ABC):
    """基礎文本分塊器"""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    @abstractmethod
    def chunk_text(self, text: str, **kwargs) -> List[TextChunk]:
        """分塊文本的抽象方法"""
        pass
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        
        # 移除多餘空格
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:]', '', text)
        
        return text.strip()


class SemanticTextChunker(BaseTextChunker):
    """語義文本分塊器"""
    
    def chunk_text(self, text: str, **kwargs) -> List[TextChunk]:
        """基於語義的文本分塊"""
        if not text:
            return []
        
        text = self._clean_text(text)
        chunks = []
        
        # 按段落分割
        paragraphs = text.split('\n\n')
        current_chunk = ""
        chunk_index = 0
        start_pos = 0
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) <= self.chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk:
                    chunk = TextChunk(
                        chunk_id=f"chunk_{chunk_index}",
                        chunk_index=chunk_index,
                        chunk_text=current_chunk.strip(),
                        start_pos=start_pos,
                        end_pos=start_pos + len(current_chunk),
                        metadata=kwargs.get('metadata', {})
                    )
                    chunks.append(chunk)
                    
                    start_pos += len(current_chunk) - self.overlap
                    chunk_index += 1
                
                current_chunk = paragraph + "\n\n"
        
        # 處理最後一個分塊
        if current_chunk:
            chunk = TextChunk(
                chunk_id=f"chunk_{chunk_index}",
                chunk_index=chunk_index,
                chunk_text=current_chunk.strip(),
                start_pos=start_pos,
                end_pos=start_pos + len(current_chunk),
                metadata=kwargs.get('metadata', {})
            )
            chunks.append(chunk)
        
        return chunks


class UnifiedTagProcessor:
    """統一標籤處理器"""
    
    def __init__(self, tag_csv_path: Optional[str] = None):
        self.tag_info_map: Dict[str, TagInfo] = {}
        self.synonym_map: Dict[str, str] = {}
        
        if tag_csv_path and Path(tag_csv_path).exists():
            self._load_tag_info(tag_csv_path)
    
    def _load_tag_info(self, csv_path: str):
        """載入標籤資訊"""
        try:
            df = pd.read_csv(csv_path)
            
            for _, row in df.iterrows():
                tag_name = str(row.get('tag_name', ''))
                synonyms_str = str(row.get('synonyms', ''))
                synonyms = synonyms_str.split(',') if synonyms_str else []
                category = str(row.get('category', ''))
                weight = float(row.get('weight', 1.0)) if row.get('weight') is not None else 1.0
                description = str(row.get('description', ''))
                
                if not tag_name:
                    continue
                
                tag_info = TagInfo(
                    tag_name=tag_name,
                    synonyms=[s.strip() for s in synonyms if s.strip()],
                    category=category,
                    weight=weight,
                    description=description
                )
                
                self.tag_info_map[tag_name] = tag_info
                
                # 建立同義詞映射
                for synonym in tag_info.synonyms:
                    if synonym:
                        self.synonym_map[synonym.lower()] = tag_name
                        
        except Exception as e:
            logger.error(f"載入標籤資訊失敗: {e}")
    
    def extract_tags(self, text: str, max_tags: int = 5) -> List[str]:
        """提取文本標籤"""
        if not text:
            return []
        
        text_lower = normalize_text(text)
        found_tags = []
        
        # 精確匹配標籤
        for tag_name, tag_info in self.tag_info_map.items():
            if tag_name.lower() in text_lower:
                found_tags.append((tag_name, tag_info.weight))
                continue
            
            # 匹配同義詞
            for synonym in tag_info.synonyms:
                if synonym.lower() in text_lower:
                    found_tags.append((tag_name, tag_info.weight))
                    break
        
        # 按權重排序並返回前 max_tags 個
        found_tags.sort(key=lambda x: x[1], reverse=True)
        return [tag for tag, _ in found_tags[:max_tags]]
    
    def get_tag_info(self, tag_name: str) -> Optional[TagInfo]:
        """獲取標籤資訊"""
        return self.tag_info_map.get(tag_name)
    
    def get_tags_by_category(self, category: str) -> List[str]:
        """根據類別獲取標籤"""
        return [
            tag_name for tag_name, tag_info in self.tag_info_map.items()
            if tag_info.category == category
        ]


class TextProcessor:
    """統一文本處理器"""
    
    def __init__(self, 
                 chunker: Optional[TextChunker] = None,
                 tag_processor: Optional[UnifiedTagProcessor] = None):
        self.chunker = chunker if chunker is not None else SemanticTextChunker()
        self.tag_processor = tag_processor if tag_processor is not None else UnifiedTagProcessor()
    
    def process_text(self, text: str, **kwargs) -> List[TextChunk]:
        """處理文本：分塊 + 標籤提取"""
        chunks = self.chunker.chunk_text(text, **kwargs)
        
        for chunk in chunks:
            chunk.tags = self.tag_processor.extract_tags(chunk.chunk_text)
        
        return chunks
    
    def process_document(self, 
                        document: Dict[str, Any],
                        text_field: str = 'content') -> List[TextChunk]:
        """處理文檔"""
        text = document.get(text_field, '')
        if not text:
            return []
        
        metadata = {k: v for k, v in document.items() if k != text_field}
        
        return self.process_text(text, metadata=metadata)


class EmbeddingProcessor:
    """嵌入向量處理器"""
    
    def __init__(self, model_name: str = "text2vec-base-chinese"):
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """載入嵌入模型"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"載入嵌入模型: {self.model_name}")
        except ImportError:
            logger.warning("sentence_transformers 未安裝，嵌入功能不可用")
            self.model = None
        except Exception as e:
            logger.error(f"載入嵌入模型失敗: {e}")
            self.model = None
    
    def encode_texts(self, texts: List[str]) -> Optional[np.ndarray]:
        """編碼文本為向量"""
        if not self.model or not texts:
            return None
        
        try:
            embeddings = self.model.encode(texts)
            return embeddings
        except Exception as e:
            logger.error(f"文本編碼失敗: {e}")
            return None
    
    def encode_chunks(self, chunks: List[TextChunk]) -> List[TextChunk]:
        """為文本塊編碼向量"""
        if not chunks:
            return chunks
        
        texts = [chunk.chunk_text for chunk in chunks]
        embeddings = self.encode_texts(texts)
        
        if embeddings is not None:
            for i, chunk in enumerate(chunks):
                chunk.metadata['embedding'] = embeddings[i].tolist()
        
        return chunks


def create_text_processor(tag_csv_path: Optional[str] = None,
                         chunk_size: int = 1000,
                         overlap: int = 200) -> TextProcessor:
    """創建文本處理器工廠函數"""
    chunker = SemanticTextChunker(chunk_size=chunk_size, overlap=overlap)
    tag_processor = UnifiedTagProcessor(tag_csv_path=tag_csv_path)
    
    return TextProcessor(chunker=chunker, tag_processor=tag_processor)


# 導出主要類別和函數
__all__ = [
    'TextChunk',
    'TagInfo', 
    'TextChunker',
    'TagExtractor',
    'BaseTextChunker',
    'SemanticTextChunker',
    'UnifiedTagProcessor',
    'TextProcessor',
    'EmbeddingProcessor',
    'create_text_processor'
] 