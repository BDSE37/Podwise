"""
更新 MongoDB 節目標題腳本
將 collection 1500839292 中的節目標題改為 EPXXX_股癌 格式
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Any
from pymongo import MongoClient
from datetime import datetime

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('update_titles.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PodcastTitleUpdater:
    """播客標題更新器"""
    
    def __init__(self, mongo_config: Dict[str, Any]):
        """
        初始化更新器
        
        Args:
            mongo_config: MongoDB 配置
        """
        self.mongo_config = mongo_config
        self.client = None
        self.db = None
        self.collection = None
        
    def connect_mongodb(self) -> bool:
        """連接 MongoDB"""
        try:
            self.client = MongoClient(
                host=self.mongo_config['host'],
                port=self.mongo_config['port']
            )
            self.db = self.client[self.mongo_config['database']]
            self.collection = self.db[self.mongo_config['collection']]
            
            # 測試連接
            self.client.admin.command('ping')
            logger.info("MongoDB 連接成功")
            return True
            
        except Exception as e:
            logger.error(f"MongoDB 連接失敗: {e}")
            return False
    
    def get_podcasts(self, collection_id: str = "1500839292") -> List[Dict[str, Any]]:
        """
        獲取指定 collection 的節目列表
        
        Args:
            collection_id: Collection ID
            
        Returns:
            節目列表
        """
        try:
            # 查詢指定 collection 的節目
            query = {"collection_id": collection_id}
            
            # 可以根據需要添加排序條件
            # 例如按創建時間排序：sort=[("created_at", 1)]
            # 或者按原有順序：sort=[("_id", 1)]
            
            podcasts = list(self.collection.find(query).sort("_id", 1))
            logger.info(f"找到 {len(podcasts)} 個節目")
            
            return podcasts
            
        except Exception as e:
            logger.error(f"獲取節目列表失敗: {e}")
            return []
    
    def backup_original_titles(self, podcasts: List[Dict[str, Any]]) -> None:
        """
        備份原始標題
        
        Args:
            podcasts: 節目列表
        """
        try:
            backup_data = []
            for podcast in podcasts:
                backup_data.append({
                    "podcast_id": podcast.get("_id"),
                    "original_title": podcast.get("title", ""),
                    "backup_time": datetime.now().isoformat()
                })
            
            # 儲存備份到檔案
            backup_file = f"title_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            import json
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"原始標題已備份到: {backup_file}")
            
        except Exception as e:
            logger.error(f"備份原始標題失敗: {e}")
    
    def update_titles(self, podcasts: List[Dict[str, Any]], 
                     collection_name: str = "股癌") -> Dict[str, Any]:
        """
        更新節目標題
        
        Args:
            podcasts: 節目列表
            collection_name: Collection 名稱（預設為"股癌"）
            
        Returns:
            更新結果統計
        """
        try:
            update_stats = {
                "total": len(podcasts),
                "updated": 0,
                "failed": 0,
                "errors": []
            }
            
            for i, podcast in enumerate(podcasts, 1):
                try:
                    # 生成新標題：EP001_股癌, EP002_股癌, ...
                    new_title = f"EP{i:03d}_{collection_name}"
                    
                    # 更新標題
                    result = self.collection.update_one(
                        {"_id": podcast["_id"]},
                        {
                            "$set": {
                                "title": new_title,
                                "original_title": podcast.get("title", ""),  # 保留原始標題
                                "title_updated_at": datetime.now().isoformat()
                            }
                        }
                    )
                    
                    if result.modified_count > 0:
                        update_stats["updated"] += 1
                        logger.info(f"更新成功: {podcast.get('title', 'N/A')} -> {new_title}")
                    else:
                        update_stats["failed"] += 1
                        logger.warning(f"更新失敗: {podcast.get('title', 'N/A')}")
                        
                except Exception as e:
                    update_stats["failed"] += 1
                    error_msg = f"更新節目 {podcast.get('_id')} 失敗: {e}"
                    update_stats["errors"].append(error_msg)
                    logger.error(error_msg)
            
            return update_stats
            
        except Exception as e:
            logger.error(f"批次更新標題失敗: {e}")
            return {"total": 0, "updated": 0, "failed": 0, "errors": [str(e)]}
    
    def preview_updates(self, podcasts: List[Dict[str, Any]], 
                       collection_name: str = "股癌") -> None:
        """
        預覽更新內容（不實際執行更新）
        
        Args:
            podcasts: 節目列表
            collection_name: Collection 名稱
        """
        logger.info("=== 預覽更新內容 ===")
        
        for i, podcast in enumerate(podcasts[:10], 1):  # 只顯示前10個
            old_title = podcast.get("title", "N/A")
            new_title = f"EP{i:03d}_{collection_name}"
            logger.info(f"{i:3d}. {old_title} -> {new_title}")
        
        if len(podcasts) > 10:
            logger.info(f"... 還有 {len(podcasts) - 10} 個節目")
        
        logger.info(f"總共將更新 {len(podcasts)} 個節目")
    
    def run_update(self, collection_id: str = "1500839292", 
                   collection_name: str = "股癌", 
                   preview_only: bool = False) -> bool:
        """
        執行更新流程
        
        Args:
            collection_id: Collection ID
            collection_name: Collection 名稱
            preview_only: 是否只預覽不執行
            
        Returns:
            是否成功
        """
        try:
            # 1. 連接 MongoDB
            if not self.connect_mongodb():
                return False
            
            # 2. 獲取節目列表
            podcasts = self.get_podcasts(collection_id)
            if not podcasts:
                logger.error("沒有找到節目")
                return False
            
            # 3. 備份原始標題
            self.backup_original_titles(podcasts)
            
            # 4. 預覽更新內容
            self.preview_updates(podcasts, collection_name)
            
            if preview_only:
                logger.info("預覽模式，不執行實際更新")
                return True
            
            # 5. 確認是否執行
            confirm = input("\n是否要執行更新？(y/N): ").strip().lower()
            if confirm != 'y':
                logger.info("取消更新")
                return True
            
            # 6. 執行更新
            logger.info("開始執行更新...")
            update_stats = self.update_titles(podcasts, collection_name)
            
            # 7. 顯示結果
            logger.info("=== 更新結果 ===")
            logger.info(f"總數: {update_stats['total']}")
            logger.info(f"成功: {update_stats['updated']}")
            logger.info(f"失敗: {update_stats['failed']}")
            
            if update_stats['errors']:
                logger.error("錯誤詳情:")
                for error in update_stats['errors']:
                    logger.error(f"  - {error}")
            
            return update_stats['failed'] == 0
            
        except Exception as e:
            logger.error(f"執行更新流程失敗: {e}")
            return False
        finally:
            if self.client:
                self.client.close()
                logger.info("MongoDB 連接已關閉")


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='更新播客標題')
    parser.add_argument('--collection-id', default='1500839292', 
                       help='Collection ID (預設: 1500839292)')
    parser.add_argument('--collection-name', default='股癌', 
                       help='Collection 名稱 (預設: 股癌)')
    parser.add_argument('--preview', action='store_true', 
                       help='只預覽不執行更新')
    parser.add_argument('--host', default='localhost', 
                       help='MongoDB 主機 (預設: localhost)')
    parser.add_argument('--port', type=int, default=27017, 
                       help='MongoDB 端口 (預設: 27017)')
    parser.add_argument('--database', default='podwise', 
                       help='資料庫名稱 (預設: podwise)')
    parser.add_argument('--collection', default='podcasts', 
                       help='Collection 名稱 (預設: podcasts)')
    
    args = parser.parse_args()
    
    # MongoDB 配置
    mongo_config = {
        'host': args.host,
        'port': args.port,
        'database': args.database,
        'collection': args.collection
    }
    
    # 建立更新器
    updater = PodcastTitleUpdater(mongo_config)
    
    # 執行更新
    success = updater.run_update(
        collection_id=args.collection_id,
        collection_name=args.collection_name,
        preview_only=args.preview
    )
    
    if success:
        logger.info("更新流程完成")
    else:
        logger.error("更新流程失敗")
        sys.exit(1)


if __name__ == "__main__":
    main() 