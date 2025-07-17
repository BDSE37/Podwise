#!/usr/bin/env python3
"""
完整整合測試 - 測試前端和 RAG Pipeline 的整合
"""

import requests
import time
import json
from typing import Dict, Any

class FullIntegrationTester:
    def __init__(self):
        self.rag_api = "http://localhost:8011"
        self.frontend_api = "http://localhost:8080"
        self.session = requests.Session()
    
    def test_rag_pipeline(self) -> bool:
        """測試 RAG Pipeline 服務"""
        print("🔍 測試 RAG Pipeline 服務...")
        try:
            response = self.session.get(f"{self.rag_api}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ RAG Pipeline 健康檢查成功: {data['status']}")
                return True
            else:
                print(f"❌ RAG Pipeline 健康檢查失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ RAG Pipeline 連接失敗: {str(e)}")
            return False
    
    def test_frontend(self) -> bool:
        """測試前端服務"""
        print("🔍 測試前端服務...")
        try:
            response = self.session.get(f"{self.frontend_api}/index.html")
            if response.status_code == 200:
                print("✅ 前端服務正常")
                return True
            else:
                print(f"❌ 前端服務失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 前端連接失敗: {str(e)}")
            return False
    
    def test_podri_page(self) -> bool:
        """測試 Podri 頁面"""
        print("🔍 測試 Podri 頁面...")
        try:
            response = self.session.get(f"{self.frontend_api}/podri.html")
            if response.status_code == 200:
                print("✅ Podri 頁面正常")
                return True
            else:
                print(f"❌ Podri 頁面失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Podri 頁面連接失敗: {str(e)}")
            return False
    
    def test_query_flow(self) -> bool:
        """測試查詢流程"""
        print("🔍 測試查詢流程...")
        
        test_queries = [
            "推薦一些播客",
            "我想學習投資理財",
            "有什麼教育類的內容"
        ]
        
        success_count = 0
        for query in test_queries:
            try:
                print(f"  測試查詢: {query}")
                response = self.session.post(
                    f"{self.rag_api}/api/v1/query",
                    json={
                        "query": query,
                        "user_id": "test_user_001",
                        "session_id": "test_session_001"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"    ✅ 成功: {data['response'][:50]}...")
                    success_count += 1
                else:
                    print(f"    ❌ 失敗: {response.status_code}")
                    
            except Exception as e:
                print(f"    ❌ 錯誤: {str(e)}")
            
            time.sleep(0.5)  # 避免請求過快
        
        return success_count == len(test_queries)
    
    def test_user_validation_flow(self) -> bool:
        """測試用戶驗證流程"""
        print("🔍 測試用戶驗證流程...")
        try:
            response = self.session.post(
                f"{self.rag_api}/api/v1/validate-user",
                json={"user_id": "test_user_001"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 用戶驗證成功: {data['message']}")
                return True
            else:
                print(f"❌ 用戶驗證失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 用戶驗證錯誤: {str(e)}")
            return False
    
    def test_tts_flow(self) -> bool:
        """測試 TTS 流程"""
        print("🔍 測試 TTS 流程...")
        try:
            # 測試獲取語音列表
            response = self.session.get(f"{self.rag_api}/api/v1/tts/voices")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ TTS 語音列表成功: {data['voices']}")
                
                # 測試語音合成
                tts_response = self.session.post(
                    f"{self.rag_api}/api/v1/tts/synthesize",
                    json={
                        "text": "這是一個測試語音",
                        "voice": "podrina",
                        "speed": 1.0
                    }
                )
                
                if tts_response.status_code == 200:
                    tts_data = tts_response.json()
                    print(f"✅ TTS 語音合成成功: {tts_data['message']}")
                    return True
                else:
                    print(f"❌ TTS 語音合成失敗: {tts_response.status_code}")
                    return False
            else:
                print(f"❌ TTS 語音列表失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ TTS 流程錯誤: {str(e)}")
            return False
    
    def test_frontend_to_rag_flow(self) -> bool:
        """測試前端到 RAG Pipeline 的完整流程"""
        print("🔍 測試前端到 RAG Pipeline 的完整流程...")
        
        # 模擬前端發送的請求
        test_payload = {
            "query": "推薦一些播客",
            "user_id": "Podwise0001",
            "session_id": "session_Podwise0001_1234567890",
            "enable_tts": True,
            "voice": "podrina",
            "speed": 1.0,
            "metadata": {
                "source": "podri_chat",
                "timestamp": "2025-07-17T11:30:00Z"
            }
        }
        
        try:
            response = self.session.post(
                f"{self.rag_api}/api/v1/query",
                json=test_payload
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 完整流程成功:")
                print(f"   查詢: {data['query']}")
                print(f"   回應: {data['response'][:100]}...")
                print(f"   分類: {data['category']}")
                print(f"   信心度: {data['confidence']}")
                print(f"   TTS 啟用: {data['tts_enabled']}")
                return True
            else:
                print(f"❌ 完整流程失敗: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 完整流程錯誤: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """運行所有測試"""
        print("🚀 開始完整整合測試")
        print("=" * 60)
        
        results = {}
        
        # 基本服務測試
        results['rag_pipeline'] = self.test_rag_pipeline()
        results['frontend'] = self.test_frontend()
        results['podri_page'] = self.test_podri_page()
        
        # 功能測試
        results['user_validation'] = self.test_user_validation_flow()
        results['query_flow'] = self.test_query_flow()
        results['tts_flow'] = self.test_tts_flow()
        
        # 完整流程測試
        results['full_flow'] = self.test_frontend_to_rag_flow()
        
        # 總結
        print("\n📊 整合測試總結")
        print("=" * 60)
        
        success_count = sum(results.values())
        total_count = len(results)
        
        print(f"總測試數: {total_count}")
        print(f"成功數: {success_count}")
        print(f"失敗數: {total_count - success_count}")
        print(f"成功率: {success_count/total_count*100:.1f}%")
        
        if success_count == total_count:
            print("\n🎉 所有測試通過！前端和 RAG Pipeline 整合成功！")
            print("\n✅ 現在您可以：")
            print("1. 訪問 http://localhost:8080/index.html")
            print("2. 輸入用戶 ID 並搜尋")
            print("3. 點擊跳轉到 Podri 聊天頁面")
            print("4. 開始與 RAG Pipeline 對話")
        else:
            print("\n⚠️  部分測試失敗，請檢查服務狀態。")
            
            print("\n❌ 失敗的測試:")
            for test_name, result in results.items():
                if not result:
                    print(f"  - {test_name}")
        
        return results

def main():
    """主函數"""
    tester = FullIntegrationTester()
    results = tester.run_all_tests()
    
    # 返回結果
    if all(results.values()):
        print("\n🎯 整合測試完成 - 可以開始使用！")
        return 0
    else:
        print("\n⚠️  整合測試發現問題，請檢查服務。")
        return 1

if __name__ == "__main__":
    exit(main()) 