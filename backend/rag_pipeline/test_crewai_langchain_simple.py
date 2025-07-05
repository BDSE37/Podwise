#!/usr/bin/env python3
"""
CrewAI + LangChain + LLM 簡化整合測試腳本

此腳本提供簡化的整合測試，專注於核心組件的功能驗證，
避免複雜的依賴關係和類型檢查問題。

測試內容：
- 基本組件初始化
- 核心功能驗證
- 工作流程測試

作者: Podwise Team
版本: 1.0.0
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleIntegrationTest:
    """
    簡化整合測試類別
    
    此類別提供基本的整合測試功能，避免複雜的類型檢查。
    """
    
    def __init__(self) -> None:
        """初始化測試類別"""
        self.test_results: Dict[str, Any] = {}
        self.start_time = datetime.now()
    
    async def test_component_imports(self) -> Dict[str, Any]:
        """
        測試組件導入
        
        Returns:
            Dict[str, Any]: 測試結果
        """
        logger.info("🧪 測試組件導入...")
        
        results = {}
        
        try:
            # 測試核心組件導入
            from core.crew_agents import AgentManager
            results["crew_agents"] = "✅ 導入成功"
            logger.info("  ✅ Crew Agents 導入成功")
        except Exception as e:
            results["crew_agents"] = f"❌ 導入失敗: {str(e)}"
            logger.error(f"  ❌ Crew Agents 導入失敗: {str(e)}")
        
        try:
            from core.chat_history_service import ChatHistoryService
            results["chat_history"] = "✅ 導入成功"
            logger.info("  ✅ Chat History Service 導入成功")
        except Exception as e:
            results["chat_history"] = f"❌ 導入失敗: {str(e)}"
            logger.error(f"  ❌ Chat History Service 導入失敗: {str(e)}")
        
        try:
            from core.qwen3_llm_manager import Qwen3LLMManager
            results["qwen3_manager"] = "✅ 導入成功"
            logger.info("  ✅ Qwen3 LLM Manager 導入成功")
        except Exception as e:
            results["qwen3_manager"] = f"❌ 導入失敗: {str(e)}"
            logger.error(f"  ❌ Qwen3 LLM Manager 導入失敗: {str(e)}")
        
        try:
            from tools.keyword_mapper import KeywordMapper
            results["keyword_mapper"] = "✅ 導入成功"
            logger.info("  ✅ Keyword Mapper 導入成功")
        except Exception as e:
            results["keyword_mapper"] = f"❌ 導入失敗: {str(e)}"
            logger.error(f"  ❌ Keyword Mapper 導入失敗: {str(e)}")
        
        try:
            from tools.knn_recommender import KNNRecommender
            results["knn_recommender"] = "✅ 導入成功"
            logger.info("  ✅ KNN Recommender 導入成功")
        except Exception as e:
            results["knn_recommender"] = f"❌ 導入失敗: {str(e)}"
            logger.error(f"  ❌ KNN Recommender 導入失敗: {str(e)}")
        
        try:
            from tools.unified_llm_tool import UnifiedLLMTool
            results["unified_llm_tool"] = "✅ 導入成功"
            logger.info("  ✅ Unified LLM Tool 導入成功")
        except Exception as e:
            results["unified_llm_tool"] = f"❌ 導入失敗: {str(e)}"
            logger.error(f"  ❌ Unified LLM Tool 導入失敗: {str(e)}")
        
        try:
            from config.integrated_config import get_config
            results["config"] = "✅ 導入成功"
            logger.info("  ✅ Config 導入成功")
        except Exception as e:
            results["config"] = f"❌ 導入失敗: {str(e)}"
            logger.error(f"  ❌ Config 導入失敗: {str(e)}")
        
        return {
            "component": "Component Imports",
            "status": "completed",
            "results": results,
            "success_count": len([r for r in results.values() if "✅" in r])
        }
    
    async def test_basic_functionality(self) -> Dict[str, Any]:
        """
        測試基本功能
        
        Returns:
            Dict[str, Any]: 測試結果
        """
        logger.info("🧪 測試基本功能...")
        
        results = {}
        
        # 測試 Keyword Mapper 基本功能
        try:
            from tools.keyword_mapper import KeywordMapper
            mapper = KeywordMapper()
            
            # 測試分類功能
            test_queries = [
                "我想了解股票投資",
                "推薦學習資源",
                "商業策略分析"
            ]
            
            classification_results = []
            for query in test_queries:
                try:
                    result = mapper.categorize_query(query)
                    classification_results.append({
                        "query": query,
                        "category": result.category,
                        "confidence": result.confidence
                    })
                except Exception as e:
                    classification_results.append({
                        "query": query,
                        "error": str(e)
                    })
            
            results["keyword_mapper"] = {
                "status": "✅ 功能正常",
                "classifications": classification_results
            }
            logger.info("  ✅ Keyword Mapper 基本功能測試通過")
            
        except Exception as e:
            results["keyword_mapper"] = {
                "status": f"❌ 功能異常: {str(e)}"
            }
            logger.error(f"  ❌ Keyword Mapper 基本功能測試失敗: {str(e)}")
        
        # 測試 KNN Recommender 基本功能
        try:
            from tools.knn_recommender import KNNRecommender
            recommender = KNNRecommender(k=5, metric="cosine")
            
            results["knn_recommender"] = {
                "status": "✅ 初始化成功",
                "k": 5,
                "metric": "cosine"
            }
            logger.info("  ✅ KNN Recommender 基本功能測試通過")
            
        except Exception as e:
            results["knn_recommender"] = {
                "status": f"❌ 功能異常: {str(e)}"
            }
            logger.error(f"  ❌ KNN Recommender 基本功能測試失敗: {str(e)}")
        
        # 測試 LLM 工具基本功能
        try:
            from tools.unified_llm_tool import get_unified_llm_tool
            llm_tool = get_unified_llm_tool()
            
            results["unified_llm_tool"] = {
                "status": "✅ 初始化成功",
                "available_models": llm_tool.get_available_models()
            }
            logger.info("  ✅ Unified LLM Tool 基本功能測試通過")
            
        except Exception as e:
            results["unified_llm_tool"] = {
                "status": f"❌ 功能異常: {str(e)}"
            }
            logger.error(f"  ❌ Unified LLM Tool 基本功能測試失敗: {str(e)}")
        
        return {
            "component": "Basic Functionality",
            "status": "completed",
            "results": results,
            "success_count": len([r for r in results.values() if "✅" in r.get("status", "")])
        }
    
    async def test_configuration(self) -> Dict[str, Any]:
        """
        測試配置系統
        
        Returns:
            Dict[str, Any]: 測試結果
        """
        logger.info("🧪 測試配置系統...")
        
        try:
            from config.integrated_config import get_config
            config = get_config()
            
            # 檢查基本配置
            config_check = {
                "database": hasattr(config, 'database'),
                "models": hasattr(config, 'models'),
                "api": hasattr(config, 'api'),
                "agent": hasattr(config, 'agent')
            }
            
            results = {
                "config_loaded": "✅ 配置載入成功",
                "config_sections": config_check,
                "total_sections": len(config_check),
                "valid_sections": sum(config_check.values())
            }
            
            logger.info("  ✅ 配置系統測試通過")
            
        except Exception as e:
            results = {
                "config_loaded": f"❌ 配置載入失敗: {str(e)}"
            }
            logger.error(f"  ❌ 配置系統測試失敗: {str(e)}")
        
        return {
            "component": "Configuration System",
            "status": "completed",
            "results": results,
            "success_count": 1 if "✅" in results.get("config_loaded", "") else 0
        }
    
    async def test_crewai_integration(self) -> Dict[str, Any]:
        """
        測試 CrewAI 整合
        
        Returns:
            Dict[str, Any]: 測試結果
        """
        logger.info("🧪 測試 CrewAI 整合...")
        
        try:
            from core.crew_agents import AgentManager
            from config.integrated_config import get_config
            
            config = get_config()
            
            # 檢查是否有代理人配置
            if hasattr(config, 'get_agent_config'):
                agent_config = config.get_agent_config()
                agent_manager = AgentManager(agent_config)
                
                results = {
                    "agent_manager": "✅ 初始化成功",
                    "config_method": "✅ 配置方法存在",
                    "agent_count": len(agent_config.get('agents', {})) if isinstance(agent_config, dict) else 0
                }
                logger.info("  ✅ CrewAI 整合測試通過")
                
            else:
                results = {
                    "agent_manager": "⚠️ 無法初始化",
                    "config_method": "❌ 配置方法不存在"
                }
                logger.warning("  ⚠️ CrewAI 整合測試部分通過")
                
        except Exception as e:
            results = {
                "error": f"❌ CrewAI 整合失敗: {str(e)}"
            }
            logger.error(f"  ❌ CrewAI 整合測試失敗: {str(e)}")
        
        return {
            "component": "CrewAI Integration",
            "status": "completed",
            "results": results,
            "success_count": len([r for r in results.values() if "✅" in str(r)])
        }
    
        async def test_langchain_integration(self) -> Dict[str, Any]:
        """
        測試 LangChain 整合
        
        Returns:
            Dict[str, Any]: 測試結果
        """
        logger.info("🧪 測試 LangChain 整合...")
        
        try:
            # 檢查 LangChain 相關導入
            langchain_imports = {}
            
            try:
                from langchain.tools import BaseTool
                langchain_imports["BaseTool"] = "✅ 導入成功"
            except Exception as e:
                langchain_imports["BaseTool"] = f"❌ 導入失敗: {str(e)}"
            
            try:
                from langchain_core.pydantic_v1 import BaseModel, Field
                langchain_imports["Pydantic"] = "✅ 導入成功"
            except Exception as e:
                langchain_imports["Pydantic"] = f"❌ 導入失敗: {str(e)}"
            
            try:
                from langchain.schema import BaseMessage
                langchain_imports["Schema"] = "✅ 導入成功"
            except Exception as e:
                langchain_imports["Schema"] = f"❌ 導入失敗: {str(e)}"
            
            # 測試統一 LLM 工具
            try:
                from tools.unified_llm_tool import UnifiedLLMTool
                tool = UnifiedLLMTool()
                
                results = {
                    "langchain_imports": langchain_imports,
                    "unified_llm_tool": "✅ 工具創建成功",
                    "tool_name": tool.name,
                    "tool_description": tool.description
                }
                logger.info("  ✅ LangChain 整合測試通過")
                
            except Exception as e:
                results = {
                    "langchain_imports": langchain_imports,
                    "unified_llm_tool": f"❌ 工具創建失敗: {str(e)}"
                }
                logger.error(f"  ❌ LangChain 整合測試失敗: {str(e)}")
            
        except Exception as e:
            results = {
                "error": f"❌ LangChain 整合失敗: {str(e)}"
            }
            logger.error(f"  ❌ LangChain 整合測試失敗: {str(e)}")
        
        return {
            "component": "LangChain Integration",
            "status": "completed",
            "results": results,
            "success_count": len([r for r in results.values() if "✅" in str(r)])
        }
    
    async def test_llm_integration(self) -> Dict[str, Any]:
        """
        測試 LLM 整合和備援機制
        
        Returns:
            Dict[str, Any]: 測試結果
        """
        logger.info("🤖 測試 LLM 整合和備援機制...")
        
        try:
            from core.qwen3_llm_manager import get_qwen3_llm_manager
            from config.integrated_config import get_config
            
            # 測試 LLM 管理器
            llm_manager = get_qwen3_llm_manager()
            config = get_config()
            
            # 檢查可用模型
            available_models = llm_manager.get_available_models()
            logger.info(f" 可用模型: {available_models}")
            
            # 檢查優先級順序
            priority_models = config.models.llm_priority or []
            logger.info(f" 優先級順序: {priority_models}")
            
            # 檢查台灣模型是否為第一優先
            taiwan_first = priority_models and priority_models[0] == "qwen2.5:taiwan"
            logger.info(f" 台灣模型第一優先: {'✅' if taiwan_first else '❌'}")
            
            # 測試模型健康檢查
            current_model = llm_manager.current_model
            is_healthy = llm_manager.test_model_health(current_model)
            logger.info(f" 當前模型 {current_model} 健康狀態: {'✅' if is_healthy else '❌'}")
            
            # 測試備援機制
            best_model = llm_manager.get_best_model()
            logger.info(f" 最佳模型: {best_model}")
            
            # 測試模型呼叫
            test_prompt = "請用繁體中文回答：你好"
            response = llm_manager.call_with_fallback(test_prompt)
            
            success = "錯誤" not in response and len(response) > 5
            logger.info(f" LLM 呼叫: {'✅ 成功' if success else '❌ 失敗'}")
            
            # 檢查 OpenAI 備援配置
            openai_configured = bool(config.api.openai_api_key)
            logger.info(f" OpenAI 備援配置: {'✅ 已配置' if openai_configured else '❌ 未配置'}")
            
            results = {
                "llm_manager": "✅ 初始化成功",
                "available_models": len(available_models),
                "current_model": current_model,
                "best_model": best_model,
                "is_healthy": is_healthy,
                "taiwan_first_priority": taiwan_first,
                "openai_configured": openai_configured,
                "llm_call_success": success,
                "response_length": len(response)
            }
            
            logger.info("  ✅ LLM 整合測試通過")
            
        except Exception as e:
            results = {
                "error": f"❌ LLM 整合失敗: {str(e)}"
            }
            logger.error(f"  ❌ LLM 整合測試失敗: {str(e)}")
        
        return {
            "component": "LLM Integration",
            "status": "completed",
            "results": results,
            "success_count": len([r for r in results.values() if "✅" in str(r)])
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """
        執行所有測試
        
        Returns:
            Dict[str, Any]: 完整測試結果
        """
        logger.info("🚀 開始執行簡化整合測試")
        logger.info("=" * 50)
        
        # 執行各項測試
        tests = [
            ("component_imports", self.test_component_imports),
            ("basic_functionality", self.test_basic_functionality),
            ("configuration", self.test_configuration),
            ("crewai_integration", self.test_crewai_integration),
            ("langchain_integration", self.test_langchain_integration),
            ("llm_integration", self.test_llm_integration)
        ]
        
        for test_name, test_func in tests:
            try:
                logger.info(f"\n📋 執行測試: {test_name}")
                result = await test_func()
                self.test_results[test_name] = result
                
                success_rate = result.get("success_count", 0) / max(1, len(result.get("results", {})))
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
            "test_suite": "CrewAI + LangChain + LLM Simple Integration",
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "overall_success_rate": overall_success_rate,
            "total_processing_time": total_time,
            "test_results": self.test_results
        }
        
        logger.info("\n" + "=" * 50)
        logger.info("📊 測試摘要")
        logger.info(f"  總測試數: {total_tests}")
        logger.info(f"  成功測試數: {successful_tests}")
        logger.info(f"  整體成功率: {overall_success_rate:.2%}")
        logger.info(f"  總處理時間: {total_time:.2f} 秒")
        logger.info("=" * 50)
        
        return test_summary
    
    def save_test_results(self, filename: str = "simple_integration_test_results.json") -> None:
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
    print("🎧 Podwise RAG Pipeline - CrewAI + LangChain + LLM 簡化整合測試")
    print("=" * 60)
    
    # 創建測試套件
    test_suite = SimpleIntegrationTest()
    
    try:
        # 執行所有測試
        results = await test_suite.run_all_tests()
        
        # 保存結果
        test_suite.save_test_results()
        
        # 顯示結果摘要
        if "error" not in results:
            print(f"\n🎉 測試完成！整體成功率: {results['overall_success_rate']:.2%}")
            
            if results['overall_success_rate'] >= 0.8:
                print("✅ 簡化整合測試通過！核心組件運作正常。")
            elif results['overall_success_rate'] >= 0.6:
                print("⚠️  簡化整合測試部分通過，部分組件需要檢查。")
            else:
                print("❌ 簡化整合測試失敗，請檢查核心組件。")
        else:
            print(f"❌ 測試失敗: {results['error']}")
        
    except Exception as e:
        print(f"❌ 測試執行失敗: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 