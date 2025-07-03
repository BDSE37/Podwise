"""
配置管理器模組
負責管理應用程式的配置設定
"""

import os
import json
import yaml
from typing import Any, Dict, Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """配置管理器類 - 單例模式"""
    
    _instance = None
    
    def __new__(cls):
        """確保單例模式"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置管理器"""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._config = {}
        self._config_dir = self._get_config_dir()
        self._config_file = os.path.join(self._config_dir, "config.yaml")
        
        # 載入預設配置
        self._load_default_config()
        # 載入用戶配置
        self._load_user_config()
        
        logger.info("配置管理器初始化完成")
    
    def _get_config_dir(self) -> str:
        """獲取配置目錄路徑
        
        Returns:
            str: 配置目錄路徑
        """
        # 使用用戶主目錄下的 .podwise 資料夾
        home_dir = os.path.expanduser("~")
        config_dir = os.path.join(home_dir, ".podwise", "config")
        os.makedirs(config_dir, exist_ok=True)
        return config_dir
    
    def _load_default_config(self):
        """載入預設配置"""
        self._config = {
            "系統設定": {
                "語言": "zh-TW",
                "時區": "Asia/Taipei",
                "日誌等級": "INFO"
            },
            "音訊設定": {
                "輸入採樣率": 16000,
                "輸出採樣率": 24000,
                "聲道數": 1,
                "音訊格式": "wav"
            },
            "網路設定": {
                "WebSocket端口": 8002,
                "HTTP端口": 8003,
                "主機地址": "0.0.0.0"
            },
            "TTS設定": {
                "預設語音": "podri",
                "語速": 1.0,
                "音調": 1.0,
                "音量": 1.0
            },
            "GPT_SoVITS設定": {
                "模型路徑": "/app/GPT-SoVITS/models",
                "預訓練模型路徑": "/app/GPT-SoVITS/pretrained_models",
                "文本處理路徑": "/app/GPT-SoVITS/text"
            }
        }
    
    def _load_user_config(self):
        """載入用戶配置"""
        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        self._merge_config(self._config, user_config)
                logger.info("用戶配置載入成功")
            except Exception as e:
                logger.error(f"載入用戶配置失敗: {e}")
    
    def _merge_config(self, base_config: Dict, user_config: Dict):
        """合併配置
        
        Args:
            base_config: 基礎配置
            user_config: 用戶配置
        """
        for key, value in user_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._merge_config(base_config[key], value)
            else:
                base_config[key] = value
    
    def save_config(self):
        """儲存配置到檔案"""
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            logger.info("配置儲存成功")
        except Exception as e:
            logger.error(f"儲存配置失敗: {e}")
    
    def get_config(self, key_path: str, default: Any = None) -> Any:
        """獲取配置值
        
        Args:
            key_path: 配置鍵路徑，使用點號分隔，如 "系統設定.語言"
            default: 預設值
            
        Returns:
            Any: 配置值
        """
        keys = key_path.split('.')
        current = self._config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def set_config(self, key_path: str, value: Any):
        """設定配置值
        
        Args:
            key_path: 配置鍵路徑
            value: 配置值
        """
        keys = key_path.split('.')
        current = self._config
        
        # 遍歷到最後一個鍵的父級
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # 設定最後一個鍵的值
        current[keys[-1]] = value
        logger.debug(f"設定配置: {key_path} = {value}")
    
    def get_config_dir(self) -> str:
        """獲取配置目錄
        
        Returns:
            str: 配置目錄路徑
        """
        return self._config_dir
    
    def get_all_config(self) -> Dict[str, Any]:
        """獲取所有配置
        
        Returns:
            Dict[str, Any]: 所有配置
        """
        return self._config.copy()
    
    def reset_config(self):
        """重置為預設配置"""
        self._load_default_config()
        self.save_config()
        logger.info("配置已重置為預設值")
    
    @classmethod
    def get_instance(cls):
        """獲取單例實例
        
        Returns:
            ConfigManager: 配置管理器實例
        """
        if cls._instance is None:
            cls._instance = ConfigManager()
        return cls._instance
