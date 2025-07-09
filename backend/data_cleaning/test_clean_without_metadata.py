#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試清理功能，驗證不會添加清理資訊
"""

import sys
import json
from pathlib import Path

# 添加父目錄到路徑
sys.path.append(str(Path(__file__).parent))

from core.youtube_cleaner import YouTubeCleaner

def test_clean_without_metadata():
    """測試清理功能，確保不會添加清理資訊"""
    
    # 測試資料
    test_data = {
        "url": "https://www.youtube.com/watch?v=zqL_-9_RY_I",
        "title": "🚩 【吳淡如Ｘ林香蘭】礦工女兒高商畢業如何成為執行長？",
        "author": "吳淡如人生實用商學院（Official官方唯一頻道）",
        "view_count": "觀看次數：3378次",
        "like_count": "75",
        "comment_count": 1,
        "comments": [
            "已訂購娘家產品，期待"
        ]
    }
    
    # 配置 YouTube 清理器，啟用檔案名稱清理
    config = {
        "fields_to_clean": {
            "filename": {
                "enabled": True,
                "clean_type": "filename",
                "description": "清理檔案名稱，使用與內文相同的清理邏輯"
            }
        }
    }
    
    cleaner = YouTubeCleaner(config)
    
    print("=== 原始資料 ===")
    print(json.dumps(test_data, ensure_ascii=False, indent=2))
    
    # 清理資料
    cleaned_data = cleaner.clean(test_data)
    
    print("\n=== 清理後資料 ===")
    print(json.dumps(cleaned_data, ensure_ascii=False, indent=2))
    
    # 檢查是否包含清理資訊
    metadata_fields = ['cleaned_at', 'cleaning_status', 'cleaner_type', 'cleaning_config']
    found_metadata = [field for field in metadata_fields if field in cleaned_data]
    
    if found_metadata:
        print(f"\n❌ 發現清理資訊欄位: {found_metadata}")
        return False
    else:
        print("\n✅ 沒有發現清理資訊欄位，清理成功！")
        return True

def test_batch_clean_without_metadata():
    """測試批次清理功能"""
    
    # 測試資料列表
    test_documents = [
        {
            "url": "https://www.youtube.com/watch?v=test1",
            "title": "🚩 測試標題1",
            "author": "測試作者（Official）",
            "view_count": "觀看次數：1000次",
            "like_count": "50",
            "comment_count": 2,
            "comments": ["測試評論1", "測試評論2"]
        },
        {
            "url": "https://www.youtube.com/watch?v=test2",
            "title": "🎯 測試標題2",
            "author": "測試作者2（Official官方唯一頻道）",
            "view_count": "觀看次數：2000次",
            "like_count": "100",
            "comment_count": 3,
            "comments": ["測試評論3", "測試評論4", "測試評論5"]
        }
    ]
    
    config = {
        "fields_to_clean": {
            "filename": {
                "enabled": True,
                "clean_type": "filename",
                "description": "清理檔案名稱，使用與內文相同的清理邏輯"
            }
        }
    }
    
    cleaner = YouTubeCleaner(config)
    
    print("=== 批次清理測試 ===")
    print(f"原始文檔數量: {len(test_documents)}")
    
    # 批次清理
    cleaned_docs = cleaner.batch_clean_documents(test_documents)
    
    print(f"清理後文檔數量: {len(cleaned_docs)}")
    
    # 檢查每個文檔是否包含清理資訊
    metadata_fields = ['cleaned_at', 'cleaning_status', 'cleaner_type', 'cleaning_config']
    all_clean = True
    
    for i, doc in enumerate(cleaned_docs):
        found_metadata = [field for field in metadata_fields if field in doc]
        if found_metadata:
            print(f"❌ 文檔 {i+1} 包含清理資訊: {found_metadata}")
            all_clean = False
        else:
            print(f"✅ 文檔 {i+1} 清理成功，無清理資訊")
    
    if all_clean:
        print("\n🎉 所有文檔都清理成功，沒有添加清理資訊！")
        return True
    else:
        print("\n❌ 部分文檔包含清理資訊")
        return False

if __name__ == "__main__":
    print("開始測試清理功能...")
    
    # 測試單一資料清理
    print("\n" + "="*50)
    print("測試單一資料清理")
    print("="*50)
    success1 = test_clean_without_metadata()
    
    # 測試批次清理
    print("\n" + "="*50)
    print("測試批次清理")
    print("="*50)
    success2 = test_batch_clean_without_metadata()
    
    # 總結
    print("\n" + "="*50)
    print("測試總結")
    print("="*50)
    if success1 and success2:
        print("🎉 所有測試通過！清理功能正常工作，不會添加清理資訊。")
    else:
        print("❌ 部分測試失敗，請檢查清理功能。") 