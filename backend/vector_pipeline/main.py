#!/usr/bin/env python3
"""
Podwise 資料處理主程式
整合 MongoDB 資料下載、PostgreSQL 元資料查詢、文本分塊、標籤化和向量化功能
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# 添加父目錄到路徑
sys.path.append(str(Path(__file__).parent.parent))

from vector_pipeline.pipeline_orchestrator import PipelineOrchestrator
from config.mongo_config import MONGO_CONFIG
from config.db_config import POSTGRES_CONFIG, MILVUS_CONFIG

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main() -> None:
    """主程式"""
    parser = argparse.ArgumentParser(description="Podwise 資料處理管道")
    parser.add_argument("--action", choices=["process", "recreate", "search", "stats"], 
                       default="process", help="執行動作")
    parser.add_argument("--mongo-collection", default="RSS_1567737523", 
                       help="MongoDB 集合名稱")
    parser.add_argument("--milvus-collection", default="podcast_chunks", 
                       help="Milvus 集合名稱")
    parser.add_argument("--limit", type=int, help="限制處理文檔數量")
    parser.add_argument("--batch-size", type=int, default=100, 
                       help="批次處理大小")
    parser.add_argument("--query-text", help="搜尋查詢文本")
    parser.add_argument("--top-k", type=int, default=10, 
                       help="搜尋結果數量")
    parser.add_argument("--tag-csv", default="TAG_info.csv", 
                       help="標籤 CSV 檔案路徑")
    parser.add_argument("--embedding-model", default="BAAI/bge-m3", 
                       help="嵌入模型名稱")
    parser.add_argument("--max-chunk-size", type=int, default=1024, 
                       help="最大分塊大小")
    
    args = parser.parse_args()
    
    try:
        # 初始化 Pipeline Orchestrator
        orchestrator = PipelineOrchestrator(
            mongo_config=MONGO_CONFIG,
            postgres_config=POSTGRES_CONFIG,
            milvus_config=MILVUS_CONFIG,
            tag_csv_path=args.tag_csv,
            embedding_model=args.embedding_model,
            max_chunk_size=args.max_chunk_size,
            batch_size=args.batch_size
        )
        
        if args.action == "process":
            # 處理和向量化
            logger.info("開始處理和向量化...")
            stats = orchestrator.process_collection(
                mongo_collection=args.mongo_collection,
                milvus_collection=args.milvus_collection,
                limit=args.limit
            )
            logger.info(f"處理完成: {stats}")
            
        elif args.action == "recreate":
            # 重建集合
            logger.info("重建 Milvus 集合...")
            orchestrator.milvus_writer.drop_collection(args.milvus_collection)
            collection_name = orchestrator.milvus_writer.create_collection(args.milvus_collection)
            logger.info(f"集合重建完成: {collection_name}")
            
        elif args.action == "search":
            # 搜尋相似文檔
            if not args.query_text:
                logger.error("搜尋需要提供 --query-text 參數")
                return
                
            logger.info(f"搜尋相似文檔: {args.query_text}")
            # TODO: 實作搜尋功能
            logger.info("搜尋功能待實作")
            
        elif args.action == "stats":
            # 獲取統計資訊
            logger.info("獲取集合統計資訊...")
            stats = orchestrator.milvus_writer.get_collection_stats(args.milvus_collection)
            logger.info(f"集合統計: {stats}")
            
        else:
            logger.error(f"未知動作: {args.action}")
            
    except Exception as e:
        logger.error(f"執行失敗: {e}")
        sys.exit(1)
    finally:
        if 'orchestrator' in locals():
            orchestrator.close()


def interactive_mode() -> None:
    """互動模式"""
    print("🎙️ Podwise 資料處理管道")
    print("=" * 50)
    
    # 配置
    mongo_config = MONGO_CONFIG
    milvus_config = MILVUS_CONFIG
    postgres_config = POSTGRES_CONFIG
    
    orchestrator = PipelineOrchestrator(
        mongo_config=mongo_config,
        postgres_config=postgres_config,
        milvus_config=milvus_config
    )
    
    try:
        while True:
            print("\n請選擇操作:")
            print("1. 處理和向量化文檔")
            print("2. 重建集合")
            print("3. 搜尋相似文檔")
            print("4. 查看統計資訊")
            print("5. 退出")
            
            choice = input("\n請輸入選項 (1-5): ").strip()
            
            if choice == "1":
                # 處理和向量化
                mongo_collection = input("MongoDB 集合名稱 (預設: RSS_1567737523): ").strip() or "RSS_1567737523"
                milvus_collection = input("Milvus 集合名稱 (預設: podcast_chunks): ").strip() or "podcast_chunks"
                limit_str = input("限制文檔數量 (預設: 無限制): ").strip()
                limit: Optional[int] = int(limit_str) if limit_str else None
                
                print("開始處理...")
                stats = orchestrator.process_collection(
                    mongo_collection=mongo_collection,
                    milvus_collection=milvus_collection,
                    limit=limit
                )
                print(f"處理完成: {stats}")
                
            elif choice == "2":
                # 重建集合
                collection_name = input("集合名稱 (預設: podcast_chunks): ").strip() or "podcast_chunks"
                confirm = input(f"確定要重建集合 {collection_name} 嗎? (y/N): ").strip().lower()
                
                if confirm == 'y':
                    print("重建集合...")
                    orchestrator.milvus_writer.drop_collection(collection_name)
                    new_collection = orchestrator.milvus_writer.create_collection(collection_name)
                    print(f"集合重建完成: {new_collection}")
                else:
                    print("取消重建")
                    
            elif choice == "3":
                # 搜尋
                query_text = input("搜尋查詢: ").strip()
                if not query_text:
                    print("請輸入搜尋查詢")
                    continue
                    
                collection_name = input("集合名稱 (預設: podcast_chunks): ").strip() or "podcast_chunks"
                print("搜尋功能待實作")
                    
            elif choice == "4":
                # 統計資訊
                collection_name = input("集合名稱 (預設: podcast_chunks): ").strip() or "podcast_chunks"
                print("獲取統計資訊...")
                stats = orchestrator.milvus_writer.get_collection_stats(collection_name)
                print(f"集合統計: {stats}")
                
            elif choice == "5":
                print("再見！")
                break
                
            else:
                print("無效選項，請重新選擇")
                
    except KeyboardInterrupt:
        print("\n\n程式被中斷")
    except Exception as e:
        print(f"發生錯誤: {e}")
    finally:
        orchestrator.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 命令列模式
        main()
    else:
        # 互動模式
        interactive_mode() 