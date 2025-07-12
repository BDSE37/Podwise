#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試用戶偏好收集服務
"""

import requests
import json

# 測試配置
BASE_URL = "http://localhost:8000"

def test_category_recommendations():
    """測試類別推薦功能"""
    print("=== 測試類別推薦功能 ===")
    
    # 測試商業類別
    response = requests.post(
        f"{BASE_URL}/api/category/recommendations",
        json={"category": "business"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 商業類別推薦成功，獲取到 {len(data.get('recommendations', []))} 個推薦")
        for rec in data.get('recommendations', [])[:2]:
            print(f"  - {rec.get('podcast_name')}: {rec.get('episode_title')}")
    else:
        print(f"❌ 商業類別推薦失敗: {response.status_code}")
    
    # 測試教育類別
    response = requests.post(
        f"{BASE_URL}/api/category/recommendations",
        json={"category": "education"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 教育類別推薦成功，獲取到 {len(data.get('recommendations', []))} 個推薦")
        for rec in data.get('recommendations', [])[:2]:
            print(f"  - {rec.get('podcast_name')}: {rec.get('episode_title')}")
    else:
        print(f"❌ 教育類別推薦失敗: {response.status_code}")

def test_user_feedback():
    """測試用戶反饋功能"""
    print("\n=== 測試用戶反饋功能 ===")
    
    feedback_data = {
        "user_id": "test_user_123",
        "episode_id": 1,
        "podcast_name": "測試播客",
        "episode_title": "測試節目",
        "rss_id": "test_rss_123",
        "action": "like",
        "category": "business"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/feedback",
        json=feedback_data
    )
    
    if response.status_code == 200:
        print("✅ 用戶反饋記錄成功")
    else:
        print(f"❌ 用戶反饋記錄失敗: {response.status_code}")

def test_user_registration():
    """測試用戶註冊功能"""
    print("\n=== 測試用戶註冊功能 ===")
    
    user_data = {
        "user_id": "test_user_456",
        "category": "business",
        "selected_episodes": [
            {
                "episode_id": 1,
                "podcast_name": "股癌 Gooaye",
                "episode_title": "投資理財精選",
                "rss_id": "123"
            },
            {
                "episode_id": 2,
                "podcast_name": "矽谷輕鬆談",
                "episode_title": "AI 技術趨勢",
                "rss_id": "456"
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/user/register",
        json=user_data
    )
    
    if response.status_code == 200:
        print("✅ 用戶註冊成功")
    else:
        print(f"❌ 用戶註冊失敗: {response.status_code}")

def test_user_check():
    """測試用戶檢查功能"""
    print("\n=== 測試用戶檢查功能 ===")
    
    response = requests.get(f"{BASE_URL}/api/user/check/test_user_456")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 用戶檢查成功: {data.get('exists', False)}")
    else:
        print(f"❌ 用戶檢查失敗: {response.status_code}")

if __name__ == "__main__":
    print("開始測試用戶偏好收集服務...")
    
    try:
        test_category_recommendations()
        test_user_feedback()
        test_user_registration()
        test_user_check()
        
        print("\n🎉 所有測試完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到服務器，請確保服務正在運行")
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}") 