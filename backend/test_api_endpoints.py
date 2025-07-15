#!/usr/bin/env python3
"""
API 端點測試腳本
測試所有四步驟功能相關的 API 端點
"""

import requests
import json
import time

# API 基礎 URL
BASE_URL = "http://localhost:8008"

def test_api_endpoint(endpoint, method="GET", data=None, params=None):
    """測試 API 端點"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        print(f"✅ {method} {endpoint}")
        print(f"   狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   回應: {json.dumps(result, ensure_ascii=False, indent=2)}")
                return True, result
            except json.JSONDecodeError:
                print(f"   ❌ 回應不是有效的 JSON: {response.text}")
                return False, response.text
        else:
            print(f"   ❌ 錯誤: {response.text}")
            return False, response.text
            
    except Exception as e:
        print(f"❌ {method} {endpoint} - 異常: {e}")
        return False, str(e)

def main():
    """主測試函數"""
    print("🚀 開始測試 Podwise API 端點")
    print("=" * 50)
    
    # 測試 1: 獲取類別標籤
    print("\n📋 測試 1: 獲取類別標籤")
    print("-" * 30)
    
    success, result = test_api_endpoint("/api/category-tags", params={"category": "business"})
    if success and isinstance(result, dict) and result.get("success"):
        business_tags = result.get("tags", [])
        print(f"   商業類別標籤: {business_tags}")
    else:
        print("   ❌ 獲取商業類別標籤失敗")
        return
    
    success, result = test_api_endpoint("/api/category-tags", params={"category": "education"})
    if success and isinstance(result, dict) and result.get("success"):
        education_tags = result.get("tags", [])
        print(f"   教育類別標籤: {education_tags}")
    else:
        print("   ❌ 獲取教育類別標籤失敗")
        return
    
    # 測試 2: 獲取節目推薦
    print("\n🎵 測試 2: 獲取節目推薦")
    print("-" * 30)
    
    if business_tags:
        test_tag = business_tags[0]
        success, result = test_api_endpoint(
            "/api/one-minutes-episodes", 
            params={"category": "business", "tag": test_tag}
        )
        if success and isinstance(result, dict) and result.get("success"):
            episodes = result.get("episodes", [])
            print(f"   找到 {len(episodes)} 個節目")
            for i, episode in enumerate(episodes[:2]):  # 只顯示前2個
                print(f"   {i+1}. {episode.get('podcast_name', 'N/A')} - {episode.get('episode_title', 'N/A')}")
        else:
            print("   ❌ 獲取節目推薦失敗")
            return
    
    # 測試 3: 生成 Podwise ID
    print("\n🆔 測試 3: 生成 Podwise ID")
    print("-" * 30)
    
    success, result = test_api_endpoint("/api/generate-podwise-id", method="POST")
    if success and isinstance(result, dict) and result.get("success"):
        podwise_id = result.get("podwise_id")
        print(f"   生成的 Podwise ID: {podwise_id}")
        
        # 測試 4: 檢查用戶是否存在
        print("\n👤 測試 4: 檢查用戶是否存在")
        print("-" * 30)
        
        success, result = test_api_endpoint(f"/api/user/check/{podwise_id}")
        if success and isinstance(result, dict) and result.get("success"):
            exists = result.get("exists")
            print(f"   用戶 {podwise_id} 存在: {exists}")
        else:
            print("   ❌ 檢查用戶失敗")
            return
        
        # 測試 5: 儲存用戶偏好
        print("\n💾 測試 5: 儲存用戶偏好")
        print("-" * 30)
        
        preferences_data = {
            "user_code": podwise_id,
            "main_category": "business",
            "selected_tag": test_tag if business_tags else "投資理財",
            "liked_episodes": [
                {
                    "episode_id": 1,
                    "podcast_name": "測試節目",
                    "episode_title": "測試標題",
                    "rss_id": "123"
                }
            ]
        }
        
        success, result = test_api_endpoint("/api/user/preferences", method="POST", data=preferences_data)
        if success and isinstance(result, dict) and result.get("success"):
            print("   ✅ 用戶偏好儲存成功")
        else:
            print("   ❌ 儲存用戶偏好失敗")
            return
        
        # 測試 6: 記錄反饋
        print("\n📝 測試 6: 記錄反饋")
        print("-" * 30)
        
        feedback_data = {
            "user_code": podwise_id,
            "episode_id": 1,
            "podcast_name": "測試節目",
            "episode_title": "測試標題",
            "rss_id": "123",
            "action": "like",
            "category": "business"
        }
        
        success, result = test_api_endpoint("/api/feedback", method="POST", data=feedback_data)
        if success and isinstance(result, dict) and result.get("success"):
            print("   ✅ 反饋記錄成功")
        else:
            print("   ❌ 記錄反饋失敗")
            return
        
        # 測試 7: 獲取音檔 URL
        print("\n🎵 測試 7: 獲取音檔 URL")
        print("-" * 30)
        
        audio_request = {
            "rss_id": "123",
            "episode_title": "測試標題",
            "category": "business"
        }
        
        success, result = test_api_endpoint("/api/audio/presigned-url", method="POST", data=audio_request)
        if success and isinstance(result, dict) and result.get("success"):
            audio_url = result.get("audio_url")
            print(f"   音檔 URL: {audio_url}")
        else:
            print("   ❌ 獲取音檔 URL 失敗")
            return
    
    else:
        print("   ❌ 生成 Podwise ID 失敗")
        return
    
    print("\n" + "=" * 50)
    print("🎉 所有 API 端點測試完成！")
    print("✅ 四步驟功能已準備就緒")

if __name__ == "__main__":
    main() 