#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podwise 統一 API Gateway 簡化測試腳本

測試所有 API 功能，包括：
1. 頁面訪問測試
2. 用戶管理測試
3. 音檔管理測試
4. RAG Pipeline 測試
5. TTS/STT 測試
6. 推薦系統測試
7. 反饋系統測試

使用方法：
python simple_test_api.py

作者: Podwise Team
版本: 1.0.0
"""

import asyncio
import aiohttp
import json
import time
import os
import sys
from pathlib import Path
import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API 基礎配置
BASE_URL = "http://localhost:8008"

class SimpleAPITester:
    """簡化 API 測試器"""
    
    def __init__(self):
        """初始化測試器"""
        self.session = None
        self.test_results = []
        self.start_time = None
        
    async def __aenter__(self):
        """異步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name, success, response=None, error=None):
        """記錄測試結果"""
        result = {
            "test_name": test_name,
            "success": success,
            "timestamp": time.time(),
            "response": response,
            "error": error
        }
        self.test_results.append(result)
        
        status = "✅ 通過" if success else "❌ 失敗"
        logger.info(f"{status} {test_name}")
        if error:
            logger.error(f"  錯誤: {error}")
        if response:
            logger.info(f"  回應: {json.dumps(response, ensure_ascii=False, indent=2)}")
    
    async def make_request(self, method, endpoint, data=None, files=None):
        """發送 HTTP 請求"""
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                if self.session:
                    async with self.session.get(url) as response:
                        return await response.json()
            elif method.upper() == "POST":
                if self.session:
                    if files:
                        async with self.session.post(url, data=data, files=files) as response:
                            return await response.json()
                    else:
                        async with self.session.post(url, json=data) as response:
                            return await response.json()
            else:
                raise ValueError(f"不支援的 HTTP 方法: {method}")
        except Exception as e:
            return {"error": str(e)}
        return {"error": "Session not available"}
    
    # ==================== 頁面訪問測試 ====================
    
    async def test_pages(self):
        """測試頁面訪問"""
        logger.info("🌐 開始測試頁面訪問...")
        
        # 測試首頁
        try:
            if self.session:
                async with self.session.get(f"{BASE_URL}/") as response:
                    success = response.status == 200
                    content = await response.text()
                    self.log_test("首頁訪問", success, {"status": response.status, "content_length": len(content)})
        except Exception as e:
            self.log_test("首頁訪問", False, error=str(e))
        
        # 測試 Podri 頁面
        try:
            if self.session:
                async with self.session.get(f"{BASE_URL}/podri.html") as response:
                    success = response.status == 200
                    content = await response.text()
                    self.log_test("Podri 頁面訪問", success, {"status": response.status, "content_length": len(content)})
        except Exception as e:
            self.log_test("Podri 頁面訪問", False, error=str(e))
        
        # 測試健康檢查
        response = await self.make_request("GET", "/health")
        success = "error" not in response and response.get("status") == "healthy"
        self.log_test("健康檢查", success, response)
    
    # ==================== 用戶管理測試 ====================
    
    async def test_user_management(self):
        """測試用戶管理功能"""
        logger.info("👤 開始測試用戶管理...")
        
        # 生成 Podwise ID
        response = await self.make_request("POST", "/api/generate-podwise-id")
        success = "error" not in response and response.get("success")
        self.log_test("生成 Podwise ID", success, response)
        
        if success:
            user_id = response.get("user_id", "Podwise0001")
            
            # 檢查用戶存在性
            response = await self.make_request("GET", f"/api/user/check/{user_id}")
            success = "error" not in response and response.get("success")
            self.log_test("檢查用戶存在性", success, response)
            
            # 保存用戶偏好
            preferences_data = {
                "user_id": user_id,
                "main_category": "business",
                "sub_category": "投資理財"
            }
            response = await self.make_request("POST", "/api/user/preferences", preferences_data)
            success = "error" not in response and response.get("success")
            self.log_test("保存用戶偏好", success, response)
        else:
            self.log_test("檢查用戶存在性", False, error="無法生成用戶 ID")
            self.log_test("保存用戶偏好", False, error="無法生成用戶 ID")
    
    # ==================== 推薦系統測試 ====================
    
    async def test_recommendation_system(self):
        """測試推薦系統"""
        logger.info("🎯 開始測試推薦系統...")
        
        # 獲取類別標籤
        response = await self.make_request("GET", "/api/category-tags/business")
        success = "error" not in response and response.get("success")
        self.log_test("獲取商業類別標籤", success, response)
        
        response = await self.make_request("GET", "/api/category-tags/education")
        success = "error" not in response and response.get("success")
        self.log_test("獲取教育類別標籤", success, response)
        
        # 獲取節目推薦
        response = await self.make_request("GET", "/api/one-minutes-episodes?category=business&tag=投資理財")
        success = "error" not in response and response.get("success")
        self.log_test("獲取商業節目推薦", success, response)
        
        response = await self.make_request("GET", "/api/one-minutes-episodes?category=education&tag=學習方法")
        success = "error" not in response and response.get("success")
        self.log_test("獲取教育節目推薦", success, response)
    
    # ==================== 音檔管理測試 ====================
    
    async def test_audio_management(self):
        """測試音檔管理"""
        logger.info("🎵 開始測試音檔管理...")
        
        # 獲取隨機音檔
        random_audio_data = {"category": "business"}
        response = await self.make_request("POST", "/api/random-audio", random_audio_data)
        success = "error" not in response and response.get("success")
        self.log_test("獲取隨機商業音檔", success, response)
        
        random_audio_data = {"category": "education"}
        response = await self.make_request("POST", "/api/random-audio", random_audio_data)
        success = "error" not in response and response.get("success")
        self.log_test("獲取隨機教育音檔", success, response)
        
        # 獲取預簽名 URL
        audio_request_data = {
            "rss_id": "RSS_1531106786",
            "episode_title": "投資理財精選",
            "category": "business"
        }
        response = await self.make_request("POST", "/api/audio/presigned-url", audio_request_data)
        success = "error" not in response and response.get("success")
        self.log_test("獲取音檔預簽名 URL", success, response)
    
    # ==================== 反饋系統測試 ====================
    
    async def test_feedback_system(self):
        """測試反饋系統"""
        logger.info("💬 開始測試反饋系統...")
        
        # 記錄播放反饋
        feedback_data = {
            "user_id": "Podwise0001",
            "episode_id": 1,
            "podcast_name": "股癌 Gooaye",
            "episode_title": "投資理財精選",
            "rss_id": "RSS_1531106786",
            "action": "play",
            "category": "business"
        }
        response = await self.make_request("POST", "/api/feedback", feedback_data)
        success = "error" not in response and response.get("success")
        self.log_test("記錄播放反饋", success, response)
        
        # 記錄喜歡反饋
        feedback_data["action"] = "like"
        response = await self.make_request("POST", "/api/feedback", feedback_data)
        success = "error" not in response and response.get("success")
        self.log_test("記錄喜歡反饋", success, response)
    
    # ==================== RAG Pipeline 測試 ====================
    
    async def test_rag_pipeline(self):
        """測試 RAG Pipeline"""
        logger.info("🤖 開始測試 RAG Pipeline...")
        
        # 測試查詢
        query_data = {
            "query": "什麼是投資理財？",
            "user_id": "Podwise0001",
            "session_id": f"session_{int(time.time())}",
            "enable_tts": False,
            "voice": "podrina",
            "speed": 1.0,
            "metadata": {
                "source": "test",
                "timestamp": time.time()
            }
        }
        response = await self.make_request("POST", "/api/v1/query", query_data)
        success = "error" not in response and response.get("success")
        self.log_test("RAG Pipeline 查詢", success, response)
    
    # ==================== TTS 測試 ====================
    
    async def test_tts(self):
        """測試 TTS 功能"""
        logger.info("🔊 開始測試 TTS...")
        
        # 測試語音合成
        tts_data = {
            "text": "您好，這是 TTS 測試。",
            "voice": "podrina",
            "speed": "+0%"
        }
        response = await self.make_request("POST", "/api/v1/tts/synthesize", tts_data)
        success = "error" not in response and response.get("success")
        self.log_test("TTS 語音合成", success, response)
    
    # ==================== STT 測試 ====================
    
    async def test_stt(self):
        """測試 STT 功能"""
        logger.info("🎤 開始測試 STT...")
        
        # 創建測試音檔（這裡只是測試 API 調用，實際需要真實音檔）
        test_audio_content = b"fake audio content"
        
        # 測試語音轉文字
        files = {"file": ("test_audio.wav", test_audio_content, "audio/wav")}
        response = await self.make_request("POST", "/api/v1/stt/transcribe", files=files)
        # STT 可能會失敗，因為沒有真實音檔，但 API 調用應該成功
        success = "error" not in response
        self.log_test("STT 語音轉文字", success, response)
    
    # ==================== 服務狀態測試 ====================
    
    async def test_service_status(self):
        """測試服務狀態"""
        logger.info("📊 開始測試服務狀態...")
        
        # 獲取所有服務狀態
        response = await self.make_request("GET", "/api/v1/services")
        success = "error" not in response and "services" in response
        self.log_test("獲取服務狀態", success, response)
    
    # ==================== 完整測試流程 ====================
    
    async def run_all_tests(self):
        """運行所有測試"""
        logger.info("🚀 開始運行 Podwise 統一 API Gateway 完整測試...")
        self.start_time = time.time()
        
        try:
            # 1. 頁面訪問測試
            await self.test_pages()
            
            # 2. 用戶管理測試
            await self.test_user_management()
            
            # 3. 推薦系統測試
            await self.test_recommendation_system()
            
            # 4. 音檔管理測試
            await self.test_audio_management()
            
            # 5. 反饋系統測試
            await self.test_feedback_system()
            
            # 6. RAG Pipeline 測試
            await self.test_rag_pipeline()
            
            # 7. TTS 測試
            await self.test_tts()
            
            # 8. STT 測試
            await self.test_stt()
            
            # 9. 服務狀態測試
            await self.test_service_status()
            
        except Exception as e:
            logger.error(f"測試過程中發生錯誤: {e}")
        
        # 生成測試報告
        self.generate_test_report()
    
    def generate_test_report(self):
        """生成測試報告"""
        end_time = time.time()
        duration = end_time - (self.start_time or 0)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info("\n" + "="*60)
        logger.info("📋 測試報告")
        logger.info("="*60)
        logger.info(f"總測試數: {total_tests}")
        logger.info(f"通過: {passed_tests} ✅")
        logger.info(f"失敗: {failed_tests} ❌")
        logger.info(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        logger.info(f"測試耗時: {duration:.2f} 秒")
        logger.info("="*60)
        
        # 顯示失敗的測試
        if failed_tests > 0:
            logger.info("\n❌ 失敗的測試:")
            for result in self.test_results:
                if not result["success"]:
                    logger.error(f"  - {result['test_name']}: {result.get('error', '未知錯誤')}")
        
        # 保存詳細報告到檔案
        report_data = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": passed_tests/total_tests*100,
                "duration": duration,
                "timestamp": time.time()
            },
            "results": self.test_results
        }
        
        report_file = Path("test_report.json")
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n📄 詳細報告已保存到: {report_file.absolute()}")


async def main():
    """主函數"""
    logger.info("🎯 Podwise 統一 API Gateway 測試工具")
    logger.info(f"目標服務: {BASE_URL}")
    logger.info("="*60)
    
    # 檢查服務是否可用
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    logger.info("✅ 服務可用，開始測試...")
                else:
                    logger.error(f"❌ 服務不可用，狀態碼: {response.status}")
                    return
    except Exception as e:
        logger.error(f"❌ 無法連接到服務: {e}")
        logger.info("請確保服務正在運行: python unified_api_gateway.py")
        return
    
    # 運行測試
    async with SimpleAPITester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    # 檢查命令行參數
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("""
Podwise 統一 API Gateway 測試工具

使用方法:
    python simple_test_api.py                    # 運行所有測試
    python simple_test_api.py --help            # 顯示幫助

環境要求:
    - 確保 unified_api_gateway.py 正在運行
    - 確保所有依賴服務可用 (TTS, STT, RAG Pipeline 等)

測試內容:
    - 頁面訪問測試
    - 用戶管理測試
    - 推薦系統測試
    - 音檔管理測試
    - 反饋系統測試
    - RAG Pipeline 測試
    - TTS/STT 測試
    - 服務狀態測試
            """)
            sys.exit(0)
    
    # 運行測試
    asyncio.run(main()) 