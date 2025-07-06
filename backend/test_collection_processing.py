#!/usr/bin/env python3
"""
Collection 處理測試腳本
測試長文本切分、標籤處理和向量化功能
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any

# 添加父目錄到路徑
sys.path.append(str(Path(__file__).parent))

from process_collections import CollectionProcessor, TextCleaner

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_text_cleaner():
    """測試文本清理器"""
    print("=== 測試文本清理器 ===")
    
    cleaner = TextCleaner()
    
    # 測試案例
    test_cases = [
        "這是一個測試文本 😊 包含表情符號",
        "Hello World! 🌍 混合中英文",
        "股癌 EP123 📈 投資理財 💰",
        "科技新聞 🔥 AI 人工智慧 🤖",
        "正常文本，沒有特殊字元",
        "包含顏文字 (｡◕‿◕｡) 的文本",
        "多個表情符號 🎉🎊🎈 測試",
        ""
    ]
    
    for i, text in enumerate(test_cases):
        cleaned = cleaner.clean_text(text)
        print(f"原始: {text}")
        print(f"清理後: {cleaned}")
        print(f"長度變化: {len(text)} -> {len(cleaned)}")
        print("-" * 50)
    
    # 測試標題清理
    print("\n=== 測試標題清理 ===")
    title_test_cases = [
        "EP001_股癌 📈 投資理財",
        "科技新聞 🔥 AI 人工智慧",
        "正常標題，沒有特殊字元",
        "包含表情符號的標題 🎉"
    ]
    
    for title in title_test_cases:
        cleaned_title = cleaner.clean_title(title)
        print(f"原始標題: {title}")
        print(f"清理後標題: {cleaned_title}")
        print("-" * 30)


def test_text_chunking():
    """測試文本切分"""
    print("\n=== 測試文本切分 ===")
    
    # 模擬配置
    mongo_config = {
        'host': 'localhost',
        'port': 27017,
        'database': 'podwise'
    }
    
    postgres_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'podwise',
        'user': 'postgres',
        'password': 'postgres'
    }
    
    milvus_config = {
        'host': 'localhost',
        'port': 19530
    }
    
    try:
        processor = CollectionProcessor(
            mongo_config=mongo_config,
            postgres_config=postgres_config,
            milvus_config=milvus_config,
            max_chunk_size=500  # 較小的 chunk 大小用於測試
        )
        
        # 測試文本
        test_text = """
        這是第一段文本。它包含了一些基本的內容。我們需要測試文本切分功能是否正常工作。
        
        這是第二段文本。它討論了人工智慧和機器學習的相關話題。AI技術正在快速發展。
        
        這是第三段文本。它談論了投資理財的重要性。股票市場充滿了機會和風險。
        
        這是第四段文本。它介紹了創業的基本概念。新創公司需要創新思維和執行力。
        
        這是第五段文本。它討論了健康生活的重要性。運動和飲食對身體健康至關重要。
        """
        
        chunks = processor.split_text_into_chunks(test_text)
        
        print(f"原始文本長度: {len(test_text)}")
        print(f"切分後 chunks 數量: {len(chunks)}")
        
        for i, chunk in enumerate(chunks):
            print(f"\nChunk {i+1} (長度: {len(chunk)}):")
            print(f"內容: {chunk[:100]}{'...' if len(chunk) > 100 else ''}")
            
            # 測試標籤提取
            tags = processor.extract_tags(chunk)
            print(f"提取的標籤: {tags}")
        
        processor.close()
        
    except Exception as e:
        print(f"測試失敗: {e}")


def test_tag_extraction():
    """測試標籤提取"""
    print("\n=== 測試標籤提取 ===")
    
    # 模擬配置
    mongo_config = {
        'host': 'localhost',
        'port': 27017,
        'database': 'podwise'
    }
    
    postgres_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'podwise',
        'user': 'postgres',
        'password': 'postgres'
    }
    
    milvus_config = {
        'host': 'localhost',
        'port': 19530
    }
    
    try:
        processor = CollectionProcessor(
            mongo_config=mongo_config,
            postgres_config=postgres_config,
            milvus_config=milvus_config
        )
        
        # 測試案例
        test_cases = [
            "人工智慧技術正在快速發展，機器學習和深度學習成為熱門話題。",
            "投資理財是現代人必須學習的技能，股票和基金投資需要謹慎。",
            "創業需要創新思維和執行力，新創公司面臨許多挑戰。",
            "健康生活包括運動和飲食，對身體健康至關重要。",
            "這是一段普通的文本，沒有明顯的關鍵字。",
            "科技新聞報導最新的技術發展，包括AI、區塊鏈等領域。",
            "教育學習是終身過程，知識和技能的提升對個人發展很重要。",
            "娛樂音樂讓人放鬆心情，電影和遊戲也是重要的休閒活動。"
        ]
        
        for i, text in enumerate(test_cases):
            print(f"\n測試案例 {i+1}: {text[:50]}...")
            tags = processor.extract_tags(text)
            print(f"提取的標籤: {tags}")
        
        processor.close()
        
    except Exception as e:
        print(f"測試失敗: {e}")


def test_connection():
    """測試資料庫連接"""
    print("\n=== 測試資料庫連接 ===")
    
    # 模擬配置
    mongo_config = {
        'host': 'localhost',
        'port': 27017,
        'database': 'podwise'
    }
    
    postgres_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'podwise',
        'user': 'postgres',
        'password': 'postgres'
    }
    
    milvus_config = {
        'host': 'localhost',
        'port': 19530
    }
    
    try:
        processor = CollectionProcessor(
            mongo_config=mongo_config,
            postgres_config=postgres_config,
            milvus_config=milvus_config
        )
        
        print("✅ 所有資料庫連接成功")
        
        # 測試 MongoDB 連接
        db = processor.mongo_client[processor.mongo_config['database']]
        collections = db.list_collection_names()
        print(f"MongoDB collections: {collections}")
        
        # 測試 PostgreSQL 連接
        with processor.postgres_conn.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            print(f"PostgreSQL 版本: {version[0]}")
        
        processor.close()
        
    except Exception as e:
        print(f"❌ 連接測試失敗: {e}")


def test_small_collection():
    """測試小規模 collection 處理"""
    print("\n=== 測試小規模 collection 處理 ===")
    
    # 模擬配置
    mongo_config = {
        'host': 'localhost',
        'port': 27017,
        'database': 'podwise'
    }
    
    postgres_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'podwise',
        'user': 'postgres',
        'password': 'postgres'
    }
    
    milvus_config = {
        'host': 'localhost',
        'port': 19530
    }
    
    try:
        processor = CollectionProcessor(
            mongo_config=mongo_config,
            postgres_config=postgres_config,
            milvus_config=milvus_config,
            max_chunk_size=500,
            batch_size=10
        )
        
        # 測試處理 collection 1500839292
        collection_name = "1500839292"
        
        # 先檢查 collection 是否存在
        db = processor.mongo_client[processor.mongo_config['database']]
        if collection_name in db.list_collection_names():
            print(f"找到 collection: {collection_name}")
            
            # 獲取文件數量
            collection = db[collection_name]
            doc_count = collection.count_documents({})
            print(f"文件數量: {doc_count}")
            
            if doc_count > 0:
                # 只處理前 3 個文件進行測試
                print("處理前 3 個文件進行測試...")
                
                # 獲取前 3 個文件
                test_docs = list(collection.find({}).limit(3))
                
                for i, doc in enumerate(test_docs):
                    print(f"\n處理文件 {i+1}:")
                    print(f"ID: {doc.get('_id')}")
                    print(f"Episode ID: {doc.get('episode_id')}")
                    print(f"標題: {doc.get('title', '')}")
                    
                    # 提取文本
                    text = doc.get('content', '')
                    if text:
                        print(f"文本長度: {len(text)}")
                        
                        # 切分文本
                        chunks = processor.split_text_into_chunks(text)
                        print(f"切分後 chunks: {len(chunks)}")
                        
                        # 處理第一個 chunk
                        if chunks:
                            first_chunk = chunks[0]
                            print(f"第一個 chunk: {first_chunk[:100]}...")
                            
                            # 提取標籤
                            tags = processor.extract_tags(first_chunk)
                            print(f"提取的標籤: {tags}")
                    else:
                        print("沒有文本內容")
        
        else:
            print(f"Collection {collection_name} 不存在")
        
        processor.close()
        
    except Exception as e:
        print(f"測試失敗: {e}")


def main():
    """主測試函數"""
    print("開始執行 Collection 處理測試")
    print("=" * 60)
    
    # 執行各種測試
    test_text_cleaner()
    test_text_chunking()
    test_tag_extraction()
    test_connection()
    test_small_collection()
    
    print("\n" + "=" * 60)
    print("所有測試完成！")


if __name__ == "__main__":
    main() 