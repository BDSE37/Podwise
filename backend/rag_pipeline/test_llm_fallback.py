"""
LLM 優先級和備援機制測試
確保 Qwen2.5-Taiwan 和 Qwen3:8b 優先使用，只有在這兩個都不行時才啟動 OpenAI 備援
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, List
from datetime import datetime

# 添加路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.qwen3_llm_manager import get_qwen3_llm_manager
from config.integrated_config import get_config

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMFallbackTest:
    """LLM 備援機制測試類別"""
    
    def __init__(self):
        self.config = get_config()
        self.llm_manager = get_qwen3_llm_manager()
        self.test_results: Dict[str, Any] = {}
        
    def test_model_availability(self) -> Dict[str, bool]:
        """測試所有模型的可用性"""
        logger.info("🔍 測試模型可用性...")
        
        available_models = self.llm_manager.get_available_models()
        model_health = {}
        
        for model_name in available_models:
            logger.info(f"測試模型: {model_name}")
            is_healthy = self.llm_manager.test_model_health(model_name)
            model_health[model_name] = is_healthy
            status = "✅ 健康" if is_healthy else "❌ 不可用"
            logger.info(f"  {model_name}: {status}")
        
        return model_health
    
    def test_priority_order(self) -> Dict[str, Any]:
        """測試模型優先級順序"""
        logger.info("📋 測試模型優先級順序...")
        
        priority_models = self.config.models.llm_priority or []
        logger.info(f"配置的優先級順序: {priority_models}")
        
        # 檢查優先級模型是否都存在
        available_models = self.llm_manager.get_available_models()
        missing_models = [model for model in priority_models if model not in available_models]
        
        if missing_models:
            logger.warning(f"⚠️  缺少優先級模型: {missing_models}")
        
        return {
            "priority_order": priority_models,
            "available_models": available_models,
            "missing_models": missing_models
        }
    
    def test_fallback_mechanism(self) -> Dict[str, Any]:
        """測試備援機制"""
        logger.info("🔄 測試備援機制...")
        
        test_prompt = "請用繁體中文回答：你好，請簡單介紹一下你自己"
        
        # 測試最佳模型選擇
        best_model = self.llm_manager.get_best_model()
        logger.info(f"選擇的最佳模型: {best_model}")
        
        # 測試模型呼叫
        try:
            response = self.llm_manager.call_with_fallback(test_prompt)
            logger.info(f"模型回應: {response[:100]}...")
            
            success = "錯誤" not in response and len(response) > 10
            logger.info(f"呼叫結果: {'✅ 成功' if success else '❌ 失敗'}")
            
        except Exception as e:
            logger.error(f"模型呼叫異常: {str(e)}")
            success = False
            response = f"錯誤: {str(e)}"
        
        return {
            "best_model": best_model,
            "response": response,
            "success": success
        }
    
    def test_openai_fallback(self) -> Dict[str, Any]:
        """測試 OpenAI 備援功能"""
        logger.info("🤖 測試 OpenAI 備援功能...")
        
        # 檢查 OpenAI API Key
        openai_configured = bool(self.config.api.openai_api_key)
        logger.info(f"OpenAI API Key 配置: {'✅ 已配置' if openai_configured else '❌ 未配置'}")
        
        if not openai_configured:
            return {
                "configured": False,
                "message": "OpenAI API Key 未配置，無法測試備援功能"
            }
        
        # 檢查 OpenAI 模型是否可用
        openai_models = ["openai:gpt-3.5", "openai:gpt-4"]
        available_openai_models = []
        
        for model_name in openai_models:
            if model_name in self.llm_manager.models:
                is_healthy = self.llm_manager.test_model_health(model_name)
                if is_healthy:
                    available_openai_models.append(model_name)
                logger.info(f"  {model_name}: {'✅ 可用' if is_healthy else '❌ 不可用'}")
        
        return {
            "configured": True,
            "available_models": available_openai_models,
            "total_openai_models": len(openai_models)
        }
    
    def test_taiwan_model_priority(self) -> Dict[str, Any]:
        """測試台灣模型優先級"""
        logger.info("🇹🇼 測試台灣模型優先級...")
        
        # 檢查台灣模型是否為第一優先
        priority_models = self.config.models.llm_priority or []
        taiwan_model = "qwen2.5:taiwan"
        
        is_first_priority = priority_models and priority_models[0] == taiwan_model
        logger.info(f"台灣模型是否為第一優先: {'✅ 是' if is_first_priority else '❌ 否'}")
        
        # 檢查台灣模型是否可用
        taiwan_available = taiwan_model in self.llm_manager.models
        if taiwan_available:
            taiwan_healthy = self.llm_manager.test_model_health(taiwan_model)
            logger.info(f"台灣模型可用性: {'✅ 健康' if taiwan_healthy else '❌ 不可用'}")
        else:
            logger.warning("⚠️  台灣模型未配置")
            taiwan_healthy = False
        
        return {
            "is_first_priority": is_first_priority,
            "available": taiwan_available,
            "healthy": taiwan_healthy
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """執行所有測試"""
        logger.info("🚀 開始 LLM 備援機制測試")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        # 執行各項測試
        self.test_results["model_availability"] = self.test_model_availability()
        self.test_results["priority_order"] = self.test_priority_order()
        self.test_results["fallback_mechanism"] = self.test_fallback_mechanism()
        self.test_results["openai_fallback"] = self.test_openai_fallback()
        self.test_results["taiwan_priority"] = self.test_taiwan_model_priority()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 計算測試結果
        self.test_results["summary"] = self._calculate_summary()
        self.test_results["duration"] = duration
        
        logger.info("=" * 60)
        logger.info("📊 測試結果摘要:")
        self._print_summary()
        
        return self.test_results
    
    def _calculate_summary(self) -> Dict[str, Any]:
        """計算測試摘要"""
        # 模型可用性
        available_models = sum(self.test_results["model_availability"].values())
        total_models = len(self.test_results["model_availability"])
        availability_rate = available_models / total_models if total_models > 0 else 0
        
        # 優先級配置
        priority_correct = self.test_results["taiwan_priority"]["is_first_priority"]
        
        # 備援機制
        fallback_success = self.test_results["fallback_mechanism"]["success"]
        
        # OpenAI 備援
        openai_configured = self.test_results["openai_fallback"]["configured"]
        
        return {
            "availability_rate": availability_rate,
            "priority_correct": priority_correct,
            "fallback_success": fallback_success,
            "openai_configured": openai_configured,
            "overall_success": availability_rate > 0 and fallback_success
        }
    
    def _print_summary(self):
        """列印測試摘要"""
        summary = self.test_results["summary"]
        
        print(f"\n📈 測試摘要:")
        print(f"  模型可用率: {summary['availability_rate']:.2%}")
        print(f"  優先級配置正確: {'✅' if summary['priority_correct'] else '❌'}")
        print(f"  備援機制正常: {'✅' if summary['fallback_success'] else '❌'}")
        print(f"  OpenAI 備援配置: {'✅' if summary['openai_configured'] else '❌'}")
        print(f"  整體測試結果: {'✅ 通過' if summary['overall_success'] else '❌ 失敗'}")
        
        print(f"\n⏱️  測試耗時: {self.test_results['duration']:.2f} 秒")
        
        # 詳細資訊
        print(f"\n🔍 詳細資訊:")
        print(f"  可用模型: {list(self.test_results['model_availability'].keys())}")
        print(f"  優先級順序: {self.test_results['priority_order']['priority_order']}")
        print(f"  最佳模型: {self.test_results['fallback_mechanism']['best_model']}")
        
        if self.test_results['openai_fallback']['configured']:
            print(f"  OpenAI 可用模型: {self.test_results['openai_fallback']['available_models']}")


async def main():
    """主函數"""
    try:
        # 創建測試實例
        test_suite = LLMFallbackTest()
        
        # 執行所有測試
        results = test_suite.run_all_tests()
        
        # 返回測試結果
        return results
        
    except Exception as e:
        logger.error(f"測試執行失敗: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }


if __name__ == "__main__":
    # 執行測試
    results = asyncio.run(main())
    
    # 檢查測試結果
    if results.get("success", True):
        print("\n🎉 LLM 備援機制測試完成！")
        sys.exit(0)
    else:
        print(f"\n❌ 測試失敗: {results.get('error', '未知錯誤')}")
        sys.exit(1) 