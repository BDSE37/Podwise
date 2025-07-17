#!/usr/bin/env python3
"""
整合服務管理器

整合 LLM 和 ML Pipeline 模組，確保 RAG Pipeline 能正確調用這些服務
提供統一的介面來管理所有外部服務

作者: Podwise Team
版本: 1.0.0
"""

import os
import sys
import logging
import asyncio
import httpx
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pathlib import Path

# 添加後端根目錄到 Python 路徑
current_dir = Path(__file__).parent.parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

logger = logging.getLogger(__name__)


class LLMService:
    """LLM 服務整合器"""
    
    def __init__(self, llm_module_path: str = "../llm"):
        """
        初始化 LLM 服務
        
        Args:
            llm_module_path: LLM 模組路徑
        """
        self.llm_module_path = llm_module_path
        self.llm_manager = None
        self.is_initialized = False
        
        logger.info("LLM 服務整合器初始化完成")
    
    async def initialize(self) -> bool:
        """初始化 LLM 服務"""
        try:
            # 動態導入 LLM 模組
            llm_path = Path(self.llm_module_path).resolve()
            if llm_path.exists():
                sys.path.insert(0, str(llm_path.parent))
                
                try:
                    from llm.main import get_llm_manager, LLMConfig
                    
                    # 初始化 LLM 管理器
                    config = LLMConfig(
                        enable_qwen_taiwan=True,
                        enable_qwen3=True,
                        enable_fallback=True,
                        max_tokens=2048,
                        temperature=0.7
                    )
                    
                    self.llm_manager = get_llm_manager(config)
                    
                    # 測試初始化
                    if self.llm_manager and hasattr(self.llm_manager, 'models') and self.llm_manager.models:
                        self.is_initialized = True
                        logger.info("✅ LLM 服務初始化成功")
                        return True
                    else:
                        logger.warning("LLM 管理器初始化失敗")
                        return False
                    
                except ImportError as e:
                    logger.warning(f"LLM 模組導入失敗: {e}")
                    return False
            else:
                logger.warning(f"LLM 模組路徑不存在: {llm_path}")
                return False
                
        except Exception as e:
            logger.error(f"LLM 服務初始化失敗: {e}")
            return False
    
    async def generate_text(self, prompt: str, model_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """生成文字"""
        if not self.is_initialized or not self.llm_manager:
            return {
                "success": False,
                "error": "LLM 服務未初始化",
                "prompt": prompt
            }
        
        try:
            result = await self.llm_manager.generate_text(prompt, model_name, **kwargs)
            return result
            
        except Exception as e:
            logger.error(f"LLM 文字生成失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "prompt": prompt
            }
    
    def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        if not self.is_initialized or not self.llm_manager:
            return {
                "status": "unhealthy",
                "error": "LLM 服務未初始化",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            health = self.llm_manager.health_check()
            return health
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_service_info(self) -> Dict[str, Any]:
        """獲取服務資訊"""
        if not self.is_initialized or not self.llm_manager:
            return {
                "module": "llm",
                "status": "uninitialized",
                "error": "LLM 服務未初始化"
            }
        
        try:
            info = self.llm_manager.get_service_info()
            return info
            
        except Exception as e:
            return {
                "module": "llm",
                "status": "error",
                "error": str(e)
            }


class MLPipelineService:
    """ML Pipeline 服務整合器"""
    
    def __init__(self, ml_pipeline_url: str = "http://localhost:8001"):
        """
        初始化 ML Pipeline 服務
        
        Args:
            ml_pipeline_url: ML Pipeline API URL
        """
        self.ml_pipeline_url = ml_pipeline_url
        self.http_client = None
        self.is_initialized = False
        
        logger.info("ML Pipeline 服務整合器初始化完成")
    
    async def initialize(self) -> bool:
        """初始化 ML Pipeline 服務"""
        try:
            # 初始化 HTTP 客戶端
            self.http_client = httpx.AsyncClient(
                timeout=30.0,
                base_url=self.ml_pipeline_url
            )
            
            # 測試連接
            response = await self.http_client.get("/health")
            if response.status_code == 200:
                self.is_initialized = True
                logger.info("✅ ML Pipeline 服務初始化成功")
                return True
            else:
                logger.warning(f"ML Pipeline 服務健康檢查失敗: {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"ML Pipeline 服務初始化失敗: {e}")
            return False
    
    async def get_recommendations(self, 
                                user_id: str, 
                                top_k: int = 10, 
                                category_filter: Optional[str] = None,
                                context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """獲取推薦"""
        if not self.is_initialized or not self.http_client:
            return {
                "success": False,
                "error": "ML Pipeline 服務未初始化",
                "recommendations": []
            }
        
        try:
            payload = {
                "user_id": int(user_id) if user_id.isdigit() else hash(user_id) % 1000000,
                "top_k": top_k,
                "category_filter": category_filter,
                "context": context or {}
            }
            
            response = await self.http_client.post("/recommendations", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "recommendations": data.get("recommendations", []),
                    "total_count": data.get("total_count", 0),
                    "processing_time": data.get("processing_time", 0),
                    "confidence": data.get("confidence", 0)
                }
            else:
                return {
                    "success": False,
                    "error": f"ML Pipeline API 錯誤: {response.status_code}",
                    "recommendations": []
                }
                
        except Exception as e:
            logger.error(f"ML Pipeline 推薦失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "recommendations": []
            }
    
    async def get_similar_episodes(self, episode_id: int, limit: int = 10) -> Dict[str, Any]:
        """獲取相似節目"""
        if not self.is_initialized or not self.http_client:
            return {
                "success": False,
                "error": "ML Pipeline 服務未初始化",
                "similar_episodes": []
            }
        
        try:
            payload = {
                "episode_id": episode_id,
                "limit": limit
            }
            
            response = await self.http_client.post("/similar-episodes", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "similar_episodes": data.get("similar_episodes", []),
                    "total_count": data.get("total_count", 0)
                }
            else:
                return {
                    "success": False,
                    "error": f"ML Pipeline API 錯誤: {response.status_code}",
                    "similar_episodes": []
                }
                
        except Exception as e:
            logger.error(f"ML Pipeline 相似節目查詢失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "similar_episodes": []
            }
    
    async def update_user_preference(self, 
                                   user_id: str, 
                                   podcast_id: str, 
                                   rating: float, 
                                   listen_time: int = 0) -> Dict[str, Any]:
        """更新用戶偏好"""
        if not self.is_initialized or not self.http_client:
            return {
                "success": False,
                "error": "ML Pipeline 服務未初始化"
            }
        
        try:
            payload = {
                "user_id": user_id,
                "podcast_id": podcast_id,
                "rating": rating,
                "listen_time": listen_time
            }
            
            response = await self.http_client.post("/user-preferences", json=payload)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "用戶偏好更新成功"
                }
            else:
                return {
                    "success": False,
                    "error": f"ML Pipeline API 錯誤: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"ML Pipeline 用戶偏好更新失敗: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        if not self.is_initialized or not self.http_client:
            return {
                "status": "unhealthy",
                "error": "ML Pipeline 服務未初始化",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # 同步健康檢查
            import httpx
            response = httpx.get(f"{self.ml_pipeline_url}/health", timeout=5.0)
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "url": self.ml_pipeline_url,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"健康檢查失敗: {response.status_code}",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_service_info(self) -> Dict[str, Any]:
        """獲取服務資訊"""
        return {
            "module": "ml_pipeline",
            "url": self.ml_pipeline_url,
            "status": "initialized" if self.is_initialized else "uninitialized",
            "description": "Podwise ML Pipeline 推薦服務"
        }


class TTSService:
    """TTS 服務整合器"""
    
    def __init__(self, tts_module_path: str = "../tts", tts_api_url: str = "http://localhost:8002"):
        """
        初始化 TTS 服務
        
        Args:
            tts_module_path: TTS 模組路徑
            tts_api_url: TTS API URL
        """
        self.tts_module_path = tts_module_path
        self.tts_api_url = tts_api_url
        self.tts_service = None
        self.http_client = None
        self.is_initialized = False
        
        logger.info("TTS 服務整合器初始化完成")
    
    async def initialize(self) -> bool:
        """初始化 TTS 服務"""
        try:
            # 嘗試直接導入 TTS 模組
            tts_path = Path(self.tts_module_path).resolve()
            if tts_path.exists():
                sys.path.insert(0, str(tts_path.parent))
                
                try:
                    from tts.core.tts_service import TTSService as LocalTTSService
                    
                    # 初始化本地 TTS 服務
                    self.tts_service = LocalTTSService()
                    self.is_initialized = True
                    
                    logger.info("✅ 本地 TTS 服務初始化成功")
                    return True
                    
                except ImportError as e:
                    logger.warning(f"本地 TTS 模組導入失敗: {e}")
                    
                # 嘗試導入 TTS 配置
                try:
                    from tts.config.voice_config import VoiceConfig
                    self.voice_config = VoiceConfig()
                    logger.info("✅ TTS 語音配置初始化成功")
                except ImportError as e:
                    logger.warning(f"TTS 語音配置導入失敗: {e}")
                    self.voice_config = None
            
            # 如果本地模組不可用，嘗試使用 API
            try:
                self.http_client = httpx.AsyncClient(
                    timeout=30.0,
                    base_url=self.tts_api_url
                )
                
                # 測試連接
                response = await self.http_client.get("/health")
                if response.status_code == 200:
                    self.is_initialized = True
                    logger.info("✅ TTS API 服務初始化成功")
                    return True
                else:
                    logger.warning(f"TTS API 服務健康檢查失敗: {response.status_code}")
                    return False
                    
            except Exception as e:
                logger.warning(f"TTS API 服務初始化失敗: {e}")
                return False
                
        except Exception as e:
            logger.error(f"TTS 服務初始化失敗: {e}")
            return False
    
    async def synthesize_speech(self, 
                              text: str, 
                              voice: str = "podrina", 
                              speed: float = 1.0) -> Optional[Dict[str, Any]]:
        """語音合成"""
        if not self.is_initialized:
            return {
                "success": False,
                "error": "TTS 服務未初始化",
                "audio_data": None
            }
        
        try:
            if self.tts_service:
                # 使用本地 TTS 服務
                rate_param = f"+{(speed-1)*100:.0f}%" if speed != 1.0 else "+0%"
                audio_data = await self.tts_service.synthesize_speech(
                    text=text,
                    voice_id=voice,
                    rate=rate_param
                )
                
                if audio_data:
                    import base64
                    return {
                        "success": True,
                        "audio_data": base64.b64encode(audio_data).decode('utf-8'),
                        "voice_used": voice,
                        "speed_used": speed,
                        "text_length": len(text)
                    }
                else:
                    return {
                        "success": False,
                        "error": "語音合成失敗",
                        "audio_data": None
                    }
            
            elif self.http_client:
                # 使用 TTS API
                payload = {
                    "文字": text,
                    "語音": voice,
                    "語速": f"+{(speed-1)*100:.0f}%" if speed != 1.0 else "+0%"
                }
                
                response = await self.http_client.post("/synthesize", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("成功"):
                        return {
                            "success": True,
                            "audio_data": data.get("音訊檔案"),
                            "voice_used": voice,
                            "speed_used": speed,
                            "text_length": len(text),
                            "processing_time": data.get("處理時間")
                        }
                    else:
                        return {
                            "success": False,
                            "error": data.get("錯誤訊息", "語音合成失敗"),
                            "audio_data": None
                        }
                else:
                    return {
                        "success": False,
                        "error": f"TTS API 錯誤: {response.status_code}",
                        "audio_data": None
                    }
            
            else:
                return {
                    "success": False,
                    "error": "TTS 服務不可用",
                    "audio_data": None
                }
                
        except Exception as e:
            logger.error(f"TTS 語音合成失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "audio_data": None
            }
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """獲取可用語音"""
        if not self.is_initialized:
            return []
        
        try:
            if self.tts_service:
                return self.tts_service.get_available_voices()
            else:
                # 返回預設語音列表
                return [
                    {
                        "id": "podrina",
                        "name": "Podrina",
                        "description": "溫柔親切的女聲"
                    },
                    {
                        "id": "podrisa",
                        "name": "Podrisa",
                        "description": "活潑開朗的女聲"
                    },
                    {
                        "id": "podrino",
                        "name": "Podrino",
                        "description": "穩重可靠的男聲"
                    }
                ]
                
        except Exception as e:
            logger.error(f"獲取語音列表失敗: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        if not self.is_initialized:
            return {
                "status": "unhealthy",
                "error": "TTS 服務未初始化",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            if self.tts_service:
                # 檢查 TTS 服務是否可用
                try:
                    # 嘗試獲取可用語音列表來測試服務
                    voices = self.get_available_voices()
                    is_available = len(voices) > 0
                    return {
                        "status": "healthy" if is_available else "unhealthy",
                        "type": "local",
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception:
                    return {
                        "status": "unhealthy",
                        "type": "local",
                        "error": "TTS 服務檢查失敗",
                        "timestamp": datetime.now().isoformat()
                    }
            elif self.http_client:
                # 同步健康檢查
                import httpx
                response = httpx.get(f"{self.tts_api_url}/health", timeout=5.0)
                
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "type": "api",
                        "url": self.tts_api_url,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"健康檢查失敗: {response.status_code}",
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                return {
                    "status": "unhealthy",
                    "error": "TTS 服務不可用",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_service_info(self) -> Dict[str, Any]:
        """獲取服務資訊"""
        return {
            "module": "tts",
            "type": "local" if self.tts_service else "api" if self.http_client else "none",
            "url": self.tts_api_url if self.http_client else None,
            "status": "initialized" if self.is_initialized else "uninitialized",
            "description": "Podwise TTS 語音合成服務"
        }


class IntegratedServiceManager:
    """整合服務管理器"""
    
    def __init__(self):
        """初始化整合服務管理器"""
        self.llm_service = LLMService()
        self.ml_pipeline_service = MLPipelineService()
        self.tts_service = TTSService() # 新增 TTS 服務實例
        self.is_initialized = False
        
        logger.info("整合服務管理器初始化完成")
    
    async def initialize(self) -> bool:
        """初始化所有服務"""
        try:
            # 初始化 LLM 服務
            llm_success = await self.llm_service.initialize()
            
            # 初始化 ML Pipeline 服務
            ml_pipeline_success = await self.ml_pipeline_service.initialize()

            # 初始化 TTS 服務
            tts_success = await self.tts_service.initialize()
            
            self.is_initialized = llm_success or ml_pipeline_success or tts_success
            
            if self.is_initialized:
                logger.info("✅ 整合服務管理器初始化成功")
            else:
                logger.warning("⚠️ 部分服務初始化失敗")
            
            return self.is_initialized
            
        except Exception as e:
            logger.error(f"整合服務管理器初始化失敗: {e}")
            return False
    
    async def generate_text_with_llm(self, prompt: str, model_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """使用 LLM 生成文字"""
        return await self.llm_service.generate_text(prompt, model_name, **kwargs)
    
    async def get_recommendations_with_ml_pipeline(self, 
                                                 user_id: str, 
                                                 top_k: int = 10, 
                                                 category_filter: Optional[str] = None,
                                                 context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """使用 ML Pipeline 獲取推薦"""
        return await self.ml_pipeline_service.get_recommendations(
            user_id, top_k, category_filter, context
        )
    
    async def get_similar_episodes_with_ml_pipeline(self, episode_id: int, limit: int = 10) -> Dict[str, Any]:
        """使用 ML Pipeline 獲取相似節目"""
        return await self.ml_pipeline_service.get_similar_episodes(episode_id, limit)
    
    async def update_user_preference_with_ml_pipeline(self, 
                                                    user_id: str, 
                                                    podcast_id: str, 
                                                    rating: float, 
                                                    listen_time: int = 0) -> Dict[str, Any]:
        """使用 ML Pipeline 更新用戶偏好"""
        return await self.ml_pipeline_service.update_user_preference(
            user_id, podcast_id, rating, listen_time
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        llm_health = self.llm_service.health_check()
        ml_pipeline_health = self.ml_pipeline_service.health_check()
        tts_health = self.tts_service.health_check() # 新增 TTS 健康檢查
        
        overall_status = "healthy"
        llm_status = llm_health.get("status", "unknown") if isinstance(llm_health, dict) else "unknown"
        ml_status = ml_pipeline_health.get("status", "unknown") if isinstance(ml_pipeline_health, dict) else "unknown"
        tts_status = tts_health.get("status", "unknown") if isinstance(tts_health, dict) else "unknown"
        
        if llm_status == "unhealthy" and ml_status == "unhealthy" and tts_status == "unhealthy":
            overall_status = "unhealthy"
        elif llm_status == "unhealthy" or ml_status == "unhealthy" or tts_status == "unhealthy":
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "llm": llm_health,
            "ml_pipeline": ml_pipeline_health,
            "tts": tts_health, # 新增 TTS 健康檢查結果
            "timestamp": datetime.now().isoformat()
        }
    
    def get_service_info(self) -> Dict[str, Any]:
        """獲取服務資訊"""
        return {
            "llm": self.llm_service.get_service_info(),
            "ml_pipeline": self.ml_pipeline_service.get_service_info(),
            "tts": self.tts_service.get_service_info(), # 新增 TTS 服務資訊
            "overall_status": "initialized" if self.is_initialized else "uninitialized"
        }
    
    async def cleanup(self) -> None:
        """清理資源"""
        try:
            if self.ml_pipeline_service.http_client:
                await self.ml_pipeline_service.http_client.aclose()
            
            logger.info("整合服務管理器清理完成")
            
        except Exception as e:
            logger.error(f"整合服務管理器清理失敗: {e}")


# 全域整合服務管理器實例
integrated_service_manager = IntegratedServiceManager()


def get_integrated_service_manager() -> IntegratedServiceManager:
    """獲取整合服務管理器"""
    return integrated_service_manager


async def initialize_integrated_services() -> bool:
    """初始化整合服務"""
    return await integrated_service_manager.initialize()


async def test_integrated_services():
    """測試整合服務"""
    try:
        logger.info("開始測試整合服務...")
        
        # 初始化服務
        success = await initialize_integrated_services()
        if not success:
            logger.error("整合服務初始化失敗")
            return False
        
        # 測試 LLM 服務
        llm_result = await integrated_service_manager.generate_text_with_llm(
            "你好，這是一個測試。", "qwen_taiwan"
        )
        llm_success = llm_result.get('success', False) if isinstance(llm_result, dict) else False
        logger.info(f"LLM 測試結果: {llm_success}")
        
        # 測試 ML Pipeline 服務
        ml_result = await integrated_service_manager.get_recommendations_with_ml_pipeline(
            "test_user", 5
        )
        ml_success = ml_result.get('success', False) if isinstance(ml_result, dict) else False
        logger.info(f"ML Pipeline 測試結果: {ml_success}")

        # 測試 TTS 服務
        tts_result = await integrated_service_manager.tts_service.synthesize_speech(
            "你好，這是一個測試語音。", "podrina"
        )
        tts_success = tts_result.get('success', False) if isinstance(tts_result, dict) else False
        logger.info(f"TTS 測試結果: {tts_success}")
        
        # 測試健康檢查
        health = await integrated_service_manager.health_check()
        health_status = health.get('status', 'unknown') if isinstance(health, dict) else 'unknown'
        logger.info(f"健康檢查: {health_status}")
        
        logger.info("整合服務測試完成")
        return True
        
    except Exception as e:
        logger.error(f"整合服務測試失敗: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_integrated_services()) 