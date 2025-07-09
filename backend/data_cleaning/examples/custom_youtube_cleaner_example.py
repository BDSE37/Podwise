#!/usr/bin/env python3
"""
YouTube 清理器自定義配置使用範例
展示如何根據需求自定義清理配置
"""

import json
import sys
from pathlib import Path

# 添加父目錄到路徑以支援絕對導入
sys.path.append(str(Path(__file__).parent.parent))

from core.youtube_cleaner import YouTubeCleaner

def example_basic_usage():
    """基本使用範例"""
    print("=== 基本使用範例 ===")
    
    # 測試資料
    data = {
        "title": "🚩 【吳淡如Ｘ林香蘭】礦工女兒高商畢業如何成為執行長？",
        "author": "吳淡如人生實用商學院（Official官方唯一頻道）",
        "view_count": "觀看次數：3378次",
        "like_count": "75",
        "comments": ["已訂購娘家產品，期待 👍", "非常實用的內容！💡"]
    }
    
    # 使用預設配置
    cleaner = YouTubeCleaner()
    cleaned = cleaner.clean(data)
    
    print("原始資料:", data)
    print("清理後資料:", cleaned)
    print()

def example_custom_fields():
    """自定義欄位範例"""
    print("=== 自定義欄位範例 ===")
    
    # 只清理標題和作者
    config = {
        "fields_to_clean": {
            "title": {"enabled": True, "clean_type": "title"},
            "author": {"enabled": True, "clean_type": "author"},
            "view_count": {"enabled": False},  # 停用觀看次數清理
            "like_count": {"enabled": False},  # 停用按讚數清理
            "comments": {"enabled": False}     # 停用評論清理
        }
    }
    
    data = {
        "title": "🚩 【吳淡如Ｘ林香蘭】礦工女兒高商畢業如何成為執行長？",
        "author": "吳淡如人生實用商學院（Official官方唯一頻道）",
        "view_count": "觀看次數：3378次",
        "like_count": "75",
        "comments": ["已訂購娘家產品，期待 👍"]
    }
    
    cleaner = YouTubeCleaner(config)
    cleaned = cleaner.clean(data)
    
    print("原始資料:", data)
    print("清理後資料:", cleaned)
    print()

def example_add_custom_field():
    """添加自定義欄位範例"""
    print("=== 添加自定義欄位範例 ===")
    
    cleaner = YouTubeCleaner()
    
    # 動態添加自定義欄位
    cleaner.add_custom_field("user_rating", {
        "enabled": True,
        "clean_type": "number",
        "description": "用戶評分"
    })
    
    cleaner.add_custom_field("video_quality", {
        "enabled": True,
        "clean_type": "text",
        "description": "影片品質"
    })
    
    data = {
        "title": "🚩 【吳淡如Ｘ林香蘭】礦工女兒高商畢業如何成為執行長？",
        "author": "吳淡如人生實用商學院（Official官方唯一頻道）",
        "user_rating": "4.5顆星",
        "video_quality": "高清 1080p 🎥"
    }
    
    cleaned = cleaner.clean(data)
    
    print("原始資料:", data)
    print("清理後資料:", cleaned)
    print()

def example_load_from_file():
    """從檔案載入配置範例"""
    print("=== 從檔案載入配置範例 ===")
    
    try:
        # 載入配置檔案
        config_path = Path(__file__).parent.parent / "config" / "youtube_cleaner_config.json"
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        data = {
            "title": "🚩 【吳淡如Ｘ林香蘭】礦工女兒高商畢業如何成為執行長？",
            "author": "吳淡如人生實用商學院（Official官方唯一頻道）",
            "view_count": "觀看次數：3378次",
            "description": "這是一個關於成功故事的影片 🎯",
            "tags": ["成功", "創業", "勵志 💪"],
            "duration": "15分鐘"
        }
        
        cleaner = YouTubeCleaner(config)
        cleaned = cleaner.clean(data)
        
        print("原始資料:", data)
        print("清理後資料:", cleaned)
        print()
        
    except FileNotFoundError:
        print("配置檔案不存在，請先創建 config/youtube_cleaner_config.json")
        print()

def example_different_clean_types():
    """不同清理類型範例"""
    print("=== 不同清理類型範例 ===")
    
    # 配置不同類型的清理
    config = {
        "fields_to_clean": {
            "title": {"enabled": True, "clean_type": "title"},
            "author": {"enabled": True, "clean_type": "author"},
            "view_count": {"enabled": True, "clean_type": "number"},
            "comments": {"enabled": True, "clean_type": "list"},
            "description": {"enabled": True, "clean_type": "text"},
            "tags": {"enabled": True, "clean_type": "list"}
        }
    }
    
    data = {
        "title": "🚩 【吳淡如Ｘ林香蘭】礦工女兒高商畢業如何成為執行長？",
        "author": "吳淡如人生實用商學院（Official官方唯一頻道）",
        "view_count": "觀看次數：3378次",
        "comments": ["已訂購娘家產品，期待 👍", "非常實用的內容！💡"],
        "description": "這是一個關於成功故事的影片 🎯",
        "tags": ["成功", "創業", "勵志 💪"]
    }
    
    cleaner = YouTubeCleaner(config)
    cleaned = cleaner.clean(data)
    
    print("原始資料:", data)
    print("清理後資料:", cleaned)
    print()

if __name__ == "__main__":
    example_basic_usage()
    example_custom_fields()
    example_add_custom_field()
    example_load_from_file()
    example_different_clean_types()
    
    print("=== 所有範例執行完成 ===") 