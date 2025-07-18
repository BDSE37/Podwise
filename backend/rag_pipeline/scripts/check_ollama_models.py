#!/usr/bin/env python3
"""
檢查 Ollama 模型狀態腳本

檢查 Ollama 服務中的模型可用性，並提供修復建議
"""

import os
import asyncio
import aiohttp
import json
import logging
from typing import List, Dict, Any

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaModelChecker:
    """Ollama 模型檢查器"""
    
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        self.ollama_host = ollama_host
        self.required_models = {
            "llm": [
                "qwen2.5-taiwan-7b-instruct",
                "qwen2.5:8b", 
                "qwen3:8b",
                "gpt-3.5-turbo"
            ],
            "embedding": [
                "bge-m3",
                "nomic-embed-text",
                "all-minilm"
            ]
        }
    
    async def check_ollama_service(self) -> bool:
        """檢查 Ollama 服務狀態"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_host}/api/tags") as response:
                    if response.status == 200:
                        logger.info("✅ Ollama 服務正常運行")
                        return True
                    else:
                        logger.error(f"❌ Ollama 服務異常: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ 無法連接到 Ollama 服務: {e}")
            return False
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """獲取可用模型列表"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_host}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("models", [])
                    else:
                        return []
        except Exception as e:
            logger.error(f"獲取模型列表失敗: {e}")
            return []
    
    async def check_model(self, model_name: str) -> Dict[str, Any]:
        """檢查單個模型狀態"""
        try:
            async with aiohttp.ClientSession() as session:
                # 檢查模型是否存在
                async with session.post(
                    f"{self.ollama_host}/api/show",
                    json={"name": model_name}
                ) as response:
                    if response.status == 200:
                        model_info = await response.json()
                        return {
                            "name": model_name,
                            "status": "available",
                            "info": model_info
                        }
                    else:
                        return {
                            "name": model_name,
                            "status": "not_found",
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "name": model_name,
                "status": "error",
                "error": str(e)
            }
    
    async def test_embedding_model(self, model_name: str) -> Dict[str, Any]:
        """測試嵌入模型"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_host}/api/embeddings",
                    json={
                        "model": model_name,
                        "prompt": "測試文本"
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        embedding = data.get("embedding", [])
                        return {
                            "name": model_name,
                            "status": "working",
                            "dimension": len(embedding)
                        }
                    else:
                        return {
                            "name": model_name,
                            "status": "failed",
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "name": model_name,
                "status": "error",
                "error": str(e)
            }
    
    async def test_llm_model(self, model_name: str) -> Dict[str, Any]:
        """測試 LLM 模型"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": "你好",
                        "stream": False
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_text = data.get("response", "")
                        return {
                            "name": model_name,
                            "status": "working",
                            "response_length": len(response_text)
                        }
                    else:
                        return {
                            "name": model_name,
                            "status": "failed",
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "name": model_name,
                "status": "error",
                "error": str(e)
            }
    
    async def run_full_check(self) -> Dict[str, Any]:
        """執行完整檢查"""
        logger.info("🔍 開始檢查 Ollama 模型狀態...")
        
        # 檢查服務狀態
        service_ok = await self.check_ollama_service()
        if not service_ok:
            return {
                "service_status": "failed",
                "message": "Ollama 服務不可用"
            }
        
        # 獲取可用模型
        available_models = await self.get_available_models()
        available_model_names = [m.get("name", "") for m in available_models]
        
        logger.info(f"📋 可用模型: {available_model_names}")
        
        # 檢查 LLM 模型
        llm_results = []
        for model in self.required_models["llm"]:
            if model in available_model_names:
                result = await self.test_llm_model(model)
            else:
                result = {"name": model, "status": "not_installed"}
            llm_results.append(result)
        
        # 檢查嵌入模型
        embedding_results = []
        for model in self.required_models["embedding"]:
            if model in available_model_names:
                result = await self.test_embedding_model(model)
            else:
                result = {"name": model, "status": "not_installed"}
            embedding_results.append(result)
        
        return {
            "service_status": "ok",
            "available_models": available_model_names,
            "llm_models": llm_results,
            "embedding_models": embedding_results
        }
    
    def generate_fix_commands(self, check_results: Dict[str, Any]) -> List[str]:
        """生成修復命令"""
        commands = []
        
        # 檢查 LLM 模型
        for model_result in check_results.get("llm_models", []):
            if model_result.get("status") == "not_installed":
                model_name = model_result.get("name")
                if model_name == "qwen2.5-taiwan-7b-instruct":
                    commands.append(f"# 下載台灣版本模型")
                    commands.append(f"ollama pull weiren119/Qwen2.5-Taiwan-8B-Instruct")
                elif model_name == "qwen2.5:8b":
                    commands.append(f"# 下載 Qwen2.5 模型")
                    commands.append(f"ollama pull Qwen/Qwen2.5-8B-Instruct")
                elif model_name == "qwen3:8b":
                    commands.append(f"# 下載 Qwen3 模型")
                    commands.append(f"ollama pull qwen2.5:8b")
                elif model_name == "gpt-3.5-turbo":
                    commands.append(f"# 下載 GPT-3.5 模型")
                    commands.append(f"ollama pull gpt-3.5-turbo")
        
        # 檢查嵌入模型
        for model_result in check_results.get("embedding_models", []):
            if model_result.get("status") == "not_installed":
                model_name = model_result.get("name")
                if model_name == "bge-m3":
                    commands.append(f"# 下載 BGE-M3 嵌入模型")
                    commands.append(f"ollama pull BAAI/bge-m3")
                elif model_name == "nomic-embed-text":
                    commands.append(f"# 下載 Nomic 嵌入模型")
                    commands.append(f"ollama pull nomic-embed-text")
                elif model_name == "all-minilm":
                    commands.append(f"# 下載 All-MiniLM 嵌入模型")
                    commands.append(f"ollama pull all-minilm")
        
        return commands


async def main():
    """主函數"""
    # 從環境變數獲取 Ollama 主機
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    checker = OllamaModelChecker(ollama_host)
    
    # 執行檢查
    results = await checker.run_full_check()
    
    # 輸出結果
    print("\n" + "="*60)
    print("🔍 OLLAMA 模型檢查結果")
    print("="*60)
    
    if results["service_status"] == "failed":
        print("❌ Ollama 服務不可用")
        print("請檢查:")
        print("1. Ollama 服務是否啟動")
        print("2. 網路連接是否正常")
        print("3. 端口是否正確")
        return
    
    print(f"✅ Ollama 服務正常")
    print(f"📋 可用模型數量: {len(results['available_models'])}")
    
    # LLM 模型狀態
    print("\n🤖 LLM 模型狀態:")
    for model in results["llm_models"]:
        status_icon = "✅" if model["status"] == "working" else "❌"
        print(f"  {status_icon} {model['name']}: {model['status']}")
        if model.get("error"):
            print(f"     錯誤: {model['error']}")
    
    # 嵌入模型狀態
    print("\n🔢 嵌入模型狀態:")
    for model in results["embedding_models"]:
        status_icon = "✅" if model["status"] == "working" else "❌"
        dimension_info = f" ({model['dimension']}維)" if model.get("dimension") else ""
        print(f"  {status_icon} {model['name']}: {model['status']}{dimension_info}")
        if model.get("error"):
            print(f"     錯誤: {model['error']}")
    
    # 生成修復命令
    fix_commands = checker.generate_fix_commands(results)
    if fix_commands:
        print("\n🔧 修復命令:")
        print("執行以下命令來安裝缺失的模型:")
        for cmd in fix_commands:
            print(f"  {cmd}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(main()) 