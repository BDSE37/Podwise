#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 Milvus 資料轉換功能
"""

import os
import sys
import json
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from convert_to_milvus_format import MilvusDataConverter


def test_single_file_conversion():
    """測試單個檔案轉換"""
    print("🧪 測試單個檔案轉換...")
    
    # 建立測試資料
    test_data = {
        "filename": "RSS_262026947_podcast_1304_3D printers.json",
        "episode_id": "6865015b66c1a4e8d1176616",
        "collection_name": "RSS_262026947",
        "total_chunks": 13,
        "chunks": [
            {
                "chunk_text": "This is a download from BBC Learning English. To find out more, visit our website.",
                "chunk_id": "be646042-981e-4558-ab38-da7cc3f0b9c8",
                "chunk_index": 0,
                "episode_id": "6865015b66c1a4e8d1176616",
                "original_filename": "RSS_262026947_podcast_1304_3D printers.json",
                "collection_name": "RSS_262026947",
                "chunk_length": 82,
                "enhanced_tags": ["BBC", "English", "Learning"],
                "tagged_at": "2025-07-10T14:45:08.823699"
            }
        ]
    }
    
    # 建立測試檔案
    test_file = Path("test_input.json")
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    try:
        # 建立轉換器
        converter = MilvusDataConverter()
        
        # 轉換檔案
        result = converter.convert_file_to_milvus_format(test_file)
        
        if result:
            print(f"✅ 轉換成功！共 {len(result)} 個 chunks")
            
            # 檢查第一個 chunk 的格式
            first_chunk = result[0]
            print("\n📋 轉換後的 chunk 格式:")
            for key, value in first_chunk.items():
                print(f"  {key}: {type(value).__name__} = {value}")
            
            # 驗證必要欄位
            required_fields = [
                'chunk_id', 'chunk_index', 'episode_id', 'podcast_id',
                'podcast_name', 'author', 'category', 'episode_title',
                'duration', 'published_date', 'apple_rating', 'chunk_text',
                'embedding', 'language', 'created_at', 'source_model', 'tags'
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in first_chunk:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ 缺少欄位: {missing_fields}")
            else:
                print("✅ 所有必要欄位都存在")
            
            # 驗證資料型態
            type_checks = [
                ('chunk_id', str),
                ('chunk_index', int),
                ('episode_id', int),
                ('podcast_id', int),
                ('podcast_name', str),
                ('author', str),
                ('category', str),
                ('episode_title', str),
                ('chunk_text', str),
                ('tags', str)
            ]
            
            type_errors = []
            for field, expected_type in type_checks:
                if field in first_chunk:
                    actual_type = type(first_chunk[field])
                    if not isinstance(first_chunk[field], expected_type):
                        type_errors.append(f"{field}: 期望 {expected_type.__name__}, 實際 {actual_type.__name__}")
            
            if type_errors:
                print(f"❌ 型態錯誤: {type_errors}")
            else:
                print("✅ 所有欄位型態正確")
            
            return True
        else:
            print("❌ 轉換失敗")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False
    finally:
        # 清理測試檔案
        if test_file.exists():
            test_file.unlink()


def test_filename_parsing():
    """測試檔案名稱解析"""
    print("\n🧪 測試檔案名稱解析...")
    
    converter = MilvusDataConverter()
    
    test_cases = [
        "RSS_262026947_podcast_1304_3D printers.json",
        "RSS_1488295306_podcast_1321_早晨財經速解讀.json",
        "RSS_1500839292_podcast_1234_股癌投資理財.json"
    ]
    
    for filename in test_cases:
        result = converter.parse_filename(filename)
        if result:
            print(f"✅ {filename}")
            print(f"  podcast_id: {result['podcast_id']}")
            print(f"  episode_title: {result['episode_title']}")
        else:
            print(f"❌ {filename} - 解析失敗")


def test_database_query():
    """測試資料庫查詢"""
    print("\n🧪 測試資料庫查詢...")
    
    converter = MilvusDataConverter()
    
    # 測試查詢
    podcast_id = "262026947"
    episode_title = "3D printers"
    
    metadata = converter.get_episode_metadata_from_db(podcast_id, episode_title)
    
    if metadata:
        print("✅ 資料庫查詢成功")
        print(f"  podcast_name: {metadata.get('podcast_name', 'N/A')}")
        print(f"  author: {metadata.get('author', 'N/A')}")
        print(f"  category: {metadata.get('category', 'N/A')}")
    else:
        print("⚠️ 資料庫查詢失敗，將使用快取資料")


def main():
    """主測試函數"""
    print("🚀 開始測試 Milvus 資料轉換功能")
    
    # 測試檔案名稱解析
    test_filename_parsing()
    
    # 測試資料庫查詢
    test_database_query()
    
    # 測試單個檔案轉換
    success = test_single_file_conversion()
    
    if success:
        print("\n🎉 所有測試通過！")
    else:
        print("\n❌ 測試失敗")
        sys.exit(1)


if __name__ == "__main__":
    main() 