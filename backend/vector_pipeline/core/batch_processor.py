#!/usr/bin/env python3
"""
統一的批次處理器
整合所有批次處理邏輯，提供進度追蹤和錯誤處理
符合 Google Clean Code 原則，提供 OOP 介面
"""

import logging
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import time
from dataclasses import dataclass
from abc import ABC, abstractmethod

from .tag_processor import UnifiedTagProcessor

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    """處理統計資訊"""
    total_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    total_chunks: int = 0
    total_tags: int = 0
    failed_files_list: List[str] = None
    processing_time: float = 0.0
    
    def __post_init__(self):
        if self.failed_files_list is None:
            self.failed_files_list = []


class BaseProcessor(ABC):
    """處理器抽象基類"""
    
    @abstractmethod
    def process_single_file(self, input_file: Path, output_file: Path) -> bool:
        """處理單一檔案"""
        pass
    
    @abstractmethod
    def get_processor_name(self) -> str:
        """獲取處理器名稱"""
        pass


class TaggingProcessor(BaseProcessor):
    """標籤處理器"""
    
    def __init__(self, tag_csv_path: str = "../utils/TAG_info.csv"):
        """
        初始化標籤處理器
        
        Args:
            tag_csv_path: TAG_info.csv 檔案路徑
        """
        self.tag_processor = UnifiedTagProcessor(tag_csv_path)
        self.stage1_path = Path("data/stage1_chunking")
        self.stage3_path = Path("data/stage3_tagging")
        self.progress_file = Path("tagging_progress.json")
        
        # 確保輸出目錄存在
        self.stage3_path.mkdir(parents=True, exist_ok=True)
        
        # 載入進度追蹤
        self.processed_files = self._load_progress()
        
        logger.info("標籤處理器初始化完成")
        logger.info(f"已處理檔案數: {len(self.processed_files)}")
    
    def _load_progress(self) -> set:
        """載入進度追蹤檔案"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                    return set(progress_data.get('processed_files', []))
            except Exception as e:
                logger.warning(f"載入進度檔案失敗: {e}")
        return set()
    
    def _save_progress(self):
        """儲存進度追蹤檔案"""
        try:
            progress_data = {
                'processed_files': list(self.processed_files),
                'last_updated': datetime.now().isoformat(),
                'total_processed': len(self.processed_files)
            }
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"儲存進度檔案失敗: {e}")
    
    def _is_file_processed(self, input_file: Path) -> bool:
        """檢查檔案是否已處理"""
        relative_path = str(input_file.relative_to(self.stage1_path))
        return relative_path in self.processed_files
    
    def _mark_file_processed(self, input_file: Path):
        """標記檔案為已處理"""
        relative_path = str(input_file.relative_to(self.stage1_path))
        self.processed_files.add(relative_path)
        self._save_progress()
    
    def process_single_file(self, input_file: Path, output_file: Path) -> bool:
        """
        處理單一 JSON 檔案
        
        Args:
            input_file: 輸入檔案路徑
            output_file: 輸出檔案路徑
            
        Returns:
            bool: 處理是否成功
        """
        # 檢查是否已處理
        if self._is_file_processed(input_file):
            logger.debug(f"檔案已處理，跳過: {input_file}")
            return True
        
        try:
            logger.info(f"開始處理檔案: {input_file}")
            
            # 讀取 JSON 檔案
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 檢查檔案結構
            if 'chunks' not in data:
                logger.warning(f"檔案 {input_file} 缺少 chunks 欄位，跳過")
                return False
            
            # 處理每個 chunk
            processed_chunks = []
            for i, chunk in enumerate(data['chunks']):
                if 'chunk_text' not in chunk:
                    logger.warning(f"Chunk {i} 缺少 chunk_text 欄位，跳過")
                    continue
                
                # 使用統一標籤處理器提取標籤
                chunk_text = chunk['chunk_text']
                tags = self.tag_processor.extract_enhanced_tags(chunk_text)
                
                # 建立處理後的 chunk
                processed_chunk = {
                    **chunk,  # 保留原始資料
                    'tags': tags,  # 新增標籤欄位
                    'tag_count': len(tags),  # 標籤數量
                    'processed_at': datetime.now().isoformat()
                }
                
                processed_chunks.append(processed_chunk)
                
                # 記錄處理進度
                if (i + 1) % 10 == 0:
                    logger.info(f"已處理 {i + 1}/{len(data['chunks'])} 個 chunks")
            
            # 建立輸出資料結構
            output_data = {
                **data,  # 保留原始資料
                'chunks': processed_chunks,
                'total_chunks': len(processed_chunks),
                'total_tags': sum(len(chunk['tags']) for chunk in processed_chunks),
                'processed_at': datetime.now().isoformat(),
                'tagging_system': 'UnifiedTagProcessor'
            }
            
            # 確保輸出目錄存在
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 寫入輸出檔案
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            # 標記為已處理
            self._mark_file_processed(input_file)
            
            logger.info(f"成功處理檔案: {input_file} -> {output_file}")
            logger.info(f"處理了 {len(processed_chunks)} 個 chunks，總標籤數: {output_data['total_tags']}")
            
            return True
            
        except Exception as e:
            logger.error(f"處理檔案 {input_file} 時發生錯誤: {e}")
            return False
    
    def get_processor_name(self) -> str:
        """獲取處理器名稱"""
        return "TaggingProcessor"
    
    def show_processing_status(self):
        """顯示處理狀態"""
        total_files = len(list(self.stage1_path.rglob("*.json")))
        processed_files = len(self.processed_files)
        unprocessed_files = total_files - processed_files
        
        logger.info("=== 標籤處理狀態統計 ===")
        logger.info(f"總檔案數: {total_files}")
        logger.info(f"已處理: {processed_files}")
        logger.info(f"未處理: {unprocessed_files}")
        if total_files > 0:
            logger.info(f"完成率: {processed_files/total_files*100:.2f}%")
        
        if unprocessed_files > 0:
            logger.info("還有檔案需要處理")
        else:
            logger.info("所有檔案都已處理完成！")


class BatchProcessor:
    """統一的批次處理器"""
    
    def __init__(self, processor: BaseProcessor):
        """
        初始化批次處理器
        
        Args:
            processor: 具體的處理器實例
        """
        self.processor = processor
        logger.info(f"批次處理器初始化完成，使用處理器: {processor.get_processor_name()}")
    
    def process_all_files(self, input_path: Path, output_path: Path) -> ProcessingStats:
        """
        處理所有檔案
        
        Args:
            input_path: 輸入路徑
            output_path: 輸出路徑
            
        Returns:
            ProcessingStats: 處理統計資訊
        """
        start_time = time.time()
        logger.info(f"開始批次處理所有檔案")
        
        # 統計資訊
        stats = ProcessingStats()
        
        # 尋找所有 JSON 檔案
        json_files = list(input_path.rglob("*.json"))
        stats.total_files = len(json_files)
        
        logger.info(f"找到 {len(json_files)} 個 JSON 檔案")
        
        # 處理每個檔案
        for i, json_file in enumerate(json_files, 1):
            logger.info(f"處理進度: {i}/{len(json_files)} - {json_file}")
            
            # 建立輸出檔案路徑
            relative_path = json_file.relative_to(input_path)
            output_file = output_path / relative_path
            
            success = self.processor.process_single_file(json_file, output_file)
            
            if success:
                stats.successful_files += 1
                # 讀取輸出檔案統計資訊
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    stats.total_chunks += data.get('total_chunks', 0)
                    stats.total_tags += data.get('total_tags', 0)
                except Exception as e:
                    logger.warning(f"讀取統計資訊失敗 {output_file}: {e}")
            else:
                stats.failed_files += 1
                stats.failed_files_list.append(str(json_file))
        
        stats.processing_time = time.time() - start_time
        
        logger.info("批次處理完成")
        logger.info(f"統計資訊: {stats}")
        
        return stats
    
    def process_rss_folder(self, rss_folder: str, input_path: Path, output_path: Path) -> ProcessingStats:
        """
        處理特定 RSS 資料夾
        
        Args:
            rss_folder: RSS 資料夾名稱
            input_path: 輸入路徑
            output_path: 輸出路徑
            
        Returns:
            ProcessingStats: 處理統計資訊
        """
        logger.info(f"=== 開始處理 RSS 資料夾: {rss_folder} ===")
        
        # 設定路徑
        stage1_path = input_path / rss_folder
        stage3_path = output_path / rss_folder
        
        # 確保輸出目錄存在
        stage3_path.mkdir(parents=True, exist_ok=True)
        
        return self.process_all_files(stage1_path, stage3_path)
    
    def process_multiple_rss_folders(self, rss_folders: List[str], input_path: Path, output_path: Path) -> Dict[str, ProcessingStats]:
        """
        處理多個 RSS 資料夾
        
        Args:
            rss_folders: RSS 資料夾名稱列表
            input_path: 輸入路徑
            output_path: 輸出路徑
            
        Returns:
            Dict[str, ProcessingStats]: 每個資料夾的處理統計
        """
        logger.info(f"=== 開始處理 {len(rss_folders)} 個 RSS 資料夾 ===")
        
        results = {}
        
        for i, rss_folder in enumerate(rss_folders, 1):
            logger.info(f"處理進度: {i}/{len(rss_folders)} - {rss_folder}")
            
            try:
                stats = self.process_rss_folder(rss_folder, input_path, output_path)
                results[rss_folder] = stats
            except Exception as e:
                logger.error(f"處理 RSS 資料夾 {rss_folder} 時發生錯誤: {e}")
                results[rss_folder] = ProcessingStats(failed_files=1, failed_files_list=[rss_folder])
        
        return results


def create_tagging_processor(tag_csv_path: str = "../utils/TAG_info.csv") -> TaggingProcessor:
    """
    創建標籤處理器
    
    Args:
        tag_csv_path: TAG_info.csv 檔案路徑
        
    Returns:
        TaggingProcessor: 標籤處理器實例
    """
    return TaggingProcessor(tag_csv_path)


def create_batch_processor(processor: BaseProcessor) -> BatchProcessor:
    """
    創建批次處理器
    
    Args:
        processor: 具體的處理器實例
        
    Returns:
        BatchProcessor: 批次處理器實例
    """
    return BatchProcessor(processor) 