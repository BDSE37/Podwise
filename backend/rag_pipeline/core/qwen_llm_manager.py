"""
Qwen3:8b LLM 管理器
支援多模型切換、台灣優化版本、Langfuse 追蹤
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from datetime import datetime

import requests
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from config.integrated_config import get_config

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Qwen3ModelConfig:
    """Qwen3 模型配置"""
    name: str
    endpoint: str
    model_type: str  # qwen3:8b, qwen3:taiwan, qwen3:7b
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None
    system_prompt: str = "你是一個專業的 AI 助手，能夠提供準確、有用的回答。"
    
    def __post_init__(self):
        if self.stop_sequences is None:
            self.stop_sequences = ["<|endoftext|>", "<|im_end|>"]


class Qwen3LLM:
    """Qwen3 LLM 實作"""
    
    def __init__(self, model_config: Qwen3ModelConfig, config: Optional[Dict[str, Any]] = None):
        self.model_config = model_config
        self.config = config or {}
    
    @property
    def _llm_type(self) -> str:
        return f"qwen3_{self.model_config.model_type}"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """執行 LLM 呼叫"""
        try:
            # 檢查是否為 OpenAI 模型
            if self.model_config.model_type.startswith("openai:"):
                return self._call_openai(prompt, stop, **kwargs)
            else:
                return self._call_qwen3(prompt, stop, **kwargs)
                
        except Exception as e:
            logger.error(f"LLM 呼叫異常: {str(e)}")
            return f"錯誤: {str(e)}"
    
    def _call_openai(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        """呼叫 OpenAI API"""
        try:
            config = get_config()
            if not config.api.openai_api_key:
                return "錯誤: OpenAI API Key 未配置"
            
            # 創建 OpenAI 客戶端
            openai_llm = ChatOpenAI(
                model=self.model_config.name,
                api_key=config.api.openai_api_key,
                temperature=self.model_config.temperature,
                max_tokens=self.model_config.max_tokens
            )
            
            # 準備消息
            messages = [
                HumanMessage(content=f"{self.model_config.system_prompt}\n\n{prompt}")
            ]
            
            # 發送請求
            response = openai_llm.invoke(messages)
            return str(response.content)
            
        except Exception as e:
            logger.error(f"OpenAI API 呼叫異常: {str(e)}")
            return f"錯誤: OpenAI API 呼叫失敗 - {str(e)}"
    
    def _call_qwen3(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        """呼叫 Qwen3 API"""
        try:
            # 準備請求參數
            request_data = {
                "model": self.model_config.name,
                "messages": [
                    {"role": "system", "content": self.model_config.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": self.model_config.max_tokens,
                "temperature": self.model_config.temperature,
                "top_p": self.model_config.top_p,
                "frequency_penalty": self.model_config.frequency_penalty,
                "presence_penalty": self.model_config.presence_penalty,
                "stream": False
            }
            
            # 添加停止序列
            if stop:
                request_data["stop"] = stop
            elif self.model_config.stop_sequences:
                request_data["stop"] = self.model_config.stop_sequences
            
            # 添加額外配置
            request_data.update(self.config)
            request_data.update(kwargs)
            
            # 發送請求
            response = requests.post(
                self.model_config.endpoint,
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                logger.error(f"Qwen3 API 錯誤: {response.status_code} - {response.text}")
                return f"錯誤: API 呼叫失敗 (狀態碼: {response.status_code})"
                
        except Exception as e:
            logger.error(f"Qwen3 API 呼叫異常: {str(e)}")
            return f"錯誤: Qwen3 API 呼叫失敗 - {str(e)}"
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """獲取識別參數"""
        return {
            "model": self.model_config.name,
            "model_type": self.model_config.model_type,
            "endpoint": self.model_config.endpoint,
            "max_tokens": self.model_config.max_tokens,
            "temperature": self.model_config.temperature
        }


class Qwen3LLMManager:
    """Qwen3 LLM 管理器"""
    
    def __init__(self):
        self.config = get_config()
        self.models: Dict[str, Qwen3LLM] = {}
        self.current_model: Optional[str] = None
        self.model_health: Dict[str, bool] = {}
        self.model_metrics: Dict[str, Dict[str, Any]] = {}
        
        # 初始化模型
        self._initialize_models()
    
    def _initialize_models(self):
        """初始化所有模型"""
        # Qwen2.5-Taiwan 台灣優化版本 (第一優先)
        qwen3_taiwan_config = Qwen3ModelConfig(
            name="weiren119/Qwen2.5-Taiwan-8B-Instruct",
            endpoint="http://worker1:11434/api/chat",
            model_type="qwen2.5:taiwan",
            system_prompt="你是一個專業的 AI 助手，特別針對台灣地區優化。請用繁體中文回答，提供準確、有用的資訊。"
        )
        
        # Qwen3:8b 主要模型 (第二優先)
        qwen3_8b_config = Qwen3ModelConfig(
            name="Qwen/Qwen2.5-8B-Instruct",
            endpoint="http://worker1:11434/api/chat",
            model_type="qwen3:8b",
            system_prompt="你是一個專業的 AI 助手，擅長中文和英文對話。請提供準確、有用的回答。"
        )
        
        # OpenAI GPT-3.5 備援模型
        if self.config.api.openai_api_key:
            openai_gpt35_config = Qwen3ModelConfig(
                name="gpt-3.5-turbo",
                endpoint="https://api.openai.com/v1/chat/completions",
                model_type="openai:gpt-3.5",
                system_prompt="你是一個專業的 AI 助手，能夠提供準確、有用的回答。"
            )
        
        # OpenAI GPT-4 最後備援模型
        if self.config.api.openai_api_key:
            openai_gpt4_config = Qwen3ModelConfig(
                name="gpt-4",
                endpoint="https://api.openai.com/v1/chat/completions",
                model_type="openai:gpt-4",
                system_prompt="你是一個專業的 AI 助手，能夠提供準確、有用的回答。"
            )
        
        # 創建模型實例
        self.models["qwen2.5:taiwan"] = Qwen3LLM(model_config=qwen3_taiwan_config)
        self.models["qwen3:8b"] = Qwen3LLM(model_config=qwen3_8b_config)
        
        # 只有在有 OpenAI API Key 時才添加 OpenAI 模型
        if self.config.api.openai_api_key:
            self.models["openai:gpt-3.5"] = Qwen3LLM(model_config=openai_gpt35_config)
            self.models["openai:gpt-4"] = Qwen3LLM(model_config=openai_gpt4_config)
        
        # 設置預設模型為台灣優化版本
        self.current_model = "qwen2.5:taiwan"
        
        # 初始化健康狀態
        for model_name in self.models.keys():
            self.model_health[model_name] = True
            self.model_metrics[model_name] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "average_response_time": 0.0,
                "last_used": None
            }
    
    def get_model(self, model_name: Optional[str] = None) -> Qwen3LLM:
        """獲取指定模型"""
        if model_name is None:
            model_name = self.current_model or "qwen2.5:taiwan"
        
        if model_name not in self.models:
            logger.warning(f"模型 {model_name} 不存在，使用預設模型")
            model_name = self.current_model or "qwen2.5:taiwan"
        
        return self.models[model_name]
    
    def switch_model(self, model_name: str) -> bool:
        """切換模型"""
        if model_name in self.models:
            self.current_model = model_name
            logger.info(f"已切換到模型: {model_name}")
            return True
        else:
            logger.error(f"模型 {model_name} 不存在")
            return False
    
    def get_available_models(self) -> List[str]:
        """獲取可用模型列表"""
        return list(self.models.keys())
    
    def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """獲取模型資訊"""
        if model_name is None:
            model_name = self.current_model
        
        if model_name not in self.models:
            return {"error": f"模型 {model_name} 不存在"}
        
        model = self.models[model_name]
        metrics = self.model_metrics[model_name]
        
        return {
            "name": model_name,
            "model_type": model.model_config.model_type,
            "endpoint": model.model_config.endpoint,
            "max_tokens": model.model_config.max_tokens,
            "temperature": model.model_config.temperature,
            "health": self.model_health[model_name],
            "metrics": metrics,
            "is_current": model_name == self.current_model
        }
    
    def test_model_health(self, model_name: Optional[str] = None) -> bool:
        """測試模型健康狀態"""
        if model_name is None:
            model_name = self.current_model
        
        if model_name not in self.models:
            return False
        
        try:
            model = self.models[model_name]
            test_prompt = "請回答：你好"
            
            start_time = datetime.now()
            response = model._call(test_prompt)
            end_time = datetime.now()
            
            response_time = (end_time - start_time).total_seconds()
            
            # 更新指標
            self.model_metrics[model_name]["total_calls"] += 1
            self.model_metrics[model_name]["last_used"] = datetime.now().isoformat()
            
            if "錯誤" not in response:
                self.model_health[model_name] = True
                self.model_metrics[model_name]["successful_calls"] += 1
                
                # 更新平均響應時間
                current_avg = self.model_metrics[model_name]["average_response_time"]
                total_calls = self.model_metrics[model_name]["total_calls"]
                self.model_metrics[model_name]["average_response_time"] = (
                    (current_avg * (total_calls - 1) + response_time) / total_calls
                )
                
                logger.info(f"模型 {model_name} 健康檢查通過，響應時間: {response_time:.2f}s")
                return True
            else:
                self.model_health[model_name] = False
                self.model_metrics[model_name]["failed_calls"] += 1
                logger.error(f"模型 {model_name} 健康檢查失敗: {response}")
                return False
                
        except Exception as e:
            self.model_health[model_name] = False
            self.model_metrics[model_name]["failed_calls"] += 1
            logger.error(f"模型 {model_name} 健康檢查異常: {str(e)}")
            return False
    
    def get_best_model(self) -> str:
        """獲取最佳可用模型"""
        # 檢查當前模型是否健康
        if self.current_model and self.test_model_health(self.current_model):
            return self.current_model
        
        # 按優先級檢查其他模型
        priority_models = self.config.models.llm_priority or []
        for model_name in priority_models:
            if model_name in self.models and self.test_model_health(model_name):
                self.switch_model(model_name)
                return model_name
        
        # 如果所有模型都不健康，返回預設模型
        logger.warning("所有模型都不健康，使用預設模型")
        return self.current_model or "qwen2.5:taiwan"
    
    def call_with_fallback(self, prompt: str, **kwargs) -> str:
        """帶回退機制的模型呼叫"""
        best_model_name = self.get_best_model()
        model = self.get_model(best_model_name)
        
        try:
            response = model._call(prompt, **kwargs)
            
            # 更新指標
            self.model_metrics[best_model_name]["total_calls"] += 1
            self.model_metrics[best_model_name]["last_used"] = datetime.now().isoformat()
            
            if "錯誤" not in response:
                self.model_metrics[best_model_name]["successful_calls"] += 1
            else:
                self.model_metrics[best_model_name]["failed_calls"] += 1
            
            return response
            
        except Exception as e:
            self.model_metrics[best_model_name]["failed_calls"] += 1
            logger.error(f"模型呼叫異常: {str(e)}")
            return f"錯誤: {str(e)}"
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """獲取指標摘要"""
        summary = {
            "current_model": self.current_model,
            "total_models": len(self.models),
            "healthy_models": sum(self.model_health.values()),
            "models": {}
        }
        
        for model_name in self.models.keys():
            summary["models"][model_name] = self.get_model_info(model_name)
        
        return summary
    
    def reset_metrics(self, model_name: Optional[str] = None):
        """重置模型指標"""
        if model_name:
            if model_name in self.model_metrics:
                self.model_metrics[model_name] = {
                    "total_calls": 0,
                    "successful_calls": 0,
                    "failed_calls": 0,
                    "average_response_time": 0.0,
                    "last_used": None
                }
        else:
            for model_name in self.model_metrics.keys():
                self.model_metrics[model_name] = {
                    "total_calls": 0,
                    "successful_calls": 0,
                    "failed_calls": 0,
                    "average_response_time": 0.0,
                    "last_used": None
                }


# 全域 LLM 管理器實例
qwen3_llm_manager = Qwen3LLMManager()


def get_qwen3_llm_manager() -> Qwen3LLMManager:
    """獲取 Qwen3 LLM 管理器實例"""
    return qwen3_llm_manager


if __name__ == "__main__":
    # 測試 LLM 管理器
    manager = get_qwen3_llm_manager()
    
    print("🔧 Qwen3 LLM 管理器測試")
    print("=" * 50)
    
    # 顯示可用模型
    print(f"可用模型: {manager.get_available_models()}")
    print(f"當前模型: {manager.current_model}")
    
    # 測試健康檢查
    print("\n🏥 模型健康檢查:")
    for model_name in manager.get_available_models():
        is_healthy = manager.test_model_health(model_name)
        print(f"  {model_name}: {'✅' if is_healthy else '❌'}")
    
    # 測試模型呼叫
    print("\n🤖 模型呼叫測試:")
    test_prompt = "請用繁體中文介紹一下你自己"
    response = manager.call_with_fallback(test_prompt)
    print(f"回應: {response}")
    
    # 顯示指標摘要
    print("\n📊 指標摘要:")
    metrics = manager.get_metrics_summary()
    print(json.dumps(metrics, indent=2, ensure_ascii=False)) 