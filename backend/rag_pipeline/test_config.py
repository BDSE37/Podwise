#!/usr/bin/env python3
"""
Podwise RAG Pipeline 測試配置
用於本地測試的簡化配置
"""

import os
from typing import Dict, Any

class TestConfig:
    """測試配置類別"""
    
    def __init__(self):
        # 基本配置
        self.debug = True
        self.log_level = "INFO"
        
        # 服務埠配置
        self.rag_pipeline_port = 8004
        self.tts_port = 8002
        self.stt_port = 8003
        self.llm_port = 8004
        
        # 本地服務配置
        self.services = {
            "mongodb": {
                "host": "localhost",
                "port": 27017,
                "database": "podwise_test",
                "collection": "conversations"
            },
            "postgresql": {
                "host": "localhost",
                "port": 5432,
                "database": "podwise_test",
                "user": "podwise_user",
                "password": "podwise_password"
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 1  # 使用不同的 DB 避免衝突
            },
            "milvus": {
                "host": "localhost",
                "port": 19530,
                "collection": "podwise_test_vectors"
            },
            "ollama": {
                "host": "localhost",
                "port": 11434,
                "model": "qwen2.5:8b"
            }
        }
        
        # API 配置 (測試用)
        self.apis = {
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "enabled": bool(os.getenv("OPENAI_API_KEY", "")),
                "model": "gpt-3.5-turbo"
            },
            "anthropic": {
                "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
                "enabled": bool(os.getenv("ANTHROPIC_API_KEY", "")),
                "model": "claude-3-sonnet-20240229"
            },
            "google": {
                "api_key": os.getenv("GOOGLE_API_KEY", ""),
                "enabled": bool(os.getenv("GOOGLE_API_KEY", "")),
                "model": "gemini-pro"
            }
        }
        
        # 測試資料配置
        self.test_data = {
            "sample_queries": [
                "什麼是機器學習？",
                "如何開始學習 Python 程式設計？",
                "商業策略規劃的基本步驟有哪些？",
                "教育科技的最新發展趨勢是什麼？"
            ],
            "categories": ["商業", "教育"],
            "max_response_length": 1000
        }
    
    def get_service_url(self, service_name: str) -> str:
        """取得服務 URL"""
        if service_name not in self.services:
            raise ValueError(f"未知的服務: {service_name}")
        
        service = self.services[service_name]
        return f"http://{service['host']}:{service['port']}"
    
    def is_service_available(self, service_name: str) -> bool:
        """檢查服務是否可用"""
        try:
            import socket
            service = self.services[service_name]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((service['host'], service['port']))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def get_available_apis(self) -> Dict[str, bool]:
        """取得可用的 API"""
        return {name: config["enabled"] for name, config in self.apis.items()}
    
    def print_summary(self):
        """印出配置摘要"""
        print("🔧 Podwise RAG Pipeline 測試配置摘要")
        print("=" * 50)
        
        print(f"📊 除錯模式: {self.debug}")
        print(f"📝 日誌等級: {self.log_level}")
        print(f"🌐 RAG Pipeline 埠: {self.rag_pipeline_port}")
        
        print("\n🔌 服務狀態:")
        for service_name in self.services:
            status = "✅ 可用" if self.is_service_available(service_name) else "❌ 不可用"
            print(f"  {service_name}: {status}")
        
        print("\n🤖 API 狀態:")
        for api_name, config in self.apis.items():
            status = "✅ 已配置" if config["enabled"] else "❌ 未配置"
            print(f"  {api_name}: {status}")
        
        print("\n📚 測試類別:")
        for category in self.test_data["categories"]:
            print(f"  - {category}")
        
        print("=" * 50)

# 全域測試配置實例
test_config = TestConfig() 