#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Cleaning 模組主程式入口點

提供統一的命令列介面，方便調用所有清理功能。

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

def list_cleaners():
    """列出所有可用的清理器"""
    try:
        from data_cleaning import (
            BaseCleaner, MongoCleaner, StockCancerCleaner, 
            LongTextCleaner, EpisodeCleaner, PodcastCleaner
        )
        
        cleaners = {
            "BaseCleaner": "基底清理器（抽象類別）",
            "MongoCleaner": "MongoDB 文檔清理器",
            "StockCancerCleaner": "股癌節目專用清理器",
            "LongTextCleaner": "長文本清理器",
            "EpisodeCleaner": "Episode 資料清理器",
            "PodcastCleaner": "Podcast 資料清理器"
        }
        
        print("可用的清理器：")
        print("=" * 50)
        for name, description in cleaners.items():
            print(f"• {name}: {description}")
        print("=" * 50)
        
    except ImportError as e:
        logger.error(f"無法載入清理器: {e}")
        return False
    
    return True

def test_cleaners():
    """測試所有清理器"""
    try:
        from data_cleaning import MongoCleaner, StockCancerCleaner, LongTextCleaner
        
        print("測試清理器功能...")
        print("=" * 50)
        
        # 測試 LongTextCleaner
        print("1. 測試 LongTextCleaner")
        longtext_cleaner = LongTextCleaner()
        test_text = "Hello 😊 World :) 這是一個測試文本 🚀"
        cleaned_text = longtext_cleaner.clean(test_text)
        print(f"   原始: {test_text}")
        print(f"   清理後: {cleaned_text}")
        print()
        
        # 測試 StockCancerCleaner
        print("2. 測試 StockCancerCleaner")
        stock_cleaner = StockCancerCleaner()
        test_data = {
            "episode_title": "EP572 | 🐌 2025 過一半了== 本集節目由【NordVPN】贊助",
            "description": "晦澀金融投資知識直白講，重要海內外時事輕鬆談..."
        }
        cleaned_data = stock_cleaner.clean(test_data)
        print(f"   原始標題: {test_data['episode_title']}")
        print(f"   清理後標題: {cleaned_data['episode_title']}")
        print()
        
        # 測試 MongoCleaner
        print("3. 測試 MongoCleaner")
        mongo_cleaner = MongoCleaner()
        test_doc = {
            "text": "這是一個 MongoDB 文檔 😊 包含表情符號 :)",
            "title": "測試標題 🚀",
            "description": "測試描述 :D"
        }
        cleaned_doc = mongo_cleaner.clean(test_doc)
        print(f"   原始文檔: {test_doc}")
        print(f"   清理後文檔: {cleaned_doc}")
        print()
        
        print("所有清理器測試完成！")
        return True
        
    except Exception as e:
        logger.error(f"測試清理器失敗: {e}")
        return False

def clean_data(input_file: str, output_file: str):
    """清理資料檔案"""
    try:
        from data_cleaning.services import CleanerOrchestrator
        
        print(f"開始清理檔案: {input_file}")
        
        # 初始化協調器
        orchestrator = CleanerOrchestrator()
        
        # 清理檔案
        output_path = orchestrator.clean_file(input_file)
        
        print(f"清理完成！輸出檔案: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"清理資料失敗: {e}")
        return False

def process_stock_cancer(input_file: str, import_postgresql: bool = False):
    """處理股癌資料"""
    try:
        from data_cleaning.core import StockCancerCleaner
        from data_cleaning.utils import DataExtractor
        from data_cleaning.config import Config
        
        print(f"開始處理股癌資料: {input_file}")
        
        # 初始化
        config = Config()
        extractor = DataExtractor(config)
        cleaner = StockCancerCleaner()
        
        # 讀取資料
        with open(input_file, 'r', encoding='utf-8') as f:
            import json
            data = json.load(f)
        
        # 清理資料
        if isinstance(data, list):
            cleaned_data = cleaner.batch_clean_documents(data)
        else:
            cleaned_data = cleaner.clean(data)
        
        # 儲存結果
        output_file = input_file.replace('.json', '_cleaned.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        
        print(f"股癌資料處理完成！輸出檔案: {output_file}")
        
        # 匯入 PostgreSQL
        if import_postgresql:
            print("開始匯入 PostgreSQL...")
            from data_cleaning.utils import DBUtils
            
            db_utils = DBUtils(config.get_db_config())
            db_utils.connect()
            
            success_count = 0
            if isinstance(cleaned_data, list):
                for doc in cleaned_data:
                    if doc.get('cleaning_status') != 'error':
                        if db_utils.insert_episode(doc):
                            success_count += 1
            else:
                if cleaned_data.get('cleaning_status') != 'error':
                    if db_utils.insert_episode(cleaned_data):
                        success_count += 1
            
            db_utils.disconnect()
            print(f"PostgreSQL 匯入完成！成功插入 {success_count} 筆資料")
        
        return True
        
    except Exception as e:
        logger.error(f"處理股癌資料失敗: {e}")
        return False

def import_postgresql(input_file: str):
    """匯入資料到 PostgreSQL"""
    try:
        from data_cleaning.utils import DBUtils, DataExtractor
        from data_cleaning.config import Config
        
        print(f"開始匯入 PostgreSQL: {input_file}")
        
        # 初始化
        config = Config()
        db_utils = DBUtils(config.get_db_config())
        extractor = DataExtractor(config)
        
        # 讀取資料
        with open(input_file, 'r', encoding='utf-8') as f:
            import json
            data = json.load(f)
        
        # 連接資料庫
        db_utils.connect()
        
        # 插入資料
        success_count = 0
        if isinstance(data, list):
            for doc in data:
                if doc.get('cleaning_status') != 'error':
                    if db_utils.insert_episode(doc):
                        success_count += 1
        else:
            if data.get('cleaning_status') != 'error':
                if db_utils.insert_episode(data):
                    success_count += 1
        
        # 關閉連接
        db_utils.disconnect()
        
        print(f"PostgreSQL 匯入完成！成功插入 {success_count} 筆資料")
        return True
        
    except Exception as e:
        logger.error(f"匯入 PostgreSQL 失敗: {e}")
        return False

def run_service_test(test_type: str, sample_size: int = 100):
    """執行服務測試"""
    try:
        from data_cleaning.services import CleanupService
        from data_cleaning.config import Config
        
        print(f"開始執行 {test_type} 測試...")
        
        # 初始化服務
        config = Config()
        service = CleanupService(config)
        
        # 執行測試
        if test_type == "local":
            result = service.run_local_test(sample_size)
        elif test_type == "database":
            result = service.run_database_test(sample_size)
        elif test_type == "full":
            result = service.run_full_cleanup_test(sample_size)
        else:
            print(f"未知的測試類型: {test_type}")
            return False
        
        # 顯示結果
        if result.get('success'):
            print("測試成功！")
            print(f"結果: {result}")
        else:
            print("測試失敗！")
            print(f"錯誤: {result.get('error')}")
        
        return result.get('success', False)
        
    except Exception as e:
        logger.error(f"執行服務測試失敗: {e}")
        return False

def main():
    """主程式入口點"""
    parser = argparse.ArgumentParser(
        description="Data Cleaning 模組命令列工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 列出所有清理器
  python main.py --list-cleaners
  
  # 測試清理器
  python main.py --test-cleaners
  
  # 清理資料檔案
  python main.py --clean --input data.json --output cleaned_data.json
  
  # 處理股癌資料
  python main.py --process-stock-cancer --input stock_cancer.json
  
  # 處理股癌資料並匯入 PostgreSQL
  python main.py --process-stock-cancer --input stock_cancer.json --import-postgresql
  
  # 匯入 PostgreSQL
  python main.py --import-postgresql --input cleaned_data.json
  
  # 執行服務測試
  python main.py --service-test local --sample-size 50
  python main.py --service-test database --sample-size 50
  python main.py --service-test full --sample-size 50
        """
    )
    
    # 基本選項
    parser.add_argument('--list-cleaners', action='store_true',
                       help='列出所有可用的清理器')
    parser.add_argument('--test-cleaners', action='store_true',
                       help='測試所有清理器功能')
    
    # 清理選項
    parser.add_argument('--clean', action='store_true',
                       help='清理資料檔案')
    parser.add_argument('--input', type=str,
                       help='輸入檔案路徑')
    parser.add_argument('--output', type=str,
                       help='輸出檔案路徑')
    
    # 股癌處理選項
    parser.add_argument('--process-stock-cancer', action='store_true',
                       help='處理股癌資料')
    parser.add_argument('--import-postgresql', action='store_true',
                       help='匯入資料到 PostgreSQL')
    
    # 服務測試選項
    parser.add_argument('--service-test', type=str, choices=['local', 'database', 'full'],
                       help='執行服務測試 (local/database/full)')
    parser.add_argument('--sample-size', type=int, default=100,
                       help='測試樣本大小 (預設: 100)')
    
    args = parser.parse_args()
    
    # 執行對應功能
    if args.list_cleaners:
        return list_cleaners()
    
    elif args.test_cleaners:
        return test_cleaners()
    
    elif args.clean:
        if not args.input:
            print("錯誤: 清理資料需要指定 --input 參數")
            return False
        return clean_data(args.input, args.output or f"cleaned_{args.input}")
    
    elif args.process_stock_cancer:
        if not args.input:
            print("錯誤: 處理股癌資料需要指定 --input 參數")
            return False
        return process_stock_cancer(args.input, args.import_postgresql)
    
    elif args.import_postgresql:
        if not args.input:
            print("錯誤: 匯入 PostgreSQL 需要指定 --input 參數")
            return False
        return import_postgresql(args.input)
    
    elif args.service_test:
        return run_service_test(args.service_test, args.sample_size)
    
    else:
        parser.print_help()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 