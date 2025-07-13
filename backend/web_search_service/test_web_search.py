#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Search Service 測試腳本

測試 WebSearchExpert 和 WebSearchService 的功能。

Author: Podwise Team
License: MIT
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any

# 添加專案路徑
sys.path.append(os.path.dirname(__file__))

try:
    from rag_pipeline.tools.web_search_tool import WebSearchExpert, SearchRequest
    from core.service_manager import WebSearchService
except ImportError as e:
    print(f"匯入錯誤: {e}")
    sys.exit(1)

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_web_search_expert():
    """測試 WebSearchExpert 類別"""
    print("=== 測試 WebSearchExpert ===")
    
    try:
        # 初始化專家
        expert = WebSearchExpert()
        success = await expert.initialize()
        
        if not success:
            print("❌ WebSearchExpert 初始化失敗")
            return False
        
        print("✅ WebSearchExpert 初始化成功")
        
        # 測試健康檢查
        health = await expert.health_check()
        print(f"健康檢查結果: {health}")
        
        # 測試搜尋
        request = SearchRequest(
            query="台灣最新科技新聞",
            max_results=2,
            language="zh-TW"
        )
        
        response = await expert.search(request)
        print(f"搜尋結果: {response}")
        
        # 清理資源
        await expert.cleanup()
        print("✅ WebSearchExpert 測試完成")
        
        return True
        
    except Exception as e:
        print(f"❌ WebSearchExpert 測試失敗: {e}")
        return False


async def test_web_search_service():
    """測試 WebSearchService 類別"""
    print("\n=== 測試 WebSearchService ===")
    
    try:
        # 初始化服務
        service = WebSearchService()
        success = await service.initialize()
        
        if not success:
            print("❌ WebSearchService 初始化失敗")
            return False
        
        print("✅ WebSearchService 初始化成功")
        
        # 測試健康檢查
        health = await service.health_check()
        print(f"健康檢查結果: {health}")
        
        # 測試搜尋
        response = await service.search(
            query="AI 人工智慧發展",
            max_results=2,
            language="zh-TW"
        )
        print(f"搜尋結果: {response}")
        
        # 清理資源
        await service.cleanup()
        print("✅ WebSearchService 測試完成")
        
        return True
        
    except Exception as e:
        print(f"❌ WebSearchService 測試失敗: {e}")
        return False


async def test_api_endpoints():
    """測試 API 端點（需要服務運行）"""
    print("\n=== 測試 API 端點 ===")
    
    import httpx
    
    base_url = "http://localhost:8006"
    
    try:
        async with httpx.AsyncClient() as client:
            # 測試健康檢查
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ 健康檢查成功: {health_data}")
            else:
                print(f"❌ 健康檢查失敗: {response.status_code}")
                return False
            
            # 測試搜尋端點
            search_data = {
                "query": "機器學習應用",
                "max_results": 2,
                "language": "zh-TW"
            }
            
            response = await client.post(
                f"{base_url}/search",
                json=search_data
            )
            
            if response.status_code == 200:
                search_result = response.json()
                print(f"✅ 搜尋成功: {search_result}")
            else:
                print(f"❌ 搜尋失敗: {response.status_code} - {response.text}")
                return False
            
            # 測試簡化搜尋端點
            response = await client.post(
                f"{base_url}/search/simple?query=深度學習&max_results=1"
            )
            
            if response.status_code == 200:
                simple_result = response.json()
                print(f"✅ 簡化搜尋成功: {simple_result}")
            else:
                print(f"❌ 簡化搜尋失敗: {response.status_code}")
                return False
            
            # 測試服務資訊端點
            response = await client.get(f"{base_url}/info")
            if response.status_code == 200:
                info = response.json()
                print(f"✅ 服務資訊: {info}")
            else:
                print(f"❌ 服務資訊失敗: {response.status_code}")
                return False
        
        print("✅ API 端點測試完成")
        return True
        
    except Exception as e:
        print(f"❌ API 端點測試失敗: {e}")
        return False


async def test_integration():
    """測試整合功能"""
    print("\n=== 測試整合功能 ===")
    
    try:
        # 測試 fallback 機制
        from rag_pipeline.tools.web_search_tool import get_web_search_expert
        
        expert = get_web_search_expert()
        await expert.initialize()
        
        # 模擬 RAG 信心度不足的情況
        query = "最新的量子計算技術發展"
        
        # 執行網路搜尋
        request = SearchRequest(query=query, max_results=3)
        response = await expert.search(request)
        
        print(f"查詢: {query}")
        print(f"信心度: {response.confidence}")
        print(f"結果數量: {response.total_results}")
        print(f"摘要: {response.summary}")
        
        if response.confidence > 0.7:
            print("✅ 高信心度結果，適合作為 fallback 回應")
        else:
            print("⚠️ 信心度較低，可能需要進一步處理")
        
        await expert.cleanup()
        print("✅ 整合功能測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 整合功能測試失敗: {e}")
        return False


def print_test_summary(results: Dict[str, bool]):
    """印出測試摘要"""
    print("\n" + "="*50)
    print("測試摘要")
    print("="*50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
    
    print(f"\n總計: {total_tests} 個測試")
    print(f"通過: {passed_tests} 個")
    print(f"失敗: {failed_tests} 個")
    
    if failed_tests == 0:
        print("\n🎉 所有測試都通過了！")
    else:
        print(f"\n⚠️ 有 {failed_tests} 個測試失敗")


async def main():
    """主測試函數"""
    print("開始 Web Search Service 測試...")
    print("請確保已設定 OPENAI_API_KEY 環境變數")
    
    # 檢查環境變數
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ 錯誤: 未設定 OPENAI_API_KEY 環境變數")
        print("請設定環境變數後再執行測試")
        return
    
    results = {}
    
    # 執行測試
    results["WebSearchExpert"] = await test_web_search_expert()
    results["WebSearchService"] = await test_web_search_service()
    results["整合功能"] = await test_integration()
    
    # API 端點測試（可選）
    try:
        results["API 端點"] = await test_api_endpoints()
    except Exception as e:
        print(f"⚠️ API 端點測試跳過: {e}")
        results["API 端點"] = False
    
    # 印出摘要
    print_test_summary(results)


if __name__ == "__main__":
    asyncio.run(main()) 