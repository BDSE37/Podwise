#!/usr/bin/env python3
"""
Ollama 服務啟動腳本

自動啟動 Ollama 服務並載入指定模型
作者: Podwise Team
版本: 1.0.0
"""

import subprocess
import time
import logging
import requests
from typing import Optional, List

logger = logging.getLogger(__name__)


class OllamaServiceManager:
    """Ollama 服務管理器"""
    
    def __init__(self, models: Optional[List[str]] = None):
        # 預設載入兩個模型
        self.models = models or [
            "benchang1110/Qwen2.5-Taiwan-7B-Instruct",
            "Qwen/Qwen3-8B"
        ]
        self.ollama_url = "http://localhost:11434"
        self.is_running = False
    
    def start_ollama_service(self) -> bool:
        """啟動 Ollama 服務"""
        try:
            # 檢查 Ollama 是否已在運行
            if self._check_ollama_running():
                logger.info("✅ Ollama 服務已在運行")
                self.is_running = True
                return True
            
            # 啟動 Ollama 服務
            logger.info("🚀 啟動 Ollama 服務...")
            subprocess.Popen(["ollama", "serve"], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            # 等待服務啟動
            for i in range(30):  # 最多等待 30 秒
                time.sleep(1)
                if self._check_ollama_running():
                    logger.info("✅ Ollama 服務啟動成功")
                    self.is_running = True
                    return True
            
            logger.error("❌ Ollama 服務啟動超時")
            return False
            
        except Exception as e:
            logger.error(f"❌ 啟動 Ollama 服務失敗: {e}")
            return False
    
    def load_model(self) -> bool:
        """載入指定模型"""
        try:
            if not self.is_running:
                logger.error("❌ Ollama 服務未運行")
                return False
            
            logger.info(f"📥 載入模型: {self.models}")
            
            # 使用 ollama pull 載入模型
            for model_name in self.models:
                result = subprocess.run(
                    ["ollama", "pull", model_name],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分鐘超時
                )
                
                if result.returncode == 0:
                    logger.info(f"✅ 模型 {model_name} 載入成功")
                else:
                    logger.error(f"❌ 模型載入失敗: {result.stderr}")
                    return False
            return True
                
        except subprocess.TimeoutExpired:
            logger.error("❌ 模型載入超時")
            return False
        except Exception as e:
            logger.error(f"❌ 載入模型失敗: {e}")
            return False
    
    def test_model(self) -> bool:
        """測試模型是否可用"""
        try:
            if not self.is_running:
                return False
            
            # 發送簡單的測試請求
            test_data = {
                "model": self.models[0], # 測試第一個模型
                "prompt": "你好",
                "stream": False
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info("✅ 模型測試成功")
                return True
            else:
                logger.error(f"❌ 模型測試失敗: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 模型測試失敗: {e}")
            return False
    
    def _check_ollama_running(self) -> bool:
        """檢查 Ollama 是否在運行"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_available_models(self) -> list:
        """獲取可用模型列表"""
        try:
            if not self._check_ollama_running():
                return []
            
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            else:
                return []
                
        except Exception as e:
            logger.error(f"獲取模型列表失敗: {e}")
            return []
    
    def stop_service(self):
        """停止 Ollama 服務"""
        try:
            subprocess.run(["pkill", "ollama"], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
            logger.info("🛑 Ollama 服務已停止")
            self.is_running = False
        except Exception as e:
            logger.error(f"停止 Ollama 服務失敗: {e}")


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ollama 服務管理器")
    parser.add_argument("--models", nargs="+", 
                       default=["benchang1110/Qwen2.5-Taiwan-7B-Instruct", "Qwen/Qwen3-8B"],
                       help="要載入的模型名稱列表")
    parser.add_argument("--action", choices=["start", "stop", "test"], 
                       default="start", help="執行動作")
    
    args = parser.parse_args()
    
    # 設定日誌
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    manager = OllamaServiceManager(args.models)
    
    if args.action == "start":
        # 啟動服務
        if manager.start_ollama_service():
            # 載入模型
            if manager.load_model():
                # 測試模型
                if manager.test_model():
                    logger.info("🎉 Ollama 服務完全就緒！")
                else:
                    logger.error("❌ 模型測試失敗")
            else:
                logger.error("❌ 模型載入失敗")
        else:
            logger.error("❌ 服務啟動失敗")
    
    elif args.action == "stop":
        manager.stop_service()
    
    elif args.action == "test":
        if manager._check_ollama_running():
            models = manager.get_available_models()
            logger.info(f"可用模型: {models}")
            if manager.test_model():
                logger.info("✅ 服務測試成功")
            else:
                logger.error("❌ 服務測試失敗")
        else:
            logger.error("❌ Ollama 服務未運行")


if __name__ == "__main__":
    main() 