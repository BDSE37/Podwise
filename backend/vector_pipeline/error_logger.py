"""
錯誤記錄器
專門記錄向量化過程中的錯誤，供事後處理
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class VectorizationError:
    """向量化錯誤資料類別"""
    collection_id: str
    rss_id: str
    title: str
    error_type: str
    error_message: str
    error_details: str
    timestamp: str
    processing_stage: str
    retry_count: int = 0


class ErrorLogger:
    """錯誤記錄器"""
    
    def __init__(self, log_dir: str = "error_logs"):
        """
        初始化錯誤記錄器
        
        Args:
            log_dir: 錯誤日誌目錄
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 錯誤列表
        self.errors: List[VectorizationError] = []
        
        # 設定日誌
        self.logger = logging.getLogger(__name__)
        
    def add_error(self, 
                  collection_id: str,
                  rss_id: str,
                  title: str,
                  error_type: str,
                  error_message: str,
                  error_details: str = "",
                  processing_stage: str = "unknown") -> None:
        """
        添加錯誤記錄
        
        Args:
            collection_id: Collection ID
            rss_id: RSS ID
            title: 節目標題
            error_type: 錯誤類型
            error_message: 錯誤訊息
            error_details: 詳細錯誤資訊
            processing_stage: 處理階段
        """
        error = VectorizationError(
            collection_id=collection_id,
            rss_id=rss_id,
            title=title,
            error_type=error_type,
            error_message=error_message,
            error_details=error_details,
            timestamp=datetime.now().isoformat(),
            processing_stage=processing_stage
        )
        
        self.errors.append(error)
        self.logger.error(f"錯誤記錄: {collection_id}/{rss_id} - {error_type}: {error_message}")
    
    def save_errors(self, filename: Optional[str] = None) -> str:
        """
        儲存錯誤清單到檔案
        
        Args:
            filename: 檔案名稱（可選）
            
        Returns:
            檔案路徑
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vectorization_errors_{timestamp}.json"
        
        file_path = self.log_dir / filename
        
        # 轉換為字典格式
        error_data = {
            "summary": {
                "total_errors": len(self.errors),
                "generated_at": datetime.now().isoformat(),
                "error_types": self._get_error_type_summary()
            },
            "errors": [asdict(error) for error in self.errors]
        }
        
        # 儲存到 JSON 檔案
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"錯誤清單已儲存到: {file_path}")
        return str(file_path)
    
    def save_csv_report(self, filename: Optional[str] = None) -> str:
        """
        儲存 CSV 格式的錯誤報告
        
        Args:
            filename: 檔案名稱（可選）
            
        Returns:
            檔案路徑
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vectorization_errors_{timestamp}.csv"
        
        file_path = self.log_dir / filename
        
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 寫入標題行
            writer.writerow([
                'Collection ID',
                'RSS ID', 
                'Title',
                'Error Type',
                'Error Message',
                'Processing Stage',
                'Timestamp',
                'Retry Count'
            ])
            
            # 寫入錯誤資料
            for error in self.errors:
                writer.writerow([
                    error.collection_id,
                    error.rss_id,
                    error.title,
                    error.error_type,
                    error.error_message,
                    error.processing_stage,
                    error.timestamp,
                    error.retry_count
                ])
        
        self.logger.info(f"CSV 錯誤報告已儲存到: {file_path}")
        return str(file_path)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        獲取錯誤摘要
        
        Returns:
            錯誤摘要資訊
        """
        if not self.errors:
            return {"total_errors": 0, "error_types": {}}
        
        error_types = self._get_error_type_summary()
        
        return {
            "total_errors": len(self.errors),
            "error_types": error_types,
            "collections_affected": len(set(e.collection_id for e in self.errors)),
            "processing_stages": list(set(e.processing_stage for e in self.errors))
        }
    
    def _get_error_type_summary(self) -> Dict[str, int]:
        """獲取錯誤類型統計"""
        error_types = {}
        for error in self.errors:
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
        return error_types
    
    def get_errors_by_collection(self, collection_id: str) -> List[VectorizationError]:
        """
        獲取指定 collection 的錯誤
        
        Args:
            collection_id: Collection ID
            
        Returns:
            錯誤列表
        """
        return [error for error in self.errors if error.collection_id == collection_id]
    
    def get_errors_by_type(self, error_type: str) -> List[VectorizationError]:
        """
        獲取指定錯誤類型的錯誤
        
        Args:
            error_type: 錯誤類型
            
        Returns:
            錯誤列表
        """
        return [error for error in self.errors if error.error_type == error_type]
    
    def clear_errors(self) -> None:
        """清除錯誤列表"""
        self.errors.clear()
        self.logger.info("錯誤列表已清除")
    
    def print_summary(self) -> None:
        """列印錯誤摘要"""
        summary = self.get_error_summary()
        
        print("\n=== 錯誤摘要 ===")
        print(f"總錯誤數: {summary['total_errors']}")
        print(f"受影響的 Collections: {summary['collections_affected']}")
        
        if summary['error_types']:
            print("\n錯誤類型統計:")
            for error_type, count in summary['error_types'].items():
                print(f"  {error_type}: {count}")
        
        if summary['processing_stages']:
            print(f"\n處理階段: {', '.join(summary['processing_stages'])}")
        
        if self.errors:
            print(f"\n前5個錯誤範例:")
            for i, error in enumerate(self.errors[:5], 1):
                print(f"  {i}. {error.collection_id}/{error.rss_id} - {error.error_type}")
                print(f"     {error.title}")
                print(f"     {error.error_message}")
                print()


class ErrorHandler:
    """錯誤處理器 - 整合到管道中"""
    
    def __init__(self, error_logger: ErrorLogger):
        """
        初始化錯誤處理器
        
        Args:
            error_logger: 錯誤記錄器
        """
        self.error_logger = error_logger
        self.logger = logging.getLogger(__name__)
    
    def handle_mongodb_error(self, collection_id: str, rss_id: str, title: str, 
                           error: Exception, stage: str = "mongodb_read") -> None:
        """處理 MongoDB 錯誤"""
        self.error_logger.add_error(
            collection_id=collection_id,
            rss_id=rss_id,
            title=title,
            error_type="mongodb_error",
            error_message=str(error),
            error_details=f"Stage: {stage}",
            processing_stage=stage
        )
    
    def handle_text_processing_error(self, collection_id: str, rss_id: str, title: str,
                                   error: Exception, stage: str = "text_processing") -> None:
        """處理文本處理錯誤"""
        self.error_logger.add_error(
            collection_id=collection_id,
            rss_id=rss_id,
            title=title,
            error_type="text_processing_error",
            error_message=str(error),
            error_details=f"Stage: {stage}",
            processing_stage=stage
        )
    
    def handle_vectorization_error(self, collection_id: str, rss_id: str, title: str,
                                 error: Exception, stage: str = "vectorization") -> None:
        """處理向量化錯誤"""
        self.error_logger.add_error(
            collection_id=collection_id,
            rss_id=rss_id,
            title=title,
            error_type="vectorization_error",
            error_message=str(error),
            error_details=f"Stage: {stage}",
            processing_stage=stage
        )
    
    def handle_milvus_error(self, collection_id: str, rss_id: str, title: str,
                          error: Exception, stage: str = "milvus_write") -> None:
        """處理 Milvus 錯誤"""
        self.error_logger.add_error(
            collection_id=collection_id,
            rss_id=rss_id,
            title=title,
            error_type="milvus_error",
            error_message=str(error),
            error_details=f"Stage: {stage}",
            processing_stage=stage
        )
    
    def handle_general_error(self, collection_id: str, rss_id: str, title: str,
                           error: Exception, stage: str = "general") -> None:
        """處理一般錯誤"""
        self.error_logger.add_error(
            collection_id=collection_id,
            rss_id=rss_id,
            title=title,
            error_type="general_error",
            error_message=str(error),
            error_details=f"Stage: {stage}",
            processing_stage=stage
        )
    
    def save_error_reports(self) -> Dict[str, str]:
        """
        儲存錯誤報告
        
        Returns:
            報告檔案路徑字典
        """
        json_file = self.error_logger.save_errors()
        csv_file = self.error_logger.save_csv_report()
        
        return {
            "json_report": json_file,
            "csv_report": csv_file
        } 