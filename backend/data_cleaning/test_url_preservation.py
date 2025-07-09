#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 URL 保留功能，驗證 https:// 不會被刪除
"""

import sys
import json
from pathlib import Path

# 添加父目錄到路徑
sys.path.append(str(Path(__file__).parent))

from core.youtube_cleaner import YouTubeCleaner
from core.episode_cleaner import EpisodeCleaner
from core.longtext_cleaner import LongTextCleaner

def test_url_preservation():
    """測試 URL 保留功能"""
    
    print("🔧 測試 URL 保留功能...")
    
    # 測試資料
    test_data = {
        "url": "https://www.youtube.com/watch?v=zqL_-9_RY_I",
        "title": "🚩 【吳淡如Ｘ林香蘭】礦工女兒高商畢業如何成為執行長？",
        "description": "這是一個測試描述，包含 https://example.com 和 http://test.com 連結",
        "author": "吳淡如人生實用商學院（Official官方唯一頻道）",
        "view_count": "觀看次數：3378次",
        "like_count": "75",
        "comment_count": 1,
        "comments": [
            "已訂購娘家產品，期待 https://shop.example.com"
        ]
    }
    
    # 測試 YouTube 清理器
    print("\n📺 測試 YouTube 清理器...")
    youtube_cleaner = YouTubeCleaner()
    cleaned_youtube = youtube_cleaner.clean(test_data)
    
    print(f"原始 URL: {test_data['url']}")
    print(f"清理後 URL: {cleaned_youtube['url']}")
    print(f"原始描述: {test_data['description']}")
    print(f"清理後描述: {cleaned_youtube['description']}")
    print(f"原始評論: {test_data['comments']}")
    print(f"清理後評論: {cleaned_youtube['comments']}")
    
    # 測試 Episode 清理器
    print("\n🎬 測試 Episode 清理器...")
    episode_cleaner = EpisodeCleaner()
    episode_data = {
        "episode_title": "🚩 測試標題 https://example.com",
        "description": "測試描述包含 https://test.com 連結"
    }
    cleaned_episode = episode_cleaner.clean(episode_data)
    
    print(f"原始標題: {episode_data['episode_title']}")
    print(f"清理後標題: {cleaned_episode['episode_title']}")
    print(f"原始描述: {episode_data['description']}")
    print(f"清理後描述: {cleaned_episode['description']}")
    
    # 測試 LongText 清理器
    print("\n📝 測試 LongText 清理器...")
    longtext_cleaner = LongTextCleaner()
    longtext_data = "這是一個長文本，包含 https://example.com 和 http://test.com 連結，還有一些表情符號 🚩"
    cleaned_longtext = longtext_cleaner.clean(longtext_data)
    
    print(f"原始文本: {longtext_data}")
    print(f"清理後文本: {cleaned_longtext}")
    
    # 驗證結果
    print("\n✅ 驗證結果:")
    
    # 檢查 YouTube 清理器
    if "https://" in cleaned_youtube['url'] and "http://" in cleaned_youtube['description']:
        print("✅ YouTube 清理器：URL 保留成功")
    else:
        print("❌ YouTube 清理器：URL 保留失敗")
    
    # 檢查 Episode 清理器
    if "https://" in cleaned_episode['episode_title'] and "https://" in cleaned_episode['description']:
        print("✅ Episode 清理器：URL 保留成功")
    else:
        print("❌ Episode 清理器：URL 保留失敗")
    
    # 檢查 LongText 清理器
    if "https://" in cleaned_longtext and "http://" in cleaned_longtext:
        print("✅ LongText 清理器：URL 保留成功")
    else:
        print("❌ LongText 清理器：URL 保留失敗")
    
    print("\n🎉 URL 保留測試完成！")

if __name__ == "__main__":
    test_url_preservation() 