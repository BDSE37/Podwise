"""
批次處理腳本
整合所有批次處理功能
符合 Google Clean Code 原則
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..services.tagging_service import TaggingService
from ..services.embedding_service import EmbeddingService
from ..config.settings import config

logger = logging.getLogger(__name__)


class BatchProcessor:
    """批次處理器 - 整合所有批次處理功能"""
    
    def __init__(self):
        """初始化批次處理器"""
        self.tagging_service = TaggingService()
        self.embedding_service = EmbeddingService()
        
    def process_all_rss_folders(self) -> Dict[str, Any]:
        """
        處理所有 RSS 資料夾
        
        Returns:
            處理結果統計
        """
        logger.info("開始批次處理所有 RSS 資料夾")
        
        # 獲取所有 RSS 資料夾
        stage1_path = Path(config.stage1_dir)
        stage3_path = Path(config.stage3_dir)
        
        if not stage1_path.exists():
            return {"error": f"輸入路徑不存在: {stage1_path}"}
        
        rss_folders = [f.name for f in stage1_path.iterdir() 
                      if f.is_dir() and f.name.startswith('RSS_')]
        
        if not rss_folders:
            return {"error": "沒有找到 RSS 資料夾"}
        
        logger.info(f"找到 {len(rss_folders)} 個 RSS 資料夾")
        
        # 處理所有資料夾
        results = self.tagging_service.process_multiple_rss_folders(
            rss_folders, str(stage1_path), str(stage3_path)
        )
        
        # 顯示總體統計
        self._show_overall_stats(results)
        
        return results
    
    def _show_overall_stats(self, results: Dict[str, Dict[str, Any]]) -> None:
        """顯示總體統計"""
        total_files = sum(r.get('total_files', 0) for r in results.values())
        total_successful = sum(r.get('successful_files', 0) for r in results.values())
        total_failed = sum(r.get('failed_files', 0) for r in results.values())
        total_chunks = sum(r.get('total_chunks', 0) for r in results.values())
        total_tags = sum(r.get('total_tags', 0) for r in results.values())
        
        logger.info("=" * 60)
        logger.info("總體批次處理統計")
        logger.info("=" * 60)
        logger.info(f"總檔案數: {total_files}")
        logger.info(f"成功檔案: {total_successful}")
        logger.info(f"失敗檔案: {total_failed}")
        logger.info(f"總 chunks: {total_chunks}")
        logger.info(f"總標籤: {total_tags}")
        logger.info(f"成功率: {total_successful/total_files*100:.2f}%" if total_files > 0 else "0%")
        logger.info("=" * 60)
    
    def embed_all_stage3_data(self) -> Dict[str, Any]:
        """
        嵌入所有 stage3 資料
        
        Returns:
            嵌入結果統計
        """
        logger.info("開始批次嵌入所有 stage3 資料")
        
        results = self.embedding_service.embed_stage3_data()
        
        if "error" not in results:
            logger.info(f"批次嵌入完成: {results['successful_files']}/{results['total_files']} 檔案成功")
            logger.info(f"總 chunks: {results['total_chunks']}")
            logger.info(f"成功率: {results['success_rate']:.2f}%")
        
        return results
    
    def run_full_batch_pipeline(self) -> Dict[str, Any]:
        """
        執行完整批次管線
        
        Returns:
            完整管線結果
        """
        logger.info("🚀 開始執行完整批次管線")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "stages": {}
        }
        
        try:
            # 階段 1: 標籤處理
            logger.info("=== 階段 1: 標籤處理 ===")
            tagging_results = self.process_all_rss_folders()
            results["stages"]["tagging"] = tagging_results
            
            # 階段 2: 嵌入處理
            logger.info("=== 階段 2: 嵌入處理 ===")
            embedding_results = self.embed_all_stage3_data()
            results["stages"]["embedding"] = embedding_results
            
            logger.info("🎉 完整批次管線執行完成")
            
        except Exception as e:
            logger.error(f"批次管線執行失敗: {e}")
            results["error"] = str(e)
        
        return results 