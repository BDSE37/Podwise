"""
設備激活器模組
負責處理設備的激活和授權功能
"""

import os
import json
import hashlib
import requests
from typing import Optional, Dict, Any
from utils.logging_config import get_logger

logger = get_logger(__name__)


class DeviceActivator:
    """設備激活器類"""
    
    def __init__(self, config_manager):
        """初始化設備激活器
        
        Args:
            config_manager: 配置管理器實例
        """
        self.config_manager = config_manager
        self.activation_file = os.path.join(
            self.config_manager.get_config_dir(), 
            "device_activation.json"
        )
        self.activation_data = self._load_activation_data()
    
    def _load_activation_data(self) -> Dict[str, Any]:
        """載入激活資料
        
        Returns:
            Dict[str, Any]: 激活資料字典
        """
        if os.path.exists(self.activation_file):
            try:
                with open(self.activation_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"載入激活資料失敗: {e}")
                return {}
        return {}
    
    def _save_activation_data(self):
        """儲存激活資料"""
        try:
            os.makedirs(os.path.dirname(self.activation_file), exist_ok=True)
            with open(self.activation_file, 'w', encoding='utf-8') as f:
                json.dump(self.activation_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"儲存激活資料失敗: {e}")
    
    def get_device_id(self) -> str:
        """獲取設備唯一識別碼
        
        Returns:
            str: 設備ID
        """
        # 這裡應該實現真正的設備ID生成邏輯
        # 目前使用簡單的實現
        import platform
        import uuid
        
        system_info = f"{platform.system()}-{platform.machine()}-{platform.node()}"
        device_hash = hashlib.md5(system_info.encode()).hexdigest()
        return device_hash
    
    def is_activated(self) -> bool:
        """檢查設備是否已激活
        
        Returns:
            bool: 是否已激活
        """
        if not self.activation_data:
            return False
        
        # 檢查激活狀態
        activated = self.activation_data.get('activated', False)
        device_id = self.activation_data.get('device_id')
        
        if not activated or not device_id:
            return False
        
        # 驗證設備ID
        current_device_id = self.get_device_id()
        if device_id != current_device_id:
            logger.warning("設備ID不匹配，需要重新激活")
            return False
        
        return True
    
    def process_activation(self, activation_code: str) -> bool:
        """處理設備激活
        
        Args:
            activation_code (str): 激活碼
            
        Returns:
            bool: 激活是否成功
        """
        try:
            # 這裡應該實現真正的激活驗證邏輯
            # 目前使用簡單的實現
            if not activation_code or len(activation_code) < 8:
                logger.error("激活碼格式無效")
                return False
            
            # 模擬激活驗證
            device_id = self.get_device_id()
            self.activation_data = {
                'activated': True,
                'device_id': device_id,
                'activation_code': activation_code,
                'activation_time': self._get_current_timestamp()
            }
            
            self._save_activation_data()
            logger.info("設備激活成功")
            return True
            
        except Exception as e:
            logger.error(f"激活處理失敗: {e}")
            return False
    
    def _get_current_timestamp(self) -> str:
        """獲取當前時間戳
        
        Returns:
            str: 時間戳字串
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def deactivate(self):
        """取消激活"""
        try:
            if os.path.exists(self.activation_file):
                os.remove(self.activation_file)
            self.activation_data = {}
            logger.info("設備已取消激活")
        except Exception as e:
            logger.error(f"取消激活失敗: {e}")
    
    def get_activation_info(self) -> Dict[str, Any]:
        """獲取激活資訊
        
        Returns:
            Dict[str, Any]: 激活資訊字典
        """
        return self.activation_data.copy() 