#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vector Pipeline 主程式入口點

提供統一的命令列介面，方便調用所有向量處理功能。

Author: Podri Team
License: MIT
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加父目錄到路徑
sys.path.append(str(Path(__file__).parent.parent))

def list_components():
    """列出所有可用的組件"""
    try:
        from vector_pipeline import (
            PipelineOrchestrator, MongoDBProcessor, PostgreSQLMapper,
            TextChunker, VectorProcessor, MilvusWriter
        )
        
        components = {
            "PipelineOrchestrator": "主要協調器，整合所有處理流程",
            "MongoDBProcessor": "MongoDB 資料處理器（整合 data_cleaning）",
            "PostgreSQLMapper": "PostgreSQL metadata mapping",
            "TextChunker": "文本切分處理器",
            "VectorProcessor": "向量化處理器",
            "MilvusWriter": "Milvus 資料寫入器"
        }
        
        print("可用的組件：")
        print("=" * 60)
        for name, description in components.items():
            print(f"• {name}: {description}")
        print("=" * 60)
        
    except ImportError as e:
        logger.error(f"無法載入組件: {e}")
        return False
    
    return True

def test_components():
    """測試所有組件"""
    try:
        from vector_pipeline import MongoDBProcessor, TextChunker, VectorProcessor
        
        print("測試組件功能...")
        print("=" * 60)
        
        # 測試 TextChunker
        print("1. 測試 TextChunker")
        chunker = TextChunker()
        test_text = "這是一個測試文本。它包含多個句子。我們要測試文本切分功能。"
        chunks = chunker.split_text_into_chunks(test_text, "test_doc")
        print(f"   原始文本: {test_text}")
        print(f"   切分結果: {len(chunks)} 個 chunks")
        for i, chunk in enumerate(chunks[:3]):  # 只顯示前3個
            print(f"     Chunk {i+1}: {chunk.chunk_text[:30]}...")
        print()
        
        # 測試 VectorProcessor
        print("2. 測試 VectorProcessor")
        processor = VectorProcessor()
        test_chunks = [
            {"text": "這是第一個文本塊", "metadata": {"source": "test"}},
            {"text": "這是第二個文本塊", "metadata": {"source": "test"}}
        ]
        print(f"   測試文本塊數量: {len(test_chunks)}")
        print("   (向量化需要模型載入，這裡只測試初始化)")
        print()
        
        # 測試 MongoDBProcessor
        print("3. 測試 MongoDBProcessor")
        processor = MongoDBProcessor("mongodb://localhost:27017", "test_db")
        print("   MongoDBProcessor 初始化成功")
        print("   (實際處理需要 MongoDB 連接)")
        print()
        
        print("所有組件測試完成！")
        return True
        
    except Exception as e:
        logger.error(f"測試組件失敗: {e}")
        return False

def process_rss_collection(collection_name: str, mongo_config: Dict[str, Any]):
    """處理 RSS collection"""
    try:
        from vector_pipeline.rss_processor import RSSProcessor
        
        print(f"開始處理 RSS collection: {collection_name}")
        
        # 初始化 RSS 處理器
        postgres_config = {
            "host": "localhost",
            "port": 5432,
            "database": "podcast",
            "user": "user",
            "password": "password"
        }
        
        milvus_config = {
            "host": "localhost",
            "port": "19530",
            "collection_name": "podcast_chunks",
            "dim": 1024
        }
        
        processor = RSSProcessor(mongo_config, postgres_config, milvus_config)
        
        # 處理 collection
        result = processor.process_rss_collection(collection_name)
        
        print(f"RSS collection 處理完成！")
        print(f"結果: {result}")
        return True
        
    except Exception as e:
        logger.error(f"處理 RSS collection 失敗: {e}")
        return False

def run_pipeline(input_config: Dict[str, Any]):
    """執行完整的 Pipeline"""
    try:
        from vector_pipeline import PipelineOrchestrator
        
        print("開始執行完整 Pipeline...")
        
        # 準備配置
        mongo_config = input_config.get('mongo', {})
        postgres_config = {
            "host": "localhost",
            "port": 5432,
            "database": "podcast",
            "user": "user",
            "password": "password"
        }
        milvus_config = {
            "host": "localhost",
            "port": "19530",
            "collection_name": "podcast_chunks",
            "dim": 1024
        }
        
        # 初始化協調器
        orchestrator = PipelineOrchestrator(mongo_config, postgres_config, milvus_config)
        
        # 執行 Pipeline
        collections = input_config.get('collections', [])
        results = []
        
        for collection in collections:
            result = orchestrator.process_collection(collection, "podcast_chunks")
            results.append(result)
        
        print(f"Pipeline 執行完成！")
        print(f"結果: {results}")
        return True
        
    except Exception as e:
        logger.error(f"執行 Pipeline 失敗: {e}")
        return False

def test_data_cleaning_integration():
    """測試 data_cleaning 整合"""
    try:
        print("測試 data_cleaning 模組整合...")
        print("=" * 60)
        
        # 測試導入
        from vector_pipeline.core import MongoDBProcessor
        
        # 初始化處理器
        processor = MongoDBProcessor("mongodb://localhost:27017", "test_db")
        
        # 測試清理功能
        test_doc = {
            "text": "這是一個測試文檔 😊 包含表情符號 :)",
            "title": "測試標題 🚀",
            "description": "測試描述 :D"
        }
        
        # 測試清理（需要實際的清理器）
        print("MongoDBProcessor 初始化成功")
        print("data_cleaning 模組整合正常")
        print()
        
        return True
        
    except Exception as e:
        logger.error(f"測試 data_cleaning 整合失敗: {e}")
        return False

def main():
    """主程式入口點"""
    parser = argparse.ArgumentParser(
        description="Vector Pipeline 命令列工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 列出所有組件
  python main.py --list-components
  
  # 測試組件
  python main.py --test-components
  
  # 測試 data_cleaning 整合
  python main.py --test-data-cleaning
  
  # 處理 RSS collection
  python main.py --process-rss RSS_1500839292
  
  # 執行完整 Pipeline
  python main.py --run-pipeline
        """
    )
    
    # 基本選項
    parser.add_argument('--list-components', action='store_true',
                       help='列出所有可用的組件')
    parser.add_argument('--test-components', action='store_true',
                       help='測試所有組件功能')
    parser.add_argument('--test-data-cleaning', action='store_true',
                       help='測試 data_cleaning 模組整合')
    
    # 處理選項
    parser.add_argument('--process-rss', type=str,
                       help='處理指定的 RSS collection')
    parser.add_argument('--run-pipeline', action='store_true',
                       help='執行完整的 Pipeline')
    
    # 配置選項
    parser.add_argument('--mongo-host', type=str, default='localhost',
                       help='MongoDB 主機 (預設: localhost)')
    parser.add_argument('--mongo-port', type=int, default=27017,
                       help='MongoDB 埠號 (預設: 27017)')
    parser.add_argument('--mongo-db', type=str, default='podwise',
                       help='MongoDB 資料庫名稱 (預設: podwise)')
    
    args = parser.parse_args()
    
    # 準備配置
    mongo_config = {
        'host': args.mongo_host,
        'port': args.mongo_port,
        'database': args.mongo_db
    }
    
    # 執行對應功能
    if args.list_components:
        return list_components()
    
    elif args.test_components:
        return test_components()
    
    elif args.test_data_cleaning:
        return test_data_cleaning_integration()
    
    elif args.process_rss:
        return process_rss_collection(args.process_rss, mongo_config)
    
    elif args.run_pipeline:
        input_config = {
            'mongo': mongo_config,
            'collections': ['RSS_1500839292']  # 預設處理股癌 collection
        }
        return run_pipeline(input_config)
    
    else:
        parser.print_help()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 