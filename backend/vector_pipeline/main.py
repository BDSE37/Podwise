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

from vector_pipeline.vector_pipeline import VectorPipeline
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
    parser.add_argument("--mongo-collection", default="transcripts", 
                       help="MongoDB 集合名稱")
    parser.add_argument("--milvus-collection", default="podwise_podcasts", 
                       help="Milvus 集合名稱")
    parser.add_argument("--text-field", default="content", 
                       help="文本欄位名稱")
    parser.add_argument("--limit", type=int, help="限制處理文檔數量")
    parser.add_argument("--batch-size", type=int, default=100, 
                       help="批次處理大小")
    parser.add_argument("--query-text", help="搜尋查詢文本")
    parser.add_argument("--top-k", type=int, default=10, 
                       help="搜尋結果數量")
    parser.add_argument("--tag-csv", default="csv/TAG_info.csv", 
                       help="標籤 CSV 檔案路徑")
    parser.add_argument("--embedding-model", default="BAAI/bge-m3", 
                       help="嵌入模型名稱")
    parser.add_argument("--max-chunk-size", type=int, default=1024, 
                       help="最大分塊大小")
    
    args = parser.parse_args()
    
    try:
        # 初始化向量化管道
        pipeline = VectorPipeline(
            mongo_config=MONGO_CONFIG,
            milvus_config=MILVUS_CONFIG,
            postgres_config=POSTGRES_CONFIG,
            tag_csv_path=args.tag_csv,
            embedding_model=args.embedding_model,
            max_chunk_size=args.max_chunk_size
        )
        
        if args.action == "process":
            # 處理和向量化
            logger.info("開始處理和向量化...")
            stats = pipeline.process_and_vectorize(
                collection_name=args.milvus_collection,
                mongo_collection=args.mongo_collection,
                text_field=args.text_field,
                limit=args.limit,
                batch_size=args.batch_size
            )
            logger.info(f"處理完成: {stats}")
            
        elif args.action == "recreate":
            # 重建集合
            logger.info("重建 Milvus 集合...")
            collection_name = pipeline.recreate_collection(args.milvus_collection)
            logger.info(f"集合重建完成: {collection_name}")
            
        elif args.action == "search":
            # 搜尋相似文檔
            if not args.query_text:
                logger.error("搜尋需要提供 --query-text 參數")
                return
                
            logger.info(f"搜尋相似文檔: {args.query_text}")
            results = pipeline.search_similar(
                query_text=args.query_text,
                collection_name=args.milvus_collection,
                top_k=args.top_k
            )
            
            logger.info(f"搜尋結果 ({len(results)} 個):")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. 相似度: {result['score']:.4f}")
                print(f"   標題: {result['episode_title']}")
                print(f"   播客: {result['podcast_name']}")
                print(f"   標籤: {', '.join(result['tags'])}")
                print(f"   內容: {result['chunk_text'][:200]}...")
                
        elif args.action == "stats":
            # 獲取統計資訊
            logger.info("獲取集合統計資訊...")
            stats = pipeline.get_collection_stats(args.milvus_collection)
            logger.info(f"集合統計: {stats}")
            
        else:
            logger.error(f"未知動作: {args.action}")
            
    except Exception as e:
        logger.error(f"執行失敗: {e}")
        sys.exit(1)
    finally:
        if 'pipeline' in locals():
            pipeline.close()


def interactive_mode() -> None:
    """互動模式"""
    print("🎙️ Podwise 資料處理管道")
    print("=" * 50)
    
    # 配置
    mongo_config = MONGO_CONFIG
    milvus_config = MILVUS_CONFIG
    postgres_config = POSTGRES_CONFIG
    
    pipeline = VectorPipeline(
        mongo_config=mongo_config,
        milvus_config=milvus_config,
        postgres_config=postgres_config
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
                mongo_collection = input("MongoDB 集合名稱 (預設: transcripts): ").strip() or "transcripts"
                milvus_collection = input("Milvus 集合名稱 (預設: podwise_podcasts): ").strip() or "podwise_podcasts"
                limit_str = input("限制文檔數量 (預設: 無限制): ").strip()
                limit: Optional[int] = int(limit_str) if limit_str else None
                
                print("開始處理...")
                stats = pipeline.process_and_vectorize(
                    collection_name=milvus_collection,
                    mongo_collection=mongo_collection,
                    limit=limit
                )
                print(f"處理完成: {stats}")
                
            elif choice == "2":
                # 重建集合
                collection_name = input("集合名稱 (預設: podwise_podcasts): ").strip() or "podwise_podcasts"
                confirm = input(f"確定要重建集合 {collection_name} 嗎? (y/N): ").strip().lower()
                
                if confirm == 'y':
                    print("重建集合...")
                    new_collection = pipeline.recreate_collection(collection_name)
                    print(f"集合重建完成: {new_collection}")
                else:
                    print("取消重建")
                    
            elif choice == "3":
                # 搜尋
                query_text = input("搜尋查詢: ").strip()
                if not query_text:
                    print("請輸入搜尋查詢")
                    continue
                    
                collection_name = input("集合名稱 (預設: podwise_podcasts): ").strip() or "podwise_podcasts"
                top_k_str = input("結果數量 (預設: 10): ").strip()
                top_k = int(top_k_str) if top_k_str else 10
                
                print("搜尋中...")
                results = pipeline.search_similar(
                    query_text=query_text,
                    collection_name=collection_name,
                    top_k=top_k
                )
                
                print(f"\n搜尋結果 ({len(results)} 個):")
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. 相似度: {result['score']:.4f}")
                    print(f"   標題: {result['episode_title']}")
                    print(f"   播客: {result['podcast_name']}")
                    print(f"   標籤: {', '.join(result['tags'])}")
                    print(f"   內容: {result['chunk_text'][:200]}...")
                    
            elif choice == "4":
                # 統計資訊
                collection_name = input("集合名稱 (預設: podwise_podcasts): ").strip() or "podwise_podcasts"
                print("獲取統計資訊...")
                stats = pipeline.get_collection_stats(collection_name)
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
        pipeline.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 命令列模式
        main()
    else:
        # 互動模式
        interactive_mode() 