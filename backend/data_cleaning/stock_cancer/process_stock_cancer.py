#!/usr/bin/env python3
"""
股癌 Podcast 專用處理腳本
專門處理 Apple Podcast ID: 1500839292 的股癌節目資料
包含 MongoDB 資料清理和 PostgreSQL 插入功能
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StockCancerProcessor:
    """股癌資料處理器"""
    
    def __init__(self, output_dir: str = '../../data/cleaned_data'):
        """初始化處理器"""
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 導入清理器
        from stock_cancer_cleaner import StockCancerCleaner
        self.cleaner = StockCancerCleaner()
        
        # 資料庫配置
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB', 'podcast'),
            'user': os.getenv('POSTGRES_USER', 'bdse37'),
            'password': os.getenv('POSTGRES_PASSWORD', '111111')
        }
    
    def load_mongodb_data(self, file_path: str) -> List[Dict[str, Any]]:
        """載入 MongoDB 資料"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"成功載入 {len(data)} 筆 MongoDB 資料")
            return data
            
        except Exception as e:
            logger.error(f"載入 MongoDB 資料失敗: {e}")
            raise
    
    def filter_stock_cancer_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """過濾出股癌相關資料"""
        stock_cancer_data = []
        
        for doc in data:
            if self.cleaner._is_stock_cancer_podcast(doc):
                stock_cancer_data.append(doc)
        
        logger.info(f"找到 {len(stock_cancer_data)} 筆股癌相關資料")
        return stock_cancer_data
    
    def clean_stock_cancer_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """清理股癌資料"""
        logger.info("開始清理股癌資料")
        
        cleaned_data = self.cleaner.batch_clean_documents(data)
        
        # 統計結果
        success_count = len([doc for doc in cleaned_data if doc.get('cleaning_status') == 'completed'])
        error_count = len(cleaned_data) - success_count
        
        logger.info(f"清理完成: 成功 {success_count} 筆，失敗 {error_count} 筆")
        
        return cleaned_data
    
    def save_cleaned_data(self, data: List[Dict[str, Any]], filename: str = "stock_cancer_cleaned.json") -> str:
        """儲存清理後的資料"""
        output_path = os.path.join(self.output_dir, filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"清理資料已儲存至: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"儲存資料失敗: {e}")
            raise
    
    def prepare_postgresql_data(self, cleaned_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """準備 PostgreSQL 插入資料"""
        episodes_data = []
        podcast_data = None
        
        for doc in cleaned_data:
            if doc.get('cleaning_status') != 'completed':
                continue
            
            # 準備 episode 資料
            episode = {
                'episode_id': doc.get('_id', doc.get('episode_id')),
                'podcast_id': '1500839292',  # 股癌的 Apple Podcast ID
                'episode_title': doc.get('episode_title', doc.get('title', '')),
                'published_date': doc.get('published_date', doc.get('created', '')),
                'audio_url': doc.get('audio_url', ''),
                'duration': doc.get('duration', 0),
                'description': doc.get('description', doc.get('text', '')),
                'audio_preview_url': doc.get('audio_preview_url', ''),
                'languages': 'zh-TW',
                'explicit': False,
                'file_name': doc.get('file', ''),
                'cleaned_at': doc.get('cleaned_at', ''),
                'cleaner_type': doc.get('cleaner_type', '')
            }
            
            episodes_data.append(episode)
            
            # 準備 podcast 資料（只需要一次）
            if podcast_data is None:
                podcast_data = {
                    'podcast_id': '1500839292',
                    'name': '股癌',
                    'description': '股癌是由謝孟恭主持的投資理財 Podcast',
                    'author': '謝孟恭',
                    'rss_link': '',
                    'languages': 'zh-TW',
                    'category': '投資理財',
                    'apple_podcast_id': '1500839292'
                }
        
        return {
            'podcast': podcast_data,
            'episodes': episodes_data
        }
    
    def insert_to_postgresql(self, data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """插入資料到 PostgreSQL"""
        try:
            # 導入 PostgreSQL 插入器
            from insert_to_postgres import PostgreSQLInserter
            
            inserter = PostgreSQLInserter(self.db_config)
            
            # 插入 podcast 資料
            podcast_result = None
            if data['podcast']:
                podcast_id = inserter.insert_podcast(data['podcast'])
                podcast_result = {"podcast_id": podcast_id, "status": "success"}
                logger.info(f"Podcast 插入成功: ID {podcast_id}")
            
            # 插入 episodes 資料
            episodes_result = inserter.batch_insert_episodes(data['episodes'], podcast_id)
            
            inserter.close()
            
            result = {
                "podcast_insert": podcast_result,
                "episodes_inserted": len(episodes_result),
                "total_episodes": len(data['episodes']),
                "insert_time": datetime.now().isoformat()
            }
            
            logger.info(f"PostgreSQL 插入完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"PostgreSQL 插入失敗: {e}")
            raise
    
    def process_stock_cancer_file(self, input_file: str) -> Dict[str, Any]:
        """處理股癌資料檔案"""
        try:
            logger.info(f"開始處理股癌資料檔案: {input_file}")
            
            # 1. 載入資料
            raw_data = self.load_mongodb_data(input_file)
            
            # 2. 過濾股癌資料
            stock_cancer_data = self.filter_stock_cancer_data(raw_data)
            
            if not stock_cancer_data:
                logger.warning("沒有找到股癌相關資料")
                return {"status": "no_data", "message": "沒有找到股癌相關資料"}
            
            # 3. 清理資料
            cleaned_data = self.clean_stock_cancer_data(stock_cancer_data)
            
            # 4. 儲存清理資料
            output_file = self.save_cleaned_data(cleaned_data)
            
            # 5. 準備 PostgreSQL 資料
            pg_data = self.prepare_postgresql_data(cleaned_data)
            
            # 6. 插入 PostgreSQL
            insert_result = self.insert_to_postgresql(pg_data)
            
            # 7. 統計結果
            result = {
                "status": "success",
                "input_file": input_file,
                "output_file": output_file,
                "raw_data_count": len(raw_data),
                "stock_cancer_count": len(stock_cancer_data),
                "cleaned_count": len([d for d in cleaned_data if d.get('cleaning_status') == 'completed']),
                "postgresql_result": insert_result,
                "processing_time": datetime.now().isoformat()
            }
            
            logger.info(f"股癌資料處理完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"處理股癌資料失敗: {e}")
            return {"status": "error", "error": str(e)}
    
    def process_stock_cancer_collection(self, collection_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """處理股癌 collection 資料"""
        try:
            logger.info("開始處理股癌 collection 資料")
            
            # 1. 過濾股癌資料
            stock_cancer_data = self.filter_stock_cancer_data(collection_data)
            
            if not stock_cancer_data:
                logger.warning("沒有找到股癌相關資料")
                return {"status": "no_data", "message": "沒有找到股癌相關資料"}
            
            # 2. 清理資料
            cleaned_data = self.clean_stock_cancer_data(stock_cancer_data)
            
            # 3. 儲存清理資料
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.save_cleaned_data(cleaned_data, f"stock_cancer_cleaned_{timestamp}.json")
            
            # 4. 準備 PostgreSQL 資料
            pg_data = self.prepare_postgresql_data(cleaned_data)
            
            # 5. 插入 PostgreSQL
            insert_result = self.insert_to_postgresql(pg_data)
            
            # 6. 統計結果
            result = {
                "status": "success",
                "output_file": output_file,
                "collection_data_count": len(collection_data),
                "stock_cancer_count": len(stock_cancer_data),
                "cleaned_count": len([d for d in cleaned_data if d.get('cleaning_status') == 'completed']),
                "postgresql_result": insert_result,
                "processing_time": datetime.now().isoformat()
            }
            
            logger.info(f"股癌 collection 處理完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"處理股癌 collection 失敗: {e}")
            return {"status": "error", "error": str(e)}


def main():
    """主程式"""
    import argparse
    
    parser = argparse.ArgumentParser(description='股癌 Podcast 專用處理工具')
    parser.add_argument('--input-file', type=str, help='輸入檔案路徑')
    parser.add_argument('--output-dir', type=str, default='../../data/cleaned_data', 
                       help='輸出目錄路徑')
    parser.add_argument('--skip-postgresql', action='store_true', 
                       help='跳過 PostgreSQL 插入')
    
    args = parser.parse_args()
    
    try:
        # 建立處理器
        processor = StockCancerProcessor(args.output_dir)
        
        if args.input_file:
            # 處理檔案
            if not os.path.exists(args.input_file):
                logger.error(f"輸入檔案不存在: {args.input_file}")
                sys.exit(1)
            
            result = processor.process_stock_cancer_file(args.input_file)
            
        else:
            logger.error("請指定輸入檔案路徑")
            sys.exit(1)
        
        # 輸出結果
        if result.get("status") == "success":
            logger.info("✅ 股癌資料處理成功")
            logger.info(f"原始資料: {result.get('raw_data_count', 0)} 筆")
            logger.info(f"股癌資料: {result.get('stock_cancer_count', 0)} 筆")
            logger.info(f"清理成功: {result.get('cleaned_count', 0)} 筆")
            logger.info(f"輸出檔案: {result.get('output_file', '')}")
            
            if not args.skip_postgresql:
                pg_result = result.get('postgresql_result', {})
                logger.info(f"PostgreSQL 插入: {pg_result.get('episodes_inserted', 0)} 筆")
            
            sys.exit(0)
        else:
            logger.error(f"❌ 處理失敗: {result.get('error', '未知錯誤')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("使用者中斷操作")
        sys.exit(1)
    except Exception as e:
        logger.error(f"執行時發生錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 