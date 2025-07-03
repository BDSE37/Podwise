# src/core/podri_engine.py (更新版)
import asyncio
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import uuid
from models.voice_profile import VoiceProfile
from models.conversation import Conversation, MessageRole
from backend.tts.providers.tts_manager import TTSManager
from core.llm_manager import LLMManager
from core.audio_handler import AudioHandler
from utils.logging_config import get_logger


logger = get_logger(__name__)

class PodriInterface(ABC):
    """Podri 介面定義"""
    
    @abstractmethod
    async def speak(self, text: str, voice_profile: Optional[VoiceProfile] = None) -> bytes:
        """文字轉語音"""
        pass
    
    @abstractmethod
    async def chat(self, user_input: str, conversation_id: Optional[str] = None) -> tuple[str, bytes]:
        """對話並生成語音"""
        pass
class PodriEngine(PodriInterface):
    """Podri AI 助理引擎 - 整合 Qwen2.5-Taiwan"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化 Podri 引擎"""
        self.config = config or {}
        
        # TTS 配置
        self.tts_manager = TTSManager(config.get('tts', {}))      
        # LLM 配置 - 使用 Qwen2.5-Taiwan
        llm_config = config.get('llm', {})
        self.llm_manager = LLMManager(
            model_size=llm_config.get('model_size', '3b'),
            custom_model=llm_config.get('custom_model')
        )
        
        self.audio_handler = AudioHandler()
        self.current_voice = VoiceProfile.taiwan_female()
        self.conversations: Dict[str, Conversation] = {}     
        # 台灣特色對話預設
        self.taiwan_personas = {
            "friendly": "請保持友善親切的態度，像朋友般對話",
            "professional": "請保持專業但不失親和力，適合商務場合",
            "casual": "請用輕鬆隨性的方式對話，可以適當使用『啦』、『喔』等語助詞",
            "elder": "請用尊敬的語氣，適合與長輩對話"
        }
        
        logger.info("Podri AI 助理引擎初始化完成 (Powered by Qwen2.5-Taiwan)")

    
    async def initialize(self):
        """異步初始化"""
        await self.llm_manager.initialize()
        logger.info("LLM 模型載入完成")
    
    async def speak(self, text: str, voice_profile: Optional[VoiceProfile] = None) -> bytes:
        """將文字轉換為語音"""
        voice = voice_profile or self.current_voice
        
        try:
            # 生成語音
            audio_data = await self.tts_manager.synthesize(text, voice)
            
            if audio_data:
                # 處理音頻
                processed_audio = self.audio_handler.process(audio_data, voice)
                return processed_audio
            else:
                raise Exception("無法生成語音")
                
        except Exception as e:
            logger.error(f"語音生成錯誤: {e}")
            raise
    
    async def chat(self, user_input: str, conversation_id: Optional[str] = None) -> tuple[str, bytes]:
        """
        進行對話並生成語音回應
        
        Args:
            user_input: 用戶輸入
            conversation_id: 對話ID（可選）
            
        Returns:
            (回應文字, 語音數據)
        """
        # 獲取或創建對話
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
            
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = Conversation(id=conversation_id)
        
        conversation = self.conversations[conversation_id]
        
        # 添加用戶訊息
        conversation.add_message(MessageRole.USER, user_input)
        
        try:
            # 生成 AI 回應
            logger.info(f"生成回應: {user_input[:50]}...")
            
            response_text = await self.llm_manager.generate_response(
                prompt=user_input,
                system_prompt=conversation.system_prompt,
                temperature=0.8,
                top_p=0.9
            )
            
            # 添加助理訊息
            conversation.add_message(MessageRole.ASSISTANT, response_text)
            
            # 生成語音
            audio_data = await self.speak(response_text)
            
            return response_text, audio_data
            
        except Exception as e:
            logger.error(f"對話處理錯誤: {e}")
            raise
    
    def get_conversation_history(self, conversation_id: str) -> Optional[Conversation]:
        """獲取對話歷史"""
        return self.conversations.get(conversation_id)
