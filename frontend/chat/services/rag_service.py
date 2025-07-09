#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG 服務模組
處理 RAG 相關功能
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List, Optional
import os


class RAGService:
    """RAG 服務類別"""
    
    def __init__(self):
        """初始化 RAG 服務"""
        # 服務端點配置
        self.k8s_rag_url = os.getenv("K8S_RAG_URL", "http://localhost:30002")
        self.rag_url = os.getenv("RAG_URL", "http://localhost:8002")
        self.container_rag_url = os.getenv("CONTAINER_RAG_URL", "http://rag-pipeline:8002")
        
        # 預設配置
        self.default_config = {
            "max_tokens": 1000,
            "temperature": 0.7,
            "top_k": 5,
            "top_p": 0.9
        }
    
    async def send_message(self, message: str, user_id: str = None) -> Dict[str, Any]:
        """發送訊息到 RAG 服務"""
        try:
            # 嘗試從 RAG 服務獲取回答
            rag_endpoints = [
                self.k8s_rag_url,      # K8s NodePort 服務
                self.rag_url,          # 本地開發
                self.container_rag_url # 容器環境
            ]
            
            payload = {
                "message": message,
                "user_id": user_id or "guest",
                "config": self.default_config
            }
            
            for endpoint in rag_endpoints:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{endpoint}/chat",
                            json=payload,
                            timeout=60
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                if data.get("success"):
                                    return {
                                        "success": True,
                                        "response": data.get("response", ""),
                                        "sources": data.get("sources", []),
                                        "confidence": data.get("confidence", 0.0),
                                        "processing_time": data.get("processing_time", 0.0)
                                    }
                                else:
                                    continue
                            else:
                                continue
                                
                except Exception as e:
                    continue
            
            # 如果所有服務都失敗，返回預設回答
            return {
                "success": True,
                "response": "抱歉，RAG 服務目前正在維護中。我可以為您提供一般性的回答，但無法訪問特定的知識庫內容。",
                "sources": [],
                "confidence": 0.0,
                "processing_time": 0.0,
                "fallback": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"RAG 服務錯誤: {str(e)}"
            }
    
    async def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜尋文件"""
        try:
            rag_endpoints = [
                self.k8s_rag_url,
                self.rag_url,
                self.container_rag_url
            ]
            
            payload = {
                "query": query,
                "top_k": top_k
            }
            
            for endpoint in rag_endpoints:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{endpoint}/search",
                            json=payload,
                            timeout=30
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                if data.get("success"):
                                    return data.get("results", [])
                                else:
                                    continue
                            else:
                                continue
                                
                except Exception as e:
                    continue
            
            return []
            
        except Exception as e:
            print(f"❌ 搜尋文件失敗: {str(e)}")
            return []
    
    def check_service_status(self) -> Dict[str, Any]:
        """檢查服務狀態"""
        try:
            import requests
            
            rag_endpoints = [
                self.k8s_rag_url,
                self.rag_url,
                self.container_rag_url
            ]
            
            for endpoint in rag_endpoints:
                try:
                    response = requests.get(f"{endpoint}/health", timeout=5)
                    if response.status_code == 200:
                        return {"status": "healthy", "endpoint": endpoint}
                except Exception as e:
                    continue
            
            return {"status": "unhealthy", "error": "無法連接到任何 RAG 服務"}
            
        except ImportError:
            return {"status": "unhealthy", "error": "缺少 requests 模組"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def get_chat_history(self, user_id: str) -> List[Dict[str, Any]]:
        """獲取聊天歷史"""
        try:
            rag_endpoints = [
                self.k8s_rag_url,
                self.rag_url,
                self.container_rag_url
            ]
            
            for endpoint in rag_endpoints:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"{endpoint}/history/{user_id}",
                            timeout=10
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                if data.get("success"):
                                    return data.get("history", [])
                                else:
                                    continue
                            else:
                                continue
                                
                except Exception as e:
                    continue
            
            return []
            
        except Exception as e:
            print(f"❌ 獲取聊天歷史失敗: {str(e)}")
            return []
    
    async def clear_chat_history(self, user_id: str) -> bool:
        """清除聊天歷史"""
        try:
            rag_endpoints = [
                self.k8s_rag_url,
                self.rag_url,
                self.container_rag_url
            ]
            
            for endpoint in rag_endpoints:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.delete(
                            f"{endpoint}/history/{user_id}",
                            timeout=10
                        ) as response:
                            if response.status == 200:
                                return True
                            else:
                                continue
                                
                except Exception as e:
                    continue
            
            return False
            
        except Exception as e:
            print(f"❌ 清除聊天歷史失敗: {str(e)}")
            return False 