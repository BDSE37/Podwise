#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試音檔播放功能
"""

import requests
import json
import time

def test_audio_stream():
    """測試音檔串流 API"""
    print("🎵 測試音檔串流功能...")
    
    # 測試商業類別
    business_test = {
        "rss_id": "1488295306",
        "episode_title": "關稅倒數",
        "category": "business"
    }
    
    print(f"📊 測試商業類別: {business_test}")
    response = requests.post(
        "http://localhost:8006/api/audio/stream",
        headers={"Content-Type": "application/json"},
        json=business_test
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 商業類別音檔 URL 獲取成功")
        print(f"   URL: {data['audio_url'][:100]}...")
        print(f"✅ 預簽名 URL 已生成，可在瀏覽器中播放")
    else:
        print(f"❌ 商業類別測試失敗: {response.status_code}")
        print(f"   錯誤: {response.text}")
    
    print("\n" + "="*50 + "\n")
    
    # 測試教育類別
    education_test = {
        "rss_id": "1452688611",
        "episode_title": "工作中那些讓你",
        "category": "education"
    }
    
    print(f"📚 測試教育類別: {education_test}")
    response = requests.post(
        "http://localhost:8006/api/audio/stream",
        headers={"Content-Type": "application/json"},
        json=education_test
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 教育類別音檔 URL 獲取成功")
        print(f"   URL: {data['audio_url'][:100]}...")
        print(f"✅ 預簽名 URL 已生成，可在瀏覽器中播放")
    else:
        print(f"❌ 教育類別測試失敗: {response.status_code}")
        print(f"   錯誤: {response.text}")

def test_recommendations():
    """測試推薦 API"""
    print("\n🎯 測試推薦功能...")
    
    # 測試商業類別推薦
    print("📊 測試商業類別推薦")
    response = requests.post(
        "http://localhost:8006/api/category/recommendations",
        headers={"Content-Type": "application/json"},
        json={"category": "business"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 商業類別推薦成功，共 {data['total_count']} 個推薦")
        for i, rec in enumerate(data['recommendations'][:2], 1):
            print(f"   {i}. {rec['podcast_name']} - {rec['episode_title']}")
    else:
        print(f"❌ 商業類別推薦失敗: {response.status_code}")
    
    print("\n📚 測試教育類別推薦")
    response = requests.post(
        "http://localhost:8006/api/category/recommendations",
        headers={"Content-Type": "application/json"},
        json={"category": "education"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 教育類別推薦成功，共 {data['total_count']} 個推薦")
        for i, rec in enumerate(data['recommendations'][:2], 1):
            print(f"   {i}. {rec['podcast_name']} - {rec['episode_title']}")
    else:
        print(f"❌ 教育類別推薦失敗: {response.status_code}")

def test_health():
    """測試健康檢查"""
    print("🏥 測試服務健康狀態...")
    
    response = requests.get("http://localhost:8006/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 服務健康: {data}")
    else:
        print(f"❌ 服務不健康: {response.status_code}")

if __name__ == "__main__":
    print("🚀 開始測試 Podwise 音檔播放功能")
    print("="*60)
    
    # 測試健康狀態
    test_health()
    print("\n" + "="*60 + "\n")
    
    # 測試音檔串流
    test_audio_stream()
    
    # 測試推薦功能
    test_recommendations()
    
    print("\n" + "="*60)
    print("🎉 測試完成！")
    print("\n💡 如果所有測試都通過，您的前端音檔播放應該可以正常工作了。")
    print("   請重新整理前端頁面並嘗試播放音檔。") 