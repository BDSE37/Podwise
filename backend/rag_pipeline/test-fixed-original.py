#!/usr/bin/env python3
"""
測試修復版本的 RAG Pipeline
"""

import requests
import json
import time
from typing import Dict, Any

class RAGPipelineTester:
    def __init__(self, base_url: str = "http://localhost:8010"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health(self) -> bool:
        """測試健康檢查"""
        print("🔍 測試健康檢查...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 健康檢查成功: {data['status']}")
                print(f"   組件狀態: {data['components']}")
                return True
            else:
                print(f"❌ 健康檢查失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 健康檢查異常: {str(e)}")
            return False
    
    def test_root(self) -> bool:
        """測試根端點"""
        print("🔍 測試根端點...")
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 根端點成功: {data['message']}")
                return True
            else:
                print(f"❌ 根端點失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 根端點異常: {str(e)}")
            return False
    
    def test_user_validation(self) -> bool:
        """測試用戶驗證"""
        print("🔍 測試用戶驗證...")
        try:
            payload = {"user_id": "test_user_001"}
            response = self.session.post(
                f"{self.base_url}/api/v1/validate-user",
                json=payload
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 用戶驗證成功: {data['message']}")
                return True
            else:
                print(f"❌ 用戶驗證失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 用戶驗證異常: {str(e)}")
            return False
    
    def test_query(self, query: str, category: str = "general") -> bool:
        """測試查詢處理"""
        print(f"🔍 測試查詢: {query}")
        try:
            payload = {
                "query": query,
                "user_id": "test_user_001",
                "session_id": "test_session_001"
            }
            response = self.session.post(
                f"{self.base_url}/api/v1/query",
                json=payload
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 查詢成功:")
                print(f"   回應: {data['response'][:100]}...")
                print(f"   分類: {data['category']}")
                print(f"   信心度: {data['confidence']}")
                print(f"   推薦數量: {len(data['recommendations'])}")
                return True
            else:
                print(f"❌ 查詢失敗: {response.status_code}")
                print(f"   錯誤: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 查詢異常: {str(e)}")
            return False
    
    def test_tts_voices(self) -> bool:
        """測試 TTS 語音列表"""
        print("🔍 測試 TTS 語音列表...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/tts/voices")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ TTS 語音列表成功: {data['voices']}")
                return True
            else:
                print(f"❌ TTS 語音列表失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ TTS 語音列表異常: {str(e)}")
            return False
    
    def test_system_info(self) -> bool:
        """測試系統資訊"""
        print("🔍 測試系統資訊...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/system-info")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 系統資訊成功:")
                print(f"   版本: {data['version']}")
                print(f"   狀態: {data['status']}")
                print(f"   組件: {data['components']}")
                return True
            else:
                print(f"❌ 系統資訊失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 系統資訊異常: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """運行所有測試"""
        print("🚀 開始測試修復版本的 RAG Pipeline")
        print("=" * 50)
        
        results = {}
        
        # 基本功能測試
        results['health'] = self.test_health()
        results['root'] = self.test_root()
        results['user_validation'] = self.test_user_validation()
        results['system_info'] = self.test_system_info()
        
        # 查詢測試
        test_queries = [
            ("推薦一些播客", "podcast"),
            ("我想學習投資理財", "business"),
            ("有什麼教育類的內容", "education"),
            ("今天天氣怎麼樣", "general")
        ]
        
        for i, (query, category) in enumerate(test_queries):
            results[f'query_{i+1}'] = self.test_query(query, category)
            time.sleep(0.5)  # 避免請求過快
        
        # TTS 測試
        results['tts_voices'] = self.test_tts_voices()
        
        # 總結
        print("\n📊 測試總結")
        print("=" * 50)
        
        success_count = sum(results.values())
        total_count = len(results)
        
        print(f"總測試數: {total_count}")
        print(f"成功數: {success_count}")
        print(f"失敗數: {total_count - success_count}")
        print(f"成功率: {success_count/total_count*100:.1f}%")
        
        if success_count == total_count:
            print("\n🎉 所有測試通過！修復版本運行正常。")
        else:
            print("\n⚠️  部分測試失敗，請檢查服務狀態。")
            
            print("\n❌ 失敗的測試:")
            for test_name, result in results.items():
                if not result:
                    print(f"  - {test_name}")
        
        return results

def main():
    """主函數"""
    import sys
    
    # 檢查命令行參數
    base_url = "http://localhost:8010"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"📍 測試目標: {base_url}")
    
    # 創建測試器
    tester = RAGPipelineTester(base_url)
    
    # 運行測試
    results = tester.run_all_tests()
    
    # 返回結果
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 