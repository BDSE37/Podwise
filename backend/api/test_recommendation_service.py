#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推薦服務測試腳本
測試 MinIO 音檔搜尋、PostgreSQL 查詢和用戶反饋功能
"""

import requests
import json
import time
from typing import Dict, Any

class RecommendationServiceTester:
    """推薦服務測試類別"""
    
    def __init__(self, base_url: str = "http://localhost:8005"):
        """初始化測試器"""
        self.base_url = base_url
        self.test_user_id = "test_user_001"
        
    def test_health_check(self) -> bool:
        """測試健康檢查"""
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ 健康檢查通過")
                return True
            else:
                print(f"❌ 健康檢查失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 健康檢查異常: {e}")
            return False
    
    def test_get_recommendations(self, category: str = "business") -> bool:
        """測試獲取推薦"""
        try:
            payload = {
                "category": category,
                "user_id": self.test_user_id,
                "limit": 3
            }
            
            response = requests.post(
                f"{self.base_url}/recommendations",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 獲取 {category} 推薦成功")
                print(f"   推薦數量: {data.get('total_count', 0)}")
                print(f"   用戶ID: {data.get('user_id', 'unknown')}")
                
                # 顯示推薦詳情
                recommendations = data.get('recommendations', [])
                for i, rec in enumerate(recommendations, 1):
                    print(f"   推薦 {i}: {rec.get('podcast_name', 'Unknown')} - {rec.get('episode_title', 'Unknown')}")
                
                return True
            else:
                print(f"❌ 獲取推薦失敗: {response.status_code}")
                print(f"   錯誤信息: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 獲取推薦異常: {e}")
            return False
    
    def test_record_feedback(self, episode_id: int = 1) -> bool:
        """測試記錄用戶反饋"""
        try:
            payload = {
                "user_id": self.test_user_id,
                "episode_id": episode_id,
                "action": "like",
                "category": "business",
                "file_name": "test_episode.mp3",
                "bucket_category": "business"
            }
            
            response = requests.post(
                f"{self.base_url}/feedback",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ 記錄反饋成功")
                print(f"   反饋ID: {data.get('feedback_id', 'unknown')}")
                print(f"   消息: {data.get('message', 'unknown')}")
                return True
            else:
                print(f"❌ 記錄反饋失敗: {response.status_code}")
                print(f"   錯誤信息: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 記錄反饋異常: {e}")
            return False
    
    def test_get_user_preferences(self) -> bool:
        """測試獲取用戶偏好"""
        try:
            response = requests.get(f"{self.base_url}/user/preferences/{self.test_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ 獲取用戶偏好成功")
                print(f"   用戶ID: {data.get('user_id', 'unknown')}")
                print(f"   偏好: {data.get('preferences', {})}")
                return True
            else:
                print(f"❌ 獲取用戶偏好失敗: {response.status_code}")
                print(f"   錯誤信息: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 獲取用戶偏好異常: {e}")
            return False
    
    def test_minio_audio_url(self, bucket_name: str = "business_one_minutes", file_name: str = "test.mp3") -> bool:
        """測試獲取 MinIO 音檔 URL"""
        try:
            response = requests.get(f"{self.base_url}/minio/audio/{bucket_name}/{file_name}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ 獲取 MinIO 音檔 URL 成功")
                print(f"   Bucket: {data.get('bucket_name', 'unknown')}")
                print(f"   檔案: {data.get('file_name', 'unknown')}")
                print(f"   URL: {data.get('audio_url', 'unknown')[:100]}...")
                return True
            else:
                print(f"❌ 獲取 MinIO 音檔 URL 失敗: {response.status_code}")
                print(f"   錯誤信息: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 獲取 MinIO 音檔 URL 異常: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """執行所有測試"""
        print("🚀 開始執行推薦服務測試...")
        print("=" * 50)
        
        results = {}
        
        # 1. 健康檢查
        results["health_check"] = self.test_health_check()
        print()
        
        # 2. 獲取商業類推薦
        results["business_recommendations"] = self.test_get_recommendations("business")
        print()
        
        # 3. 獲取教育類推薦
        results["education_recommendations"] = self.test_get_recommendations("education")
        print()
        
        # 4. 記錄用戶反饋
        results["record_feedback"] = self.test_record_feedback()
        print()
        
        # 5. 獲取用戶偏好
        results["user_preferences"] = self.test_get_user_preferences()
        print()
        
        # 6. 獲取 MinIO 音檔 URL
        results["minio_audio_url"] = self.test_minio_audio_url()
        print()
        
        # 總結
        print("=" * 50)
        print("📊 測試結果總結:")
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ 通過" if result else "❌ 失敗"
            print(f"   {test_name}: {status}")
        
        print(f"\n總計: {passed}/{total} 測試通過")
        
        if passed == total:
            print("🎉 所有測試通過！推薦服務運行正常。")
        else:
            print("⚠️ 部分測試失敗，請檢查服務配置。")
        
        return results

def test_frontend_integration():
    """測試前端整合"""
    print("\n🌐 測試前端整合...")
    print("=" * 50)
    
    # 模擬前端 API 調用
    base_url = "http://localhost:8081"  # 前端服務地址
    
    try:
        # 測試推薦 API
        response = requests.post(
            f"{base_url}/api/recommendations",
            json={
                "category": "business",
                "user_id": "frontend_user",
                "limit": 3
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ 前端推薦 API 調用成功")
            data = response.json()
            print(f"   推薦數量: {data.get('total_count', 0)}")
        else:
            print(f"❌ 前端推薦 API 調用失敗: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 前端整合測試異常: {e}")

def main():
    """主函數"""
    print("🎯 Podwise 推薦服務測試工具")
    print("=" * 60)
    
    # 檢查服務是否運行
    tester = RecommendationServiceTester()
    
    # 執行後端測試
    results = tester.run_all_tests()
    
    # 執行前端整合測試
    test_frontend_integration()
    
    print("\n" + "=" * 60)
    print("🏁 測試完成")
    
    # 提供使用建議
    if all(results.values()):
        print("\n💡 使用建議:")
        print("1. 前端可以正常調用推薦服務 API")
        print("2. 用戶選擇類別後會獲取對應推薦")
        print("3. 用戶反饋會記錄到資料庫")
        print("4. 音檔可以通過預簽名 URL 播放")
        print("5. 系統已準備好處理用戶行為分析")
    else:
        print("\n🔧 故障排除建議:")
        print("1. 檢查推薦服務是否正常啟動")
        print("2. 確認 PostgreSQL 和 MinIO 連接")
        print("3. 檢查網路和防火牆設置")
        print("4. 查看服務日誌獲取詳細錯誤信息")

if __name__ == "__main__":
    main() 