#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podri 聊天系統環境配置
包含 MongoDB 和 Milvus 的 worker3 容器配置
"""

import os
from typing import Dict, Any

class PodriConfig:
    """Podri 系統配置類別"""
    
    def __init__(self):
        """初始化配置"""
        self.load_environment_config()
    
    def load_environment_config(self):
        """載入環境配置"""
        # 服務 URL 配置
        self.rag_url = os.getenv("RAG_URL", "http://rag-pipeline-service:8004")
        self.ml_url = os.getenv("ML_URL", "http://ml-pipeline-service:8004")
        self.tts_url = os.getenv("TTS_URL", "http://tts-service:8501")
        self.stt_url = os.getenv("STT_URL", "http://stt-service:8501")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        
        # MongoDB 配置 - worker3 容器
        self.mongo_host = os.getenv("MONGO_HOST", "worker3")
        self.mongo_port = int(os.getenv("MONGO_PORT", "27017"))
        self.mongo_db_name = os.getenv("MONGO_DB", "podwise")
        self.mongo_user = os.getenv("MONGO_USER", "bdse37")
        self.mongo_password = os.getenv("MONGO_PASSWORD", "")
        
        # 建構 MongoDB URI
        if self.mongo_password:
            self.mongo_uri = f"mongodb://{self.mongo_user}:{self.mongo_password}@{self.mongo_host}:{self.mongo_port}/{self.mongo_db_name}"
        else:
            self.mongo_uri = f"mongodb://{self.mongo_host}:{self.mongo_port}/{self.mongo_db_name}"
        
        # Milvus 配置 - worker3 容器
        self.milvus_host = os.getenv("MILVUS_HOST", "worker3")
        self.milvus_port = os.getenv("MILVUS_PORT", "19530")
        self.milvus_collection = os.getenv("MILVUS_COLLECTION", "podwise_vectors")
        
        # OpenAI API 配置（備援用）
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        # 系統配置
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        self.save_history = os.getenv("SAVE_HISTORY", "true").lower() == "true"
        self.auto_play_audio = os.getenv("AUTO_PLAY_AUDIO", "true").lower() == "true"
    
    def get_mongodb_config(self) -> Dict[str, Any]:
        """獲取 MongoDB 配置"""
        return {
            "host": self.mongo_host,
            "port": self.mongo_port,
            "database": self.mongo_db_name,
            "username": self.mongo_user,
            "password": self.mongo_password,
            "uri": self.mongo_uri
        }
    
    def get_milvus_config(self) -> Dict[str, Any]:
        """獲取 Milvus 配置"""
        return {
            "host": self.milvus_host,
            "port": self.milvus_port,
            "collection": self.milvus_collection
        }
    
    def get_service_urls(self) -> Dict[str, str]:
        """獲取服務 URL 配置"""
        return {
            "rag_url": self.rag_url,
            "ml_url": self.ml_url,
            "tts_url": self.tts_url,
            "stt_url": self.stt_url,
            "ollama_url": self.ollama_url
        }
    
    def validate_config(self) -> Dict[str, bool]:
        """驗證配置"""
        validation_results = {
            "mongodb_configured": bool(self.mongo_host and self.mongo_db_name),
            "milvus_configured": bool(self.milvus_host and self.milvus_port),
            "openai_configured": bool(self.openai_api_key),
            "services_configured": bool(self.rag_url and self.ml_url)
        }
        
        return validation_results
    
    def print_config_summary(self):
        """列印配置摘要"""
        print("🔧 Podri 系統配置摘要:")
        print(f"  📊 MongoDB: {self.mongo_host}:{self.mongo_port}/{self.mongo_db_name}")
        print(f"  🔍 Milvus: {self.milvus_host}:{self.milvus_port}")
        print(f"  🤖 RAG URL: {self.rag_url}")
        print(f"  📈 ML URL: {self.ml_url}")
        print(f"  🎵 TTS URL: {self.tts_url}")
        print(f"  🎤 STT URL: {self.stt_url}")
        print(f"  🧠 Ollama URL: {self.ollama_url}")
        print(f"  🔑 OpenAI API: {'已設定' if self.openai_api_key else '未設定'}")
        print(f"  🐛 Debug Mode: {self.debug_mode}")
        print(f"  💾 Save History: {self.save_history}")
        print(f"  🔊 Auto Play: {self.auto_play_audio}")

# 全域配置實例
config = PodriConfig()

if __name__ == "__main__":
    config.print_config_summary()
    validation = config.validate_config()
    print("\n✅ 配置驗證結果:")
    for key, value in validation.items():
        status = "✅" if value else "❌"
        print(f"  {status} {key}: {value}") 