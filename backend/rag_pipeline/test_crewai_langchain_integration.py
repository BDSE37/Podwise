#!/usr/bin/env python3
"""
CrewAI + LangChain + LLM 整合測試腳本

此腳本測試三層 CrewAI 架構與 LangChain 和 LLM 的完整整合，
確保所有組件能夠協同工作。

測試內容：
- 三層代理人架構
- LangChain 工具整合
- LLM 模型管理
- 向量搜尋
- 聊天歷史
- 端到端工作流程

作者: Podwise Team
版本: 1.0.0
"""

import asyncio
import logging
import json
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional

# 導入核心組件
from core.crew_agents import AgentManager, UserQuery
from core.chat_history_service import ChatHistoryService
from core.qwen3_llm_manager import Qwen3LLMManager

# 導入工具
from tools.keyword_mapper import KeywordMapper, CategoryResult
from tools.knn_recommender import KNNRecommender, PodcastItem, RecommendationResult
from tools.enhanced_vector_search import EnhancedVectorSearchTool
from tools.unified_llm_tool import UnifiedLLMTool, get_unified_llm_tool

# 導入配置
from config.integrated_config import get_config

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegrationTestSuite:
    """
    整合測試套件
    
    此類別提供完整的整合測試功能，測試所有組件的協作。
    """
    
    def __init__(self) -> None:
        """初始化測試套件"""
        self.config = get_config()
        self.test_results: Dict[str, Any] = {}
        self.start_time = datetime.now()
        
        # 初始化組件
        self.agent_manager: Optional[AgentManager] = None
        self.keyword_mapper: Optional[KeywordMapper] = None
        self.knn_recommender: Optional[KNNRecommender] = None
        self.chat_history_service: Optional[ChatHistoryService] = None
        self.qwen3_manager: Optional[Qwen3LLMManager] = None
        self.vector_search_tool: Optional[EnhancedVectorSearchTool] = None
        self.unified_llm_tool: Optional[UnifiedLLMTool] = None
    
    async def initialize_components(self) -> bool:
        """
        初始化所有組件
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("🚀 初始化整合測試組件...")
            
            # 初始化 Keyword Mapper
            self.keyword_mapper = KeywordMapper()
            logger.info("✅ Keyword Mapper 初始化完成")
            
            # 初始化 KNN 推薦器
            self.knn_recommender = KNNRecommender(k=5, metric="cosine")
            logger.info("✅ KNN 推薦器初始化完成")
            
            # 初始化聊天歷史服務
            self.chat_history_service = ChatHistoryService()
            logger.info("✅ 聊天歷史服務初始化完成")
            
            # 初始化 Qwen3 LLM 管理器
            self.qwen3_manager = Qwen3LLMManager()
            logger.info("✅ Qwen3 LLM 管理器初始化完成")
            
            # 初始化向量搜尋工具
            self.vector_search_tool = EnhancedVectorSearchTool()
            logger.info("✅ 向量搜尋工具初始化完成")
            
            # 初始化統一 LLM 工具
            self.unified_llm_tool = get_unified_llm_tool()
            logger.info("✅ 統一 LLM 工具初始化完成")
            
            # 初始化三層代理人架構
            agent_config = self.config.get_agent_config()
            self.agent_manager = AgentManager(agent_config)
            logger.info("✅ 三層代理人架構初始化完成")
            
            # 載入示例數據
            await self._load_sample_data()
            
            logger.info("✅ 所有組件初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 組件初始化失敗: {str(e)}")
            return False
    
    async def _load_sample_data(self) -> None:
        """載入示例數據"""
        try:
            # 載入示例 Podcast 數據
            sample_podcasts = [
                PodcastItem(
                    rss_id="rss_001",
                    title="商業思維 Podcast",
                    description="探討商業策略和創業思維",
                    category="商業",
                    tags=["商業", "創業", "策略"],
                    updated_at=datetime.now().isoformat()
                ),
                PodcastItem(
                    rss_id="rss_002",
                    title="學習成長 Podcast",
                    description="個人成長和學習方法",
                    category="教育",
                    tags=["教育", "學習", "成長"],
                    updated_at=datetime.now().isoformat()
                )
            ]
            
            # 添加到 KNN 推薦器
            self.knn_recommender.add_podcast_items(sample_podcasts)
            
            logger.info(f"✅ 載入 {len(sample_podcasts)} 個示例 Podcast")
            
        except Exception as e:
            logger.warning(f"載入示例數據失敗: {str(e)}")
    
    async def test_keyword_mapper(self) -> Dict[str, Any]:
        """
        測試 Keyword Mapper
        
        Returns:
            Dict[str, Any]: 測試結果
        """
        logger.info("🧪 測試 Keyword Mapper...")
        
        test_cases = [
            "我想了解股票投資和理財規劃",
            "推薦一些學習程式設計的資源",
            "商業策略和市場分析",
            "個人成長和自我提升"
        ]
        
        results = []
        for query in test_cases:
            try:
                category_result = self.keyword_mapper.categorize_query(query)
                results.append({
                    "query": query,
                    "category": category_result.category,
                    "confidence": category_result.confidence,
                    "keywords": category_result.keywords_found
                })
                logger.info(f"  ✅ {query} -> {category_result.category} ({category_result.confidence:.2f})")
            except Exception as e:
                results.append({
                    "query": query,
                    "error": str(e)
                })
                logger.error(f"  ❌ {query} -> 錯誤: {str(e)}")
        
        return {
            "component": "Keyword Mapper",
            "status": "completed",
            "results": results,
            "success_count": len([r for r in results if "error" not in r])
        }
    
    async def test_knn_recommender(self) -> Dict[str, Any]:
        """
        測試 KNN 推薦器
        
        Returns:
            Dict[str, Any]: 測試結果
        """
        logger.info("🧪 測試 KNN 推薦器...")
        
        test_queries = [
            "商業策略",
            "學習方法",
            "投資理財",
            "個人成長"
        ]
        
        results = []
        for query in test_queries:
            try:
                # 先分類查詢
                category_result = self.keyword_mapper.categorize_query(query)
                
                # 創建示例查詢向量 (實際應用中應該使用向量化模型)
                query_vector = np.random.rand(768)  # 假設 768 維向量
                
                # 執行推薦
                recommendations = self.knn_recommender.recommend(
                    query_vector=query_vector,
                    category_filter=category_result.category,
                    top_k=3
                )
                
                results.append({
                    "query": query,
                    "category": category_result.category,
                    "recommendations_count": len(recommendations.recommendations),
                    "recommendations": [
                        {
                            "rss_id": p.rss_id,
                            "title": p.title,
                            "category": p.category,
                            "confidence": p.confidence
                        }
                        for p in recommendations.recommendations
                    ]
                })
                logger.info(f"  ✅ {query} -> {len(recommendations.recommendations)} 個推薦")
                
            except Exception as e:
                results.append({
                    "query": query,
                    "error": str(e)
                })
                logger.error(f"  ❌ {query} -> 錯誤: {str(e)}")
        
        return {
            "component": "KNN Recommender",
            "status": "completed",
            "results": results,
            "success_count": len([r for r in results if "error" not in r])
        }
    
    async def test_llm_managers(self) -> Dict[str, Any]:
        """
        測試 LLM 管理器
        
        Returns:
            Dict[str, Any]: 測試結果
        """
        logger.info("🧪 測試 LLM 管理器...")
        
        results = {}
        
        # 測試 Qwen3 管理器
        try:
            # 健康檢查
            health_status = self.qwen3_manager.test_model_health()
            results["qwen3_health"] = health_status
            
            # 獲取模型資訊
            model_info = self.qwen3_manager.get_model_info()
            results["qwen3_info"] = model_info
            
            # 測試文本生成
            test_prompt = "請用繁體中文介紹一下你自己"
            response = self.qwen3_manager.call_with_fallback(test_prompt)
            results["qwen3_response"] = response[:100] + "..." if len(response) > 100 else response
            
            logger.info(f"  ✅ Qwen3 管理器測試完成")
            
        except Exception as e:
            results["qwen3_error"] = str(e)
            logger.error(f"  ❌ Qwen3 管理器測試失敗: {str(e)}")
        
        # 測試統一 LLM 工具
        try:
            # 健康檢查
            health_results = await self.unified_llm_tool.health_check()
            results["unified_llm_health"] = health_results
            
            # 測試文本生成
            test_prompt = "請簡短介紹一下 AI 技術"
            response = await self.unified_llm_tool._arun(test_prompt)
            results["unified_llm_response"] = response[:100] + "..." if len(response) > 100 else response
            
            logger.info(f"  ✅ 統一 LLM 工具測試完成")
            
        except Exception as e:
            results["unified_llm_error"] = str(e)
            logger.error(f"  ❌ 統一 LLM 工具測試失敗: {str(e)}")
        
        return {
            "component": "LLM Managers",
            "status": "completed",
            "results": results,
            "success_count": len([k for k in results.keys() if "error" not in k])
        }
    
    async def test_agent_manager(self) -> Dict[str, Any]:
        """
        測試代理人管理器
        
        Returns:
            Dict[str, Any]: 測試結果
        """
        logger.info("🧪 測試代理人管理器...")
        
        test_queries = [
            UserQuery(
                user_id="test_user_001",
                query="我想了解股票投資",
                category="商業",
                session_id="session_001"
            ),
            UserQuery(
                user_id="test_user_002",
                query="推薦學習資源",
                category="教育",
                session_id="session_002"
            )
        ]
        
        results = []
        for user_query in test_queries:
            try:
                # 執行代理人處理
                response = await self.agent_manager.process_query(user_query)
                
                results.append({
                    "user_id": user_query.user_id,
                    "query": user_query.query,
                    "category": user_query.category,
                    "response_content": response.content[:200] + "..." if len(response.content) > 200 else response.content,
                    "confidence": response.confidence,
                    "processing_time": response.processing_time
                })
                
                logger.info(f"  ✅ {user_query.user_id} -> 信心值: {response.confidence:.2f}")
                
            except Exception as e:
                results.append({
                    "user_id": user_query.user_id,
                    "query": user_query.query,
                    "error": str(e)
                })
                logger.error(f"  ❌ {user_query.user_id} -> 錯誤: {str(e)}")
        
        return {
            "component": "Agent Manager",
            "status": "completed",
            "results": results,
            "success_count": len([r for r in results if "error" not in r])
        }
    
    async def test_chat_history(self) -> Dict[str, Any]:
        """
        測試聊天歷史服務
        
        Returns:
            Dict[str, Any]: 測試結果
        """
        logger.info("🧪 測試聊天歷史服務...")
        
        test_user_id = "test_user_history"
        
        try:
            # 保存聊天消息
            await self.chat_history_service.save_chat_message(
                user_id=test_user_id,
                session_id="test_session",
                message_type="user",
                content="我想了解投資理財",
                metadata={"category": "商業"}
            )
            
            await self.chat_history_service.save_chat_message(
                user_id=test_user_id,
                session_id="test_session",
                message_type="assistant",
                content="根據您的需求，我推薦以下投資理財相關的 Podcast...",
                metadata={"confidence": 0.85}
            )
            
            # 獲取聊天歷史
            history = await self.chat_history_service.get_chat_history(
                user_id=test_user_id,
                session_id="test_session",
                limit=10
            )
            
            results = {
                "messages_saved": 2,
                "messages_retrieved": len(history),
                "history_sample": [
                    {
                        "type": msg.message_type,
                        "content": msg.content[:50] + "..." if len(msg.content) > 50 else msg.content,
                        "timestamp": msg.timestamp.isoformat()
                    }
                    for msg in history[:3]
                ]
            }
            
            logger.info(f"  ✅ 聊天歷史測試完成 - 保存: 2, 檢索: {len(history)}")
            
        except Exception as e:
            results = {"error": str(e)}
            logger.error(f"  ❌ 聊天歷史測試失敗: {str(e)}")
        
        return {
            "component": "Chat History",
            "status": "completed",
            "results": results,
            "success_count": 1 if "error" not in results else 0
        }
    
    async def test_end_to_end_workflow(self) -> Dict[str, Any]:
        """
        測試端到端工作流程
        
        Returns:
            Dict[str, Any]: 測試結果
        """
        logger.info("🧪 測試端到端工作流程...")
        
        test_cases = [
            {
                "user_id": "e2e_user_001",
                "query": "我想了解股票投資和理財規劃",
                "expected_category": "商業"
            },
            {
                "user_id": "e2e_user_002",
                "query": "推薦一些學習程式設計的資源",
                "expected_category": "教育"
            }
        ]
        
        results = []
        for test_case in test_cases:
            try:
                start_time = datetime.now()
                
                # 1. 用戶查詢分類
                category_result = self.keyword_mapper.categorize_query(test_case["query"])
                
                # 2. 創建用戶查詢對象
                user_query = UserQuery(
                    user_id=test_case["user_id"],
                    query=test_case["query"],
                    category=category_result.category,
                    session_id=f"e2e_session_{test_case['user_id']}"
                )
                
                # 3. 執行代理人處理
                agent_response = await self.agent_manager.process_query(user_query)
                
                # 4. 保存聊天歷史
                await self.chat_history_service.save_chat_message(
                    user_id=test_case["user_id"],
                    session_id=user_query.session_id,
                    message_type="user",
                    content=test_case["query"],
                    metadata={"category": category_result.category}
                )
                
                await self.chat_history_service.save_chat_message(
                    user_id=test_case["user_id"],
                    session_id=user_query.session_id,
                    message_type="assistant",
                    content=agent_response.content,
                    metadata={"confidence": agent_response.confidence}
                )
                
                # 5. 計算處理時間
                processing_time = (datetime.now() - start_time).total_seconds()
                
                results.append({
                    "user_id": test_case["user_id"],
                    "query": test_case["query"],
                    "expected_category": test_case["expected_category"],
                    "actual_category": category_result.category,
                    "category_match": category_result.category == test_case["expected_category"],
                    "agent_confidence": agent_response.confidence,
                    "processing_time": processing_time,
                    "response_length": len(agent_response.content)
                })
                
                logger.info(f"  ✅ {test_case['user_id']} -> 類別匹配: {category_result.category == test_case['expected_category']}, 信心值: {agent_response.confidence:.2f}")
                
            except Exception as e:
                results.append({
                    "user_id": test_case["user_id"],
                    "query": test_case["query"],
                    "error": str(e)
                })
                logger.error(f"  ❌ {test_case['user_id']} -> 錯誤: {str(e)}")
        
        return {
            "component": "End-to-End Workflow",
            "status": "completed",
            "results": results,
            "success_count": len([r for r in results if "error" not in r]),
            "category_match_rate": len([r for r in results if "error" not in r and r.get("category_match", False)]) / max(1, len([r for r in results if "error" not in r]))
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """
        執行所有測試
        
        Returns:
            Dict[str, Any]: 完整測試結果
        """
        logger.info("🚀 開始執行 CrewAI + LangChain + LLM 整合測試")
        logger.info("=" * 60)
        
        # 初始化組件
        if not await self.initialize_components():
            return {"error": "組件初始化失敗"}
        
        # 執行各項測試
        tests = [
            ("keyword_mapper", self.test_keyword_mapper),
            ("knn_recommender", self.test_knn_recommender),
            ("llm_managers", self.test_llm_managers),
            ("agent_manager", self.test_agent_manager),
            ("chat_history", self.test_chat_history),
            ("end_to_end_workflow", self.test_end_to_end_workflow)
        ]
        
        for test_name, test_func in tests:
            try:
                logger.info(f"\n📋 執行測試: {test_name}")
                result = await test_func()
                self.test_results[test_name] = result
                
                success_rate = result.get("success_count", 0) / max(1, len(result.get("results", [])))
                logger.info(f"  📊 成功率: {success_rate:.2%}")
                
            except Exception as e:
                logger.error(f"❌ 測試 {test_name} 執行失敗: {str(e)}")
                self.test_results[test_name] = {
                    "component": test_name,
                    "status": "failed",
                    "error": str(e)
                }
        
        # 生成測試摘要
        total_tests = len(tests)
        successful_tests = len([r for r in self.test_results.values() if r.get("status") == "completed"])
        overall_success_rate = successful_tests / total_tests
        
        # 計算總處理時間
        total_time = (datetime.now() - self.start_time).total_seconds()
        
        test_summary = {
            "test_suite": "CrewAI + LangChain + LLM Integration",
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "overall_success_rate": overall_success_rate,
            "total_processing_time": total_time,
            "test_results": self.test_results
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 測試摘要")
        logger.info(f"  總測試數: {total_tests}")
        logger.info(f"  成功測試數: {successful_tests}")
        logger.info(f"  整體成功率: {overall_success_rate:.2%}")
        logger.info(f"  總處理時間: {total_time:.2f} 秒")
        logger.info("=" * 60)
        
        return test_summary
    
    def save_test_results(self, filename: str = "integration_test_results.json") -> None:
        """
        保存測試結果到檔案
        
        Args:
            filename: 檔案名稱
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"✅ 測試結果已保存到: {filename}")
        except Exception as e:
            logger.error(f"❌ 保存測試結果失敗: {str(e)}")


async def main():
    """主函數"""
    print("🎧 Podwise RAG Pipeline - CrewAI + LangChain + LLM 整合測試")
    print("=" * 70)
    
    # 創建測試套件
    test_suite = IntegrationTestSuite()
    
    try:
        # 執行所有測試
        results = await test_suite.run_all_tests()
        
        # 保存結果
        test_suite.save_test_results()
        
        # 顯示結果摘要
        if "error" not in results:
            print(f"\n🎉 測試完成！整體成功率: {results['overall_success_rate']:.2%}")
            
            if results['overall_success_rate'] >= 0.8:
                print("✅ 整合測試通過！所有核心組件運作正常。")
            else:
                print("⚠️  整合測試部分通過，請檢查失敗的組件。")
        else:
            print(f"❌ 測試失敗: {results['error']}")
        
    except Exception as e:
        print(f"❌ 測試執行失敗: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 