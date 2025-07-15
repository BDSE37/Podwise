#!/usr/bin/env python3
"""
測試單個檔案處理結果
"""

import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from backend.utils.batch_process_with_progress import BatchProcessor

def test_single_file():
    """測試單個檔案處理"""
    print("=== 測試單個檔案處理 ===")
    
    # 初始化處理器
    processor = BatchProcessor()
    
    # 掃描檔案
    files = processor.scan_all_files()
    print(f"找到 {len(files)} 個檔案")
    
    if not files:
        print("❌ 沒有找到檔案")
        return
    
    # 選擇第一個檔案測試
    test_file = files[0]
    print(f"測試檔案: {test_file}")
    
    # 取得 PostgreSQL 資料
    pg_episodes = processor.get_postgresql_episodes()
    print(f"PostgreSQL 資料: {len(pg_episodes)} 筆")
    
    # 處理檔案
    chunks, fixed_data = processor.process_single_file(test_file, pg_episodes)
    print(f"處理結果: {len(chunks)} 個 chunks")
    
    if chunks:
        print("\n=== 第一個 chunk 欄位檢查 ===")
        chunk = chunks[0]
        for k, v in chunk.items():
            print(f"  {k}: {type(v).__name__} = {v}")
        
        print(f"\n=== 檔案資訊 ===")
        print(f"filename: {fixed_data.get('filename')}")
        print(f"episode_id: {fixed_data.get('episode_id')}")
        print(f"collection_name: {fixed_data.get('collection_name')}")
        print(f"total_chunks: {fixed_data.get('total_chunks')}")
        print(f"source_model: {fixed_data.get('source_model')}")
        
        # 檢查是否所有必要欄位都存在
        required_fields = [
            'chunk_id', 'chunk_index', 'episode_id', 'podcast_id', 
            'podcast_name', 'author', 'category', 'episode_title',
            'duration', 'published_date', 'apple_rating', 'chunk_text',
            'embedding', 'language', 'created_at', 'source_model', 'tags'
        ]
        
        print(f"\n=== 欄位完整性檢查 ===")
        missing_fields = []
        for field in required_fields:
            if field not in chunk:
                missing_fields.append(field)
            else:
                print(f"✅ {field}: {type(chunk[field]).__name__}")
        
        if missing_fields:
            print(f"❌ 缺少欄位: {missing_fields}")
        else:
            print("✅ 所有必要欄位都存在")
        
        # 檢查 PostgreSQL 資料是否正確補齊
        print(f"\n=== PostgreSQL 資料補齊檢查 ===")
        if chunk['episode_id'] > 0:
            print(f"✅ episode_id: {chunk['episode_id']} (來自 PostgreSQL)")
        else:
            print(f"⚠️ episode_id: {chunk['episode_id']} (使用預設值)")
        
        if chunk['podcast_name'] != '未知播客':
            print(f"✅ podcast_name: {chunk['podcast_name']} (來自 PostgreSQL)")
        else:
            print(f"⚠️ podcast_name: {chunk['podcast_name']} (使用預設值)")
        
        if chunk['author'] != '未知作者':
            print(f"✅ author: {chunk['author']} (來自 PostgreSQL)")
        else:
            print(f"⚠️ author: {chunk['author']} (使用預設值)")
        
        if chunk['duration'] != '未知時長':
            print(f"✅ duration: {chunk['duration']} (來自 PostgreSQL)")
        else:
            print(f"⚠️ duration: {chunk['duration']} (使用預設值)")
        
        # 檢查 tags 轉換
        print(f"\n=== Tags 轉換檢查 ===")
        print(f"原始 enhanced_tags 已轉換為 tags: {chunk['tags']}")
        
    else:
        print("❌ 處理失敗，沒有產生 chunks")

if __name__ == "__main__":
    test_single_file() 