#!/usr/bin/env python3
"""
測試圖片 URL 生成和資料庫連接
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from user_management.main import UserPreferenceManager, UserServiceConfig
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_image_urls():
    """測試圖片 URL 生成"""
    try:
        # 初始化用戶偏好管理器
        config = UserServiceConfig()
        manager = UserPreferenceManager(config)
        
        print("=== 測試圖片 URL 生成 ===")
        
        # 測試從資料庫獲取的 podcast 資訊
        print(f"已載入 {len(manager.podcast_name_cache)} 個 podcast 名稱")
        print(f"已載入 {len(manager.episode_title_cache)} 個 episode 標題")
        print(f"已載入 {len(manager.podcast_tags_cache)} 個 podcast 標籤")
        
        # 顯示前幾個 podcast 資訊
        print("\n前 5 個 podcast 資訊:")
        for i, (podcast_id, name) in enumerate(list(manager.podcast_name_cache.items())[:5]):
            tags = manager.podcast_tags_cache.get(podcast_id, [])
            episode_title = manager.episode_title_cache.get(podcast_id, "未知標題")
            image_url = f"http://{config.minio_endpoint}/podcast-images/RSS_{podcast_id}_300.jpg"
            
            print(f"  {i+1}. ID: {podcast_id}")
            print(f"     名稱: {name}")
            print(f"     標題: {episode_title}")
            print(f"     標籤: {tags}")
            print(f"     圖片: {image_url}")
            print()
        
        # 測試獲取類別標籤
        print("=== 測試獲取類別標籤 ===")
        business_tags = manager.get_category_tags("business")
        print(f"商業類別標籤: {business_tags}")
        
        education_tags = manager.get_category_tags("education")
        print(f"教育類別標籤: {education_tags}")
        
        # 測試獲取預設節目
        print("\n=== 測試獲取預設節目 ===")
        business_episodes = manager._get_default_episodes("business")
        print(f"商業類別預設節目: {business_episodes}")
        
        education_episodes = manager._get_default_episodes("education")
        print(f"教育類別預設節目: {education_episodes}")
        
        print("\n✅ 測試完成")
        
    except Exception as e:
        logger.error(f"測試失敗: {e}")
        print(f"❌ 測試失敗: {e}")

if __name__ == "__main__":
    test_image_urls() 