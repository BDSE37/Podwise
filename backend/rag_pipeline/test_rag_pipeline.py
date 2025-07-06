#!/usr/bin/env python3
"""
RAG Pipeline 完整功能測試腳本

此腳本測試 RAG Pipeline 的所有核心功能，包括：
- 客戶端初始化
- 查詢處理
- 用戶驗證
- 聊天歷史
- 系統狀態檢查

作者: Podwise Team
版本: 3.0.0
"""

import asyncio
import logging
import sys
from typing import Dict, Any

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_client_initialization():
    """測試客戶端初始化"""
    logger.info("🧪 測試客戶端初始化...")
    
    try:
        from rag_pipeline_client import RAGPipelineClient
        
        client = RAGPipelineClient()
        await client.initialize()
        
        # 檢查系統狀態
        status = client.get_system_status()
        logger.info(f"✅ 客戶端初始化成功")
        logger.info(f"   系統狀態: {status.is_ready}")
        logger.info(f"   組件狀態: {status.components}")
        
        return client
        
    except Exception as e:
        logger.error(f"❌ 客戶端初始化失敗: {str(e)}")
        raise


async def test_query_processing(client):
    """測試查詢處理"""
    logger.info("🧪 測試查詢處理...")
    
    try:
        from rag_pipeline_client import QueryRequest
        
        # 測試商業查詢
        business_request = QueryRequest(
            query="我想了解台積電的投資分析",
            user_id="test_user_001",
            use_web_search=True,
            use_smart_tags=True,
            max_recommendations=3
        )
        
        response = await client.process_query(business_request)
        
        logger.info(f"✅ 商業查詢處理成功")
        logger.info(f"   回應長度: {len(response.response)}")
        logger.info(f"   信心度: {response.confidence}")
        logger.info(f"   推薦數量: {len(response.recommendations)}")
        logger.info(f"   處理時間: {response.processing_time:.2f}秒")
        
        # 測試教育查詢
        education_request = QueryRequest(
            query="我想學習 Python 程式設計",
            user_id="test_user_001",
            use_web_search=True,
            use_smart_tags=True,
            max_recommendations=3
        )
        
        response = await client.process_query(education_request)
        
        logger.info(f"✅ 教育查詢處理成功")
        logger.info(f"   回應長度: {len(response.response)}")
        logger.info(f"   信心度: {response.confidence}")
        logger.info(f"   推薦數量: {len(response.recommendations)}")
        logger.info(f"   處理時間: {response.processing_time:.2f}秒")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 查詢處理失敗: {str(e)}")
        return False


async def test_user_validation(client):
    """測試用戶驗證"""
    logger.info("🧪 測試用戶驗證...")
    
    try:
        # 測試新用戶
        validation = await client.validate_user("new_user_001")
        
        logger.info(f"✅ 新用戶驗證成功")
        logger.info(f"   用戶 ID: {validation['user_id']}")
        logger.info(f"   是否有效: {validation['is_valid']}")
        logger.info(f"   有歷史記錄: {validation['has_history']}")
        
        # 測試現有用戶
        validation = await client.validate_user("test_user_001")
        
        logger.info(f"✅ 現有用戶驗證成功")
        logger.info(f"   用戶 ID: {validation['user_id']}")
        logger.info(f"   是否有效: {validation['is_valid']}")
        logger.info(f"   有歷史記錄: {validation['has_history']}")
        logger.info(f"   偏好類別: {validation.get('preferred_category', '無')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 用戶驗證失敗: {str(e)}")
        return False


async def test_chat_history(client):
    """測試聊天歷史"""
    logger.info("🧪 測試聊天歷史...")
    
    try:
        # 獲取聊天歷史
        history = await client.get_chat_history("test_user_001", limit=10)
        
        logger.info(f"✅ 聊天歷史獲取成功")
        logger.info(f"   歷史記錄數量: {len(history)}")
        
        if history:
            latest_record = history[0]
            logger.info(f"   最新記錄時間: {latest_record.get('timestamp', '未知')}")
            logger.info(f"   最新記錄內容: {latest_record.get('content', '未知')[:50]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 聊天歷史測試失敗: {str(e)}")
        return False


async def test_convenience_functions():
    """測試便捷函數"""
    logger.info("🧪 測試便捷函數...")
    
    try:
        from rag_pipeline_client import process_query_simple, validate_user_simple, get_chat_history_simple
        
        # 測試簡單查詢處理
        response = await process_query_simple(
            query="我想了解 NVIDIA 的發展趨勢",
            user_id="test_user_002"
        )
        
        logger.info(f"✅ 簡單查詢處理成功")
        logger.info(f"   回應長度: {len(response.response)}")
        logger.info(f"   信心度: {response.confidence}")
        
        # 測試簡單用戶驗證
        validation = await validate_user_simple("test_user_002")
        
        logger.info(f"✅ 簡單用戶驗證成功")
        logger.info(f"   是否有效: {validation['is_valid']}")
        
        # 測試簡單聊天歷史
        history = await get_chat_history_simple("test_user_002", limit=5)
        
        logger.info(f"✅ 簡單聊天歷史獲取成功")
        logger.info(f"   歷史記錄數量: {len(history)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 便捷函數測試失敗: {str(e)}")
        return False


async def test_system_components():
    """測試系統組件"""
    logger.info("🧪 測試系統組件...")
    
    try:
        # 測試工具組件
        from tools.podcast_formatter import PodcastFormatter
        from tools.smart_tag_extractor import SmartTagExtractor
        from tools.web_search_tool import WebSearchTool
        
        # 測試 Podcast 格式化工具
        formatter = PodcastFormatter()
        logger.info("✅ Podcast 格式化工具初始化成功")
        
        # 測試智能 TAG 提取工具
        tag_extractor = SmartTagExtractor()
        logger.info("✅ 智能 TAG 提取工具初始化成功")
        
        # 測試 Web Search 工具
        web_search = WebSearchTool()
        logger.info(f"✅ Web Search 工具初始化成功 (配置狀態: {web_search.is_configured()})")
        
        # 測試核心組件
        from core.crew_agents import AgentManager
        from config.crewai_config import get_crewai_config
        
        config = get_crewai_config()
        agent_manager = AgentManager(config)
        logger.info("✅ Agent Manager 初始化成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 系統組件測試失敗: {str(e)}")
        return False


async def run_performance_test(client):
    """執行性能測試"""
    logger.info("🧪 執行性能測試...")
    
    try:
        from rag_pipeline_client import QueryRequest
        import time
        
        test_queries = [
            "我想了解台積電的投資分析",
            "我想學習 Python 程式設計",
            "我想了解 NVIDIA 的發展趨勢",
            "我想學習機器學習",
            "我想了解比特幣的投資機會"
        ]
        
        total_time = 0
        success_count = 0
        
        for i, query in enumerate(test_queries, 1):
            start_time = time.time()
            
            try:
                request = QueryRequest(
                    query=query,
                    user_id=f"perf_test_user_{i}",
                    use_web_search=True,
                    use_smart_tags=True
                )
                
                response = await client.process_query(request)
                
                end_time = time.time()
                processing_time = end_time - start_time
                total_time += processing_time
                success_count += 1
                
                logger.info(f"   查詢 {i}: {processing_time:.2f}秒 (信心度: {response.confidence:.2f})")
                
            except Exception as e:
                logger.error(f"   查詢 {i} 失敗: {str(e)}")
        
        if success_count > 0:
            avg_time = total_time / success_count
            logger.info(f"✅ 性能測試完成")
            logger.info(f"   成功查詢: {success_count}/{len(test_queries)}")
            logger.info(f"   平均處理時間: {avg_time:.2f}秒")
            logger.info(f"   總處理時間: {total_time:.2f}秒")
        
        return success_count == len(test_queries)
        
    except Exception as e:
        logger.error(f"❌ 性能測試失敗: {str(e)}")
        return False


async def main():
    """主測試函數"""
    logger.info("🚀 開始 RAG Pipeline 完整功能測試")
    
    test_results = {}
    
    try:
        # 1. 測試客戶端初始化
        client = await test_client_initialization()
        test_results['initialization'] = True
        
        # 2. 測試查詢處理
        test_results['query_processing'] = await test_query_processing(client)
        
        # 3. 測試用戶驗證
        test_results['user_validation'] = await test_user_validation(client)
        
        # 4. 測試聊天歷史
        test_results['chat_history'] = await test_chat_history(client)
        
        # 5. 測試便捷函數
        test_results['convenience_functions'] = await test_convenience_functions()
        
        # 6. 測試系統組件
        test_results['system_components'] = await test_system_components()
        
        # 7. 執行性能測試
        test_results['performance'] = await run_performance_test(client)
        
        # 8. 關閉客戶端
        await client.close()
        
    except Exception as e:
        logger.error(f"❌ 測試過程中發生錯誤: {str(e)}")
        test_results['error'] = str(e)
    
    # 輸出測試結果摘要
    logger.info("\n" + "="*50)
    logger.info("📊 測試結果摘要")
    logger.info("="*50)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        if test_name == 'error':
            logger.error(f"❌ {test_name}: {result}")
        elif result:
            logger.info(f"✅ {test_name}: 通過")
            passed_tests += 1
        else:
            logger.error(f"❌ {test_name}: 失敗")
    
    logger.info(f"\n總體結果: {passed_tests}/{total_tests} 項測試通過")
    
    if passed_tests == total_tests:
        logger.info("🎉 所有測試通過！RAG Pipeline 運行正常")
        return 0
    else:
        logger.error("⚠️ 部分測試失敗，請檢查相關組件")
        return 1


if __name__ == "__main__":
    """執行測試"""
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        logger.error(f"測試執行失敗: {str(e)}")
        sys.exit(1) 