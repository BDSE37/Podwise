#!/usr/bin/env python3
"""
Vector Pipeline 主程式 - 重構版本
統一入口點，整合所有功能
符合 Google Clean Code 原則
"""

import logging
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from config.settings import config
from services.tagging_service import TaggingService
from services.embedding_service import EmbeddingService
from services.search_service import SearchService
from utils.data_quality_checker import DataQualityChecker

# 設置日誌
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class VectorPipeline:
    """Vector Pipeline 主類別 - 重構版本"""
    
    def __init__(self):
        """初始化 Vector Pipeline"""
        self.tagging_service = TaggingService()
        self.embedding_service = EmbeddingService()
        self.search_service = SearchService()
        self.data_quality_checker = DataQualityChecker()
        
        logger.info("Vector Pipeline 初始化完成")
    
    def process_tagging(self, stage1_dir: Optional[str] = None, 
                       stage3_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        執行標籤處理
        
        Args:
            stage1_dir: stage1 目錄路徑
            stage3_dir: stage3 目錄路徑
            
        Returns:
            處理結果
        """
        stage1_path = Path(stage1_dir or config.stage1_dir)
        stage3_path = Path(stage3_dir or config.stage3_dir)
        
        if not stage1_path.exists():
            return {"error": f"輸入路徑不存在: {stage1_path}"}
        
        # 獲取所有 RSS 資料夾
        rss_folders = [f.name for f in stage1_path.iterdir() 
                      if f.is_dir() and f.name.startswith('RSS_')]
        
        if not rss_folders:
            return {"error": "沒有找到 RSS 資料夾"}
        
        logger.info(f"開始標籤處理，找到 {len(rss_folders)} 個 RSS 資料夾")
        
        # 執行標籤處理
        results = self.tagging_service.process_multiple_rss_folders(
            rss_folders, str(stage1_path), str(stage3_path)
        )
        
        return results
    
    def process_embedding(self, stage3_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        執行嵌入處理
        
        Args:
            stage3_dir: stage3 目錄路徑
            
        Returns:
            嵌入結果
        """
        logger.info("開始嵌入處理")
        
        results = self.embedding_service.embed_stage3_data(stage3_dir)
        
        if "error" not in results:
            logger.info(f"嵌入完成: {results['successful_files']}/{results['total_files']} 檔案成功")
        
        return results
    
    def search_content(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        搜尋內容
        
        Args:
            query: 查詢文本
            top_k: 返回結果數量
            
        Returns:
            搜尋結果
        """
        logger.info(f"搜尋內容: '{query}'")
        
        results = self.search_service.search_similar_content(query, top_k)
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    
    def test_search(self) -> Dict[str, Any]:
        """
        測試搜尋功能
        
        Returns:
            測試結果
        """
        logger.info("開始搜尋功能測試")
        
        return self.search_service.test_search_functionality()
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        獲取集合統計資訊
        
        Returns:
            集合統計資訊
        """
        return self.search_service.get_collection_stats()
    
    def get_tag_statistics(self, stage3_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        獲取標籤統計資訊
        
        Args:
            stage3_dir: stage3 目錄路徑
            
        Returns:
            標籤統計資訊
        """
        return self.tagging_service.get_tag_statistics(stage3_dir)
    
    def check_data_quality(self, stage3_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        檢查資料品質
        
        Args:
            stage3_dir: stage3 目錄路徑
            
        Returns:
            資料品質報告
        """
        stage3_path = Path(stage3_dir or config.stage3_dir)
        
        if not stage3_path.exists():
            return {"error": f"目錄不存在: {stage3_path}"}
        
        logger.info("開始資料品質檢查")
        
        return self.data_quality_checker.check_stage3_data(str(stage3_path))
    
    def run_full_pipeline(self) -> Dict[str, Any]:
        """
        執行完整管線
        
        Returns:
            完整管線結果
        """
        logger.info("🚀 開始執行完整 Vector Pipeline")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "stages": {}
        }
        
        try:
            # 階段 1: 標籤處理
            logger.info("=== 階段 1: 標籤處理 ===")
            tagging_results = self.process_tagging()
            results["stages"]["tagging"] = tagging_results
            
            # 階段 2: 嵌入處理
            logger.info("=== 階段 2: 嵌入處理 ===")
            embedding_results = self.process_embedding()
            results["stages"]["embedding"] = embedding_results
            
            # 階段 3: 搜尋測試
            logger.info("=== 階段 3: 搜尋測試 ===")
            search_results = self.test_search()
            results["stages"]["search_test"] = search_results
            
            logger.info("🎉 完整管線執行完成")
            
        except Exception as e:
            logger.error(f"管線執行失敗: {e}")
            results["error"] = str(e)
        
        return results


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="Vector Pipeline 主程式")
    parser.add_argument("--action", choices=[
        "tagging", "embedding", "search", "test_search", 
        "stats", "tag_stats", "quality", "full_pipeline"
    ], default="full_pipeline", help="執行動作")
    
    parser.add_argument("--query", type=str, help="搜尋查詢")
    parser.add_argument("--top_k", type=int, default=5, help="搜尋結果數量")
    parser.add_argument("--stage1_dir", type=str, help="stage1 目錄路徑")
    parser.add_argument("--stage3_dir", type=str, help="stage3 目錄路徑")
    
    args = parser.parse_args()
    
    # 初始化 Vector Pipeline
    pipeline = VectorPipeline()
    
    try:
        if args.action == "tagging":
            results = pipeline.process_tagging(args.stage1_dir, args.stage3_dir)
            print("標籤處理結果:", results)
            
        elif args.action == "embedding":
            results = pipeline.process_embedding(args.stage3_dir)
            print("嵌入處理結果:", results)
            
        elif args.action == "search":
            if not args.query:
                print("錯誤: 搜尋需要提供 --query 參數")
                return
            results = pipeline.search_content(args.query, args.top_k)
            print("搜尋結果:", results)
            
        elif args.action == "test_search":
            results = pipeline.test_search()
            print("搜尋測試結果:", results)
            
        elif args.action == "stats":
            results = pipeline.get_collection_stats()
            print("集合統計:", results)
            
        elif args.action == "tag_stats":
            results = pipeline.get_tag_statistics(args.stage3_dir)
            print("標籤統計:", results)
            
        elif args.action == "quality":
            results = pipeline.check_data_quality(args.stage3_dir)
            print("資料品質報告:", results)
            
        elif args.action == "full_pipeline":
            results = pipeline.run_full_pipeline()
            print("完整管線結果:", results)
            
    except Exception as e:
        logger.error(f"執行失敗: {e}")
        print(f"錯誤: {e}")


if __name__ == "__main__":
    main() 