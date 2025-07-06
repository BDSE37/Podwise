#!/usr/bin/env python3
"""
資料清整和匯入整合腳本
1. 執行資料清整
2. 將清整後的資料匯入 PostgreSQL
"""

import os
import sys
import logging
from datetime import datetime

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_data_cleanup():
    """執行資料清整"""
    try:
        logger.info("=== 開始執行資料清整 ===")
        
        # 導入清整模組
        from cleanup_service import CleanupService
        from config import Config
        
        # 建立設定和服務
        config = Config()
        service = CleanupService(config)
        
        # 執行本地清整測試
        result = service.run_local_test(sample_size=100)
        
        if result.get("success"):
            logger.info("✅ 資料清整成功")
            logger.info(f"處理了 {result.get('total_episodes', 0)} 筆資料")
            logger.info(f"成功處理 {result.get('success_count', 0)} 筆")
            logger.info(f"JSON 輸出: {result.get('json_output', '')}")
            logger.info(f"CSV 輸出: {result.get('csv_output', '')}")
            return True
        else:
            logger.error(f"❌ 資料清整失敗: {result.get('error', '未知錯誤')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 資料清整執行失敗: {e}")
        return False

def run_data_import():
    """執行資料匯入"""
    try:
        logger.info("=== 開始執行資料匯入 ===")
        
        # 檢查清整資料是否存在
        cleaned_data_path = "../../data/cleaned_data/processed_episodes.json"
        if not os.path.exists(cleaned_data_path):
            logger.error(f"❌ 找不到清整資料檔案: {cleaned_data_path}")
            logger.info("請先執行資料清整")
            return False
        
        # 導入匯入模組
        from insert_to_postgres import PostgreSQLInserter
        
        # 資料庫配置
        config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB', 'podcast'),
            'user': os.getenv('POSTGRES_USER', 'bdse37'),
            'password': os.getenv('POSTGRES_PASSWORD', '111111')
        }
        
        # 建立匯入器
        inserter = PostgreSQLInserter(config)
        
        # 載入並處理資料
        cleaned_data = inserter.load_cleaned_data(cleaned_data_path)
        result = inserter.process_cleaned_data(cleaned_data)
        
        logger.info("✅ 資料匯入成功")
        logger.info(f"總 Episodes: {result.get('total_episodes', 0)}")
        logger.info(f"成功插入: {result.get('successful_inserts', 0)}")
        logger.info(f"失敗插入: {result.get('failed_inserts', 0)}")
        logger.info(f"Podcast 數量: {result.get('podcast_count', 0)}")
        
        inserter.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ 資料匯入執行失敗: {e}")
        return False

def main():
    """主程式"""
    logger.info("=== 資料清整和匯入整合流程 ===")
    logger.info(f"開始時間: {datetime.now()}")
    
    # 步驟 1: 資料清整
    cleanup_success = run_data_cleanup()
    
    if not cleanup_success:
        logger.error("資料清整失敗，停止執行")
        sys.exit(1)
    
    # 步驟 2: 資料匯入
    import_success = run_data_import()
    
    if not import_success:
        logger.error("資料匯入失敗")
        sys.exit(1)
    
    logger.info("=== 整合流程完成 ===")
    logger.info(f"完成時間: {datetime.now()}")
    logger.info("🎉 所有步驟執行成功！")

if __name__ == "__main__":
    main() 