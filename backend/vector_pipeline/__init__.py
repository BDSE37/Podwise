"""
Podwise Vector Pipeline 模組
整合文本處理、智能分塊、語意標籤選擇和向量化功能

主要組件:
- TextProcessor: 文本處理器，負責文本分塊、標籤提取和向量化
- VectorPipeline: 向量化管道，整合文本處理和 Milvus 向量資料庫操作

使用範例:
    from vector_pipeline import TextProcessor, VectorPipeline
    
    # 使用文本處理器
    processor = TextProcessor(mongo_config, postgres_config)
    chunks = processor.split_text_into_chunks(text)
    tags = processor.extract_tags_from_chunk(chunk)
    
    # 使用向量化管道
    pipeline = VectorPipeline(mongo_config, milvus_config, postgres_config)
    stats = pipeline.process_and_vectorize(collection_name, mongo_collection)
    results = pipeline.search_similar(query_text, collection_name)
"""

from .text_processor import TextProcessor
from .vector_pipeline import VectorPipeline

__version__ = "1.0.0"
__author__ = "Podwise Team"
__description__ = "整合文本處理和向量化功能的模組"

__all__ = [
    "TextProcessor",
    "VectorPipeline"
] 