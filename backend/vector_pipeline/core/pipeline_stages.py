#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量處理管線的四個階段處理器

Author: Podri Team
License: MIT
"""

import json
import logging
import uuid
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime

import pymongo
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 引用 data_cleaning 的檔名清理功能
try:
    from data_cleaning.core.mongo_cleaner import MongoCleaner
    mongo_cleaner = MongoCleaner()
    def clean_filename(filename: str) -> str:
        """使用 data_cleaning 的檔名清理功能"""
        return mongo_cleaner._clean_filename(filename)
except ImportError:
    logger.warning("無法載入 data_cleaning 模組，使用簡化版檔名清理")
    def clean_filename(filename: str) -> str:
        """簡化版檔名清理（fallback）"""
        if not filename:
            return ""
        # 移除表情符號和特殊字元，保留中文、英文、數字、底線、連字號、點號
        cleaned = re.sub(r'[^\u4e00-\u9fff\w\s\-_\.]', '', filename)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned


@dataclass
class ChunkData:
    """Chunk 資料結構"""
    chunk_id: str
    episode_id: str
    chunk_index: int
    content: str
    original_filename: str
    collection_name: str
    created_at: str


@dataclass
class ProcessedChunkData(ChunkData):
    """處理後的 Chunk 資料結構"""
    cleaned_content: str
    tags: List[str]
    tag_sources: Dict[str, List[str]]  # 標籤來源分類


class BaseStageProcessor(ABC):
    """基礎階段處理器"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.stage_name = self.__class__.__name__
    
    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """處理資料的抽象方法"""
        pass
    
    def save_results(self, results: Any, filename: str) -> str:
        """儲存結果到檔案"""
        output_path = self.data_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"{self.stage_name} 結果已儲存到: {output_path}")
        return str(output_path)
    
    def load_results(self, filename: str) -> Any:
        """從檔案載入結果"""
        input_path = self.data_dir / filename
        if not input_path.exists():
            raise FileNotFoundError(f"找不到檔案: {input_path}")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)


class Stage1TextChunker(BaseStageProcessor):
    """階段 1：文本切斷處理器"""
    
    def __init__(self, output_dir: str = "data/stage1_chunking"):
        super().__init__(output_dir)
        self.stage_name = "文本切斷"
    
    def split_text_into_chunks(self, text: str) -> List[str]:
        """將文本切斷成 chunks - 使用統一的 TextChunker"""
        from .text_chunker import TextChunker
        
        if not text or not text.strip():
            return []
        
        # 使用統一的 TextChunker
        chunker = TextChunker(max_chunk_size=1024, overlap_size=100)
        text_chunks = chunker.split_text_into_chunks(text, "temp_doc_id")
        
        # 轉換為簡單的字符串列表
        return [chunk.chunk_text for chunk in text_chunks]
    
    def process_document(self, doc: Dict[str, Any], collection_name: str) -> Dict[str, Any]:
        """處理單個文件"""
        # 獲取檔名
        filename = self._get_filename(doc)
        
        # 獲取文本內容
        text_content = doc.get('text', '')
        if not text_content:
            logger.warning(f"文件 {doc.get('_id')} 沒有內容")
            return {}
        
        # 切斷文本
        text_chunks = self.split_text_into_chunks(text_content)
        
        if not text_chunks:
            logger.warning(f"文件 {doc.get('_id')} 切斷後沒有 chunks")
            return {}
        
        # 建立 chunk 資料
        chunk_data = []
        for index, chunk_text in enumerate(text_chunks):
            chunk_info = {
                'chunk_text': chunk_text,
                'chunk_id': str(uuid.uuid4()),  # 唯一 UUID
                'chunk_index': index,  # 該段在該 episode 的順序
                'episode_id': str(doc.get('_id')),  # 保留原始 episode ID
                'original_filename': filename,
                'collection_name': collection_name,
                'chunk_length': len(chunk_text)
            }
            chunk_data.append(chunk_info)
        
        return {
            'filename': filename,
            'episode_id': str(doc.get('_id')),
            'collection_name': collection_name,
            'total_chunks': len(chunk_data),
            'chunks': chunk_data,
            'original_text_length': len(text_content)
        }
    
    def _get_filename(self, doc: Dict[str, Any]) -> str:
        """獲取檔名，優先順序：_file_metadata.filename > file > _id"""
        # 嘗試從 _file_metadata.filename 獲取
        file_metadata = doc.get('_file_metadata', {})
        if isinstance(file_metadata, dict) and 'filename' in file_metadata:
            filename = file_metadata['filename']
            if filename:
                return clean_filename(filename)
        
        # 嘗試從 file 欄位獲取
        file_field = doc.get('file', '')
        if file_field:
            # 移除 .mp3 副檔名
            filename = file_field.replace('.mp3', '')
            return clean_filename(filename)
        
        # 最後使用 _id
        return str(doc.get('_id', ''))
    
    def process(self, mongodb_config: Dict[str, str]) -> List[Dict[str, Any]]:
        """處理 MongoDB 資料 - 實作 BaseStageProcessor 抽象方法"""
        logger.info("=== 開始階段 1: 文本切斷處理 ===")
        
        # 這裡需要實作 MongoDB 連接和處理邏輯
        # 暫時返回空列表，實際實作需要根據具體需求
        logger.warning("Stage1TextChunker.process 方法需要實作 MongoDB 處理邏輯")
        return []
    
    def save_individual_file(self, result: Dict[str, Any], collection_dir: Path):
        """儲存個別檔案"""
        if not result or 'filename' not in result:
            return
        
        filename = result['filename']
        safe_filename = self._make_filename_safe(filename)
        output_file = collection_dir / f"{safe_filename}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info(f"已儲存: {output_file}")
        except Exception as e:
            logger.error(f"儲存檔案失敗 {output_file}: {e}")
    
    def save_results(self, results: List[Dict[str, Any]], filename: str):
        """儲存結果"""
        output_file = self.data_dir / filename
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"結果已儲存: {output_file}")
        except Exception as e:
            logger.error(f"儲存結果失敗 {output_file}: {e}")
    
    def _make_filename_safe(self, filename: str) -> str:
        """確保檔名安全"""
        # 移除或替換不安全的字符
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 限制長度
        if len(safe_filename) > 200:
            safe_filename = safe_filename[:200]
        return safe_filename.strip()


class Stage2TextCleaningProcessor(BaseStageProcessor):
    """階段 2: 文本清理處理器"""
    
    def __init__(self, data_dir: str = "data/stage2_text_cleaning"):
        super().__init__(data_dir)
        self.stage_name = "Stage2TextCleaning"
    
    def clean_text(self, text: str) -> str:
        """清理文本"""
        # 基本清理
        cleaned = text.strip()
        
        # 移除多餘的空白
        cleaned = ' '.join(cleaned.split())
        
        # 移除特殊字符（保留中文、英文、數字、標點符號）
        import re
        cleaned = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()\[\]{}"\'-]', '', cleaned)
        
        return cleaned
    
    def process(self, chunks_data: List[Dict]) -> List[Dict]:
        """處理文本清理"""
        logger.info("=== 開始階段 2: 文本清理處理 ===")
        
        processed_chunks = []
        
        for chunk_data in chunks_data:
            cleaned_content = self.clean_text(chunk_data['content'])
            
            processed_chunk = {
                **chunk_data,
                'cleaned_content': cleaned_content,
                'cleaned_at': datetime.now().isoformat()
            }
            processed_chunks.append(processed_chunk)
        
        # 儲存結果
        self.save_results(processed_chunks, "cleaned_chunks.json")
        
        logger.info(f"階段 2 完成: 清理了 {len(processed_chunks)} 個 chunks")
        return processed_chunks


class Stage3TaggingProcessor(BaseStageProcessor):
    """階段 3: 標籤處理器"""
    
    def __init__(self, data_dir: str = "data/stage3_tagging"):
        super().__init__(data_dir)
        self.stage_name = "Stage3Tagging"
        self.tag_processor = None
        self.tag_mappings = {}
    
    def load_tag_processor(self, tag_csv_path: str):
        """載入標籤處理器 - 使用統一的 UnifiedTagProcessor"""
        try:
            from .tag_processor import UnifiedTagProcessor
            
            self.tag_processor = UnifiedTagProcessor(tag_csv_path)
            logger.info("✅ 成功載入統一標籤處理器")
        except Exception as e:
            logger.error(f"❌ 載入統一標籤處理器失敗: {e}")
            raise
    
    def extract_tags(self, text: str) -> Tuple[List[str], Dict[str, List[str]]]:
        """提取標籤"""
        if not self.tag_processor:
            raise RuntimeError("標籤處理器未載入")
        
        # 使用統一標籤處理器提取標籤
        tags = self.tag_processor.extract_enhanced_tags(text)
        
        # 分類標籤來源（這裡簡化處理，實際可以根據 TagProcessor 的實現來分類）
        tag_sources = {
            'enhanced_processor': tags,  # 增強版處理器
            'fallback_sources': []  # 備援來源
        }
        
        return tags, tag_sources
    
    def process(self, cleaned_chunks: List[Dict]) -> List[Dict]:
        """處理標籤提取"""
        logger.info("=== 開始階段 3: 標籤處理 ===")
        
        if not self.tag_processor:
            raise RuntimeError("請先載入標籤處理器")
        
        tagged_chunks = []
        
        for chunk_data in cleaned_chunks:
            text = chunk_data['cleaned_content']
            tags, tag_sources = self.extract_tags(text)
            
            tagged_chunk = {
                **chunk_data,
                'tags': tags,
                'tag_sources': tag_sources,
                'tagged_at': datetime.now().isoformat()
            }
            tagged_chunks.append(tagged_chunk)
        
        # 儲存結果
        self.save_results(tagged_chunks, "tagged_chunks.json")
        
        logger.info(f"階段 3 完成: 為 {len(tagged_chunks)} 個 chunks 添加標籤")
        return tagged_chunks


class Stage4EmbeddingPrepProcessor(BaseStageProcessor):
    """階段 4: Embedding 準備處理器"""
    
    def __init__(self, data_dir: str = "data/stage4_embedding_prep"):
        super().__init__(data_dir)
        self.stage_name = "Stage4EmbeddingPrep"
    
    def prepare_for_embedding(self, tagged_chunk: Dict) -> Dict:
        """準備 embedding 資料"""
        # 準備符合 Milvus 格式的資料
        embedding_data = {
            'chunk_id': tagged_chunk['chunk_id'],
            'episode_id': tagged_chunk['episode_id'],
            'chunk_index': tagged_chunk['chunk_index'],
            'content': tagged_chunk['cleaned_content'],
            'tags': tagged_chunk['tags'],
            'tag_sources': tagged_chunk['tag_sources'],
            'original_filename': tagged_chunk['original_filename'],
            'collection_name': tagged_chunk['collection_name'],
            'created_at': tagged_chunk['created_at'],
            'prepared_at': datetime.now().isoformat()
        }
        
        return embedding_data
    
    def process(self, tagged_chunks: List[Dict]) -> List[Dict]:
        """處理 embedding 準備"""
        logger.info("=== 開始階段 4: Embedding 準備處理 ===")
        
        embedding_ready_data = []
        
        for tagged_chunk in tagged_chunks:
            embedding_data = self.prepare_for_embedding(tagged_chunk)
            embedding_ready_data.append(embedding_data)
        
        # 儲存結果
        self.save_results(embedding_ready_data, "embedding_ready_data.json")
        
        logger.info(f"階段 4 完成: 準備了 {len(embedding_ready_data)} 筆 embedding 資料")
        return embedding_ready_data


class PipelineOrchestrator:
    """管線協調器"""
    
    def __init__(self, base_data_dir: str = "data"):
        self.base_data_dir = Path(base_data_dir)
        self.stage1 = Stage1TextChunker(f"{base_data_dir}/stage1_chunking")
        self.stage2 = Stage2TextCleaningProcessor(f"{base_data_dir}/stage2_text_cleaning")
        self.stage3 = Stage3TaggingProcessor(f"{base_data_dir}/stage3_tagging")
        self.stage4 = Stage4EmbeddingPrepProcessor(f"{base_data_dir}/stage4_embedding_prep")
    
    def run_stage1(self, mongodb_config: Dict[str, str]) -> List[Dict]:
        """執行階段 1"""
        return self.stage1.process(mongodb_config)
    
    def run_stage2(self, chunks_data: List[Dict]) -> List[Dict]:
        """執行階段 2"""
        return self.stage2.process(chunks_data)
    
    def run_stage3(self, cleaned_chunks: List[Dict], tag_csv_path: str) -> List[Dict]:
        """執行階段 3"""
        self.stage3.load_tag_processor(tag_csv_path)
        return self.stage3.process(cleaned_chunks)
    
    def run_stage4(self, tagged_chunks: List[Dict]) -> List[Dict]:
        """執行階段 4"""
        return self.stage4.process(tagged_chunks)
    
    def run_all_stages(self, mongodb_config: Dict[str, str], tag_csv_path: str) -> List[Dict]:
        """執行所有階段"""
        logger.info("🚀 開始執行完整管線")
        
        # 階段 1: 文本切斷
        chunks_data = self.run_stage1(mongodb_config)
        
        # 階段 2: 文本清理
        cleaned_chunks = self.run_stage2(chunks_data)
        
        # 階段 3: 標籤處理
        tagged_chunks = self.run_stage3(cleaned_chunks, tag_csv_path)
        
        # 階段 4: Embedding 準備
        embedding_data = self.run_stage4(tagged_chunks)
        
        logger.info("🎉 完整管線執行完成")
        return embedding_data 