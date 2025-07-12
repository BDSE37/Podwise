#!/usr/bin/env python3
"""
Utils 工具主入口

統一包裝所有工具功能，支援 OOP 調用。
符合 Google Clean Code 原則。
"""

import os
import logging
import asyncio
import json
import re
import functools
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Protocol, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime

# ==================== 基礎工具類別 ====================

class DictToAttrRecursive(dict):
    """統一的字典到屬性轉換類別"""
    
    def __init__(self, input_dict: Dict[str, Any]):
        super().__init__(input_dict)
        for key, value in input_dict.items():
            if isinstance(value, dict):
                value = DictToAttrRecursive(value)
            self[key] = value
            setattr(self, key, value)

    def __getattr__(self, item: str) -> Any:
        try:
            return self[item]
        except KeyError:
            raise AttributeError(f"Attribute {item} not found")

    def __setattr__(self, key: str, value: Any) -> None:
        if isinstance(value, dict):
            value = DictToAttrRecursive(value)
        super(DictToAttrRecursive, self).__setitem__(key, value)
        super().__setattr__(key, value)

    def __delattr__(self, item: str) -> None:
        try:
            del self[item]
        except KeyError:
            raise AttributeError(f"Attribute {item} not found")

@dataclass
class ServiceConfig:
    """服務配置資料類別"""
    service_name: str
    host: str = "localhost"
    port: int = 8000
    timeout: int = 30
    retry_count: int = 3
    log_level: str = "INFO"
    config: Optional[Dict[str, Any]] = None

@dataclass
class ServiceResponse:
    """服務回應資料類別"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    status_code: int = 200
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

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

# ==================== 通用工具函數 ====================

def clean_path(path_str: str) -> str:
    """統一的路徑清理函數"""
    if not path_str:
        return ""
    
    if path_str.endswith(("\\", "/")):
        return clean_path(path_str[0:-1])
    
    path_str = path_str.replace("/", os.sep).replace("\\", os.sep)
    return path_str.strip(" '\n\"\u202a")

def normalize_text(text: str) -> str:
    """標準化文本，用於去重比較"""
    if not text:
        return ""
    
    text = text.lower()
    text = " ".join(text.split())
    text = re.sub(r'[^\w\s]', '', text)
    return text

def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """安全獲取字典值"""
    return dictionary.get(key, default)

def ensure_directory(path: str) -> bool:
    """確保目錄存在"""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"創建目錄失敗: {path}, 錯誤: {e}")
        return False

def validate_file_path(file_path: str) -> bool:
    """驗證檔案路徑"""
    try:
        path = Path(file_path)
        return path.exists() and path.is_file()
    except Exception:
        return False

def get_file_extension(file_path: str) -> str:
    """獲取檔案副檔名"""
    try:
        return Path(file_path).suffix.lstrip('.')
    except Exception:
        return ""

def format_file_size(size_bytes: int) -> str:
    """格式化檔案大小"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"

def create_logger(name: str, level: str = "INFO") -> logging.Logger:
    """創建統一的日誌記錄器"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """重試裝飾器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(delay)
            if last_exception:
                raise last_exception
            else:
                raise Exception("重試失敗")
        return wrapper
    return decorator

def is_empty(*items: Any) -> bool:
    """檢查是否為空"""
    for item in items:
        if item is None:
            return True
        if isinstance(item, (str, list, dict, tuple)) and not item:
            return True
    return False

def remove_duplicates(items: list, key_func=None) -> list:
    """移除重複項目"""
    seen = set()
    result = []
    for item in items:
        key = key_func(item) if key_func else item
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result

# ==================== 核心服務類別 ====================

class BaseService(ABC):
    """基礎服務抽象類別"""
    
    def __init__(self, service_name: str, config: Optional[Dict[str, Any]] = None):
        self.service_name = service_name
        self.config = config or {}
        self.logger = self._setup_logger()
        self.is_initialized = False
        self.start_time = datetime.now()
        self.health_status = "unknown"
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(f"{self.service_name}_service")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    @abstractmethod
    async def initialize(self) -> bool:
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        pass
    
    async def start(self) -> bool:
        try:
            self.logger.info(f"正在啟動 {self.service_name} 服務...")
            success = await self.initialize()
            if success:
                self.is_initialized = True
                self.health_status = "healthy"
                self.logger.info(f"{self.service_name} 服務啟動成功")
            else:
                self.health_status = "unhealthy"
                self.logger.error(f"{self.service_name} 服務啟動失敗")
            return success
        except Exception as e:
            self.health_status = "error"
            self.logger.error(f"啟動 {self.service_name} 服務時發生錯誤: {str(e)}")
            return False
    
    async def stop(self) -> bool:
        try:
            self.logger.info(f"正在停止 {self.service_name} 服務...")
            await self._cleanup()
            self.is_initialized = False
            self.health_status = "stopped"
            self.logger.info(f"{self.service_name} 服務已停止")
            return True
        except Exception as e:
            self.logger.error(f"停止 {self.service_name} 服務時發生錯誤: {str(e)}")
            return False
    
    async def _cleanup(self):
        pass
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "is_initialized": self.is_initialized,
            "health_status": self.health_status,
            "start_time": self.start_time.isoformat(),
            "uptime": str(datetime.now() - self.start_time),
            "config": self.config
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        try:
            self.config.update(new_config)
            self.logger.info(f"已更新 {self.service_name} 配置")
            return True
        except Exception as e:
            self.logger.error(f"更新配置時發生錯誤: {str(e)}")
            return False
    
    def log_operation(self, operation: str, details: Optional[Dict[str, Any]] = None):
        log_data = {
            "operation": operation,
            "service": self.service_name,
            "timestamp": datetime.now().isoformat()
        }
        if details:
            log_data.update(details)
        self.logger.info(f"操作記錄: {json.dumps(log_data, ensure_ascii=False)}")

class ServiceManager:
    """服務管理器"""
    
    def __init__(self):
        self.services: Dict[str, BaseService] = {}
        self.logger = logging.getLogger("service_manager")
    
    def register_service(self, service: BaseService) -> bool:
        try:
            self.services[service.service_name] = service
            self.logger.info(f"已註冊服務: {service.service_name}")
            return True
        except Exception as e:
            self.logger.error(f"註冊服務失敗: {str(e)}")
            return False
    
    def unregister_service(self, service_name: str) -> bool:
        try:
            if service_name in self.services:
                del self.services[service_name]
                self.logger.info(f"已取消註冊服務: {service_name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"取消註冊服務失敗: {str(e)}")
            return False
    
    async def start_all_services(self) -> Dict[str, bool]:
        results = {}
        for service_name, service in self.services.items():
            try:
                results[service_name] = await service.start()
            except Exception as e:
                self.logger.error(f"啟動服務 {service_name} 時發生錯誤: {str(e)}")
                results[service_name] = False
        return results
    
    async def stop_all_services(self) -> Dict[str, bool]:
        results = {}
        for service_name, service in self.services.items():
            try:
                results[service_name] = await service.stop()
            except Exception as e:
                self.logger.error(f"停止服務 {service_name} 時發生錯誤: {str(e)}")
                results[service_name] = False
        return results
    
    def get_service(self, service_name: str) -> Optional[BaseService]:
        return self.services.get(service_name)
    
    def get_all_services_status(self) -> Dict[str, Dict[str, Any]]:
        return {
            service_name: service.get_status()
            for service_name, service in self.services.items()
        }
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        results = {}
        for service_name, service in self.services.items():
            try:
                results[service_name] = await service.health_check()
            except Exception as e:
                self.logger.error(f"健康檢查服務 {service_name} 時發生錯誤: {str(e)}")
                results[service_name] = {"status": "error", "error": str(e)}
        return results

class ModelService(BaseService):
    """模型服務基礎類別"""
    
    def __init__(self, service_name: str, model_path: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(service_name, config)
        self.model_path = model_path
        self.model = None
        self.model_version = "1.0.0"
        self.model_metadata = {}
    
    async def load_model(self) -> bool:
        try:
            self.logger.info(f"正在載入模型: {self.model_path}")
            # 實際模型載入邏輯
            return True
        except Exception as e:
            self.logger.error(f"載入模型失敗: {e}")
            return False
    
    async def initialize(self) -> bool:
        return await self.load_model()
    
    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self.model else "unhealthy",
            "model_loaded": self.model is not None,
            "model_version": self.model_version
        }
    
    async def save_model(self, version: Optional[str] = None) -> bool:
        try:
            if version:
                self.model_version = version
            self.logger.info(f"已保存模型版本: {self.model_version}")
            return True
        except Exception as e:
            self.logger.error(f"保存模型失敗: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_path": self.model_path,
            "model_version": self.model_version,
            "model_metadata": self.model_metadata,
            "is_loaded": self.model is not None
        }

# ==================== 文本處理類別 ====================

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
        
        text = re.sub(r'\s+', ' ', text)
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
                weight_value = row.get('weight')
                weight = float(weight_value) if weight_value is not None else 1.0
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
                
                for synonym in tag_info.synonyms:
                    if synonym:
                        self.synonym_map[synonym.lower()] = tag_name
                        
        except Exception as e:
            logging.error(f"載入標籤資訊失敗: {e}")
    
    def extract_tags(self, text: str, max_tags: int = 5) -> List[str]:
        """提取文本標籤"""
        if not text:
            return []
        
        text_lower = normalize_text(text)
        found_tags = []
        
        # 檢查標籤和同義詞
        for tag_name, tag_info in self.tag_info_map.items():
            if tag_name.lower() in text_lower:
                found_tags.append(tag_name)
            else:
                for synonym in tag_info.synonyms:
                    if synonym.lower() in text_lower:
                        found_tags.append(tag_name)
                        break
        
        # 按權重排序並限制數量
        found_tags = sorted(found_tags, 
                          key=lambda x: self.tag_info_map.get(x, TagInfo("", [], "", 0.0)).weight,
                          reverse=True)[:max_tags]
        
        return found_tags
    
    def get_tag_info(self, tag_name: str) -> Optional[TagInfo]:
        """獲取標籤資訊"""
        return self.tag_info_map.get(tag_name)
    
    def get_tags_by_category(self, category: str) -> List[str]:
        """按類別獲取標籤"""
        return [
            tag_name for tag_name, tag_info in self.tag_info_map.items()
            if tag_info.category == category
        ]

class TextProcessor:
    """統一文本處理器"""
    
    def __init__(self, 
                 chunker: Optional[TextChunker] = None,
                 tag_processor: Optional[UnifiedTagProcessor] = None):
        self.chunker = chunker or SemanticTextChunker()
        self.tag_processor = tag_processor
    
    def process_text(self, text: str, **kwargs) -> List[TextChunk]:
        """處理文本"""
        chunks = self.chunker.chunk_text(text, **kwargs)
        
        if self.tag_processor:
            for chunk in chunks:
                chunk.tags = self.tag_processor.extract_tags(chunk.chunk_text)
        
        return chunks
    
    def process_document(self, 
                        document: Dict[str, Any],
                        text_field: str = 'content') -> List[TextChunk]:
        """處理文檔"""
        text = document.get(text_field, '')
        metadata = {k: v for k, v in document.items() if k != text_field}
        return self.process_text(text, metadata=metadata)

class EmbeddingProcessor:
    """嵌入向量處理器"""
    
    def __init__(self, model_name: str = "text2vec-base-chinese"):
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """載入模型"""
        try:
            # 實際模型載入邏輯
            logging.info(f"載入嵌入模型: {self.model_name}")
        except Exception as e:
            logging.error(f"載入嵌入模型失敗: {e}")
    
    def encode_texts(self, texts: List[str]) -> Optional[np.ndarray]:
        """編碼文本列表"""
        if not self.model or not texts:
            return None
        
        try:
            # 實際編碼邏輯
            return np.random.rand(len(texts), 768)  # 模擬
    except Exception as e:
            logging.error(f"文本編碼失敗: {e}")
            return None
    
    def encode_chunks(self, chunks: List[TextChunk]) -> List[TextChunk]:
        """編碼文本分塊"""
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
    tag_processor = UnifiedTagProcessor(tag_csv_path) if tag_csv_path else None
    
    return TextProcessor(chunker=chunker, tag_processor=tag_processor)

# ==================== 統一工具入口 ====================

class CommonUtils:
    """通用工具類別"""
    
    def __init__(self):
        self.logger = create_logger("common_utils")
    
    def clean_path(self, path_str: str) -> str:
        return clean_path(path_str)
    
    def normalize_text(self, text: str) -> str:
        return normalize_text(text)
    
    def safe_get(self, dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
        return safe_get(dictionary, key, default)
    
    def ensure_directory(self, path: str) -> bool:
        return ensure_directory(path)
    
    def validate_file_path(self, file_path: str) -> bool:
        return validate_file_path(file_path)
    
    def get_file_extension(self, file_path: str) -> str:
        return get_file_extension(file_path)
    
    def format_file_size(self, size_bytes: int) -> str:
        return format_file_size(size_bytes)
    
    def create_logger(self, name: str, level: str = "INFO") -> logging.Logger:
        return create_logger(name, level)
    
    def is_empty(self, *items: Any) -> bool:
        return is_empty(*items)
    
    def remove_duplicates(self, items: list, key_func=None) -> list:
        return remove_duplicates(items, key_func)

class CoreServices:
    """核心服務類別"""
    
    def __init__(self):
        self.service_manager = ServiceManager()
        self.logger = create_logger("core_services")
    
    def create_service_config(self, service_name: str, **kwargs) -> ServiceConfig:
        return ServiceConfig(service_name=service_name, **kwargs)
    
    def create_service_response(self, success: bool, **kwargs) -> ServiceResponse:
        return ServiceResponse(success=success, **kwargs)
    
    def register_service(self, service: BaseService) -> bool:
        return self.service_manager.register_service(service)
    
    def get_service(self, service_name: str) -> Optional[BaseService]:
        return self.service_manager.get_service(service_name)
    
    async def start_all_services(self) -> Dict[str, bool]:
        return await self.service_manager.start_all_services()
    
    async def stop_all_services(self) -> Dict[str, bool]:
        return await self.service_manager.stop_all_services()
    
    def get_all_services_status(self) -> Dict[str, Dict[str, Any]]:
        return self.service_manager.get_all_services_status()
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        return await self.service_manager.health_check_all()

class TextProcessing:
    """文本處理類別"""
    
    def __init__(self, tag_csv_path: Optional[str] = None):
        self.tag_csv_path = tag_csv_path
        self.text_processor = create_text_processor(tag_csv_path)
        self.embedding_processor = EmbeddingProcessor()
        self.logger = create_logger("text_processing")
    
    def process_text(self, text: str, **kwargs) -> List[TextChunk]:
        return self.text_processor.process_text(text, **kwargs)
    
    def process_document(self, document: Dict[str, Any], text_field: str = 'content') -> List[TextChunk]:
        return self.text_processor.process_document(document, text_field)
    
    def extract_tags(self, text: str, max_tags: int = 5) -> List[str]:
        if self.text_processor.tag_processor:
            return self.text_processor.tag_processor.extract_tags(text, max_tags)
        return []
    
    def encode_texts(self, texts: List[str]) -> Optional[np.ndarray]:
        return self.embedding_processor.encode_texts(texts)
    
    def encode_chunks(self, chunks: List[TextChunk]) -> List[TextChunk]:
        return self.embedding_processor.encode_chunks(chunks)
    
    def get_tag_info(self, tag_name: str) -> Optional[TagInfo]:
        if self.text_processor.tag_processor:
            return self.text_processor.tag_processor.get_tag_info(tag_name)
        return None
    
    def get_tags_by_category(self, category: str) -> List[str]:
        if self.text_processor.tag_processor:
            return self.text_processor.tag_processor.get_tags_by_category(category)
        return []

class Utils:
    """統一工具 OOP 入口"""
    
    def __init__(self, tag_csv_path: Optional[str] = None):
        self.common = CommonUtils()
        self.core = CoreServices()
        self.text = TextProcessing(tag_csv_path)
        self.logger = create_logger("utils")
    
    def get_dict_to_attr(self, input_dict: Dict[str, Any]) -> DictToAttrRecursive:
        """獲取字典到屬性轉換器"""
        return DictToAttrRecursive(input_dict)
    
    def retry_on_failure(self, max_retries: int = 3, delay: float = 1.0):
        """重試裝飾器"""
        return retry_on_failure(max_retries, delay)

# 全域工具實例
utils = Utils() 