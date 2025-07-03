#!/usr/bin/env python3
"""
Podwise RAG Pipeline 本地測試啟動腳本
用於在本地環境中測試 RAG Pipeline 功能
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LocalTestRunner:
    """本地測試執行器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / "env.local"
        
    def check_python_version(self):
        """檢查 Python 版本"""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 10):
            logger.error("❌ 需要 Python 3.10 或更高版本")
            return False
        logger.info(f"✅ Python 版本: {version.major}.{version.minor}.{version.micro}")
        return True
    
    def check_dependencies(self):
        """檢查依賴套件"""
        try:
            import fastapi
            import uvicorn
            import pydantic
            import langchain
            import crewai
            logger.info("✅ 核心依賴套件已安裝")
            return True
        except ImportError as e:
            logger.error(f"❌ 缺少依賴套件: {e}")
            return False
    
    def install_dependencies(self):
        """安裝依賴套件"""
        logger.info("📦 安裝依賴套件...")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], check=True, cwd=self.project_root)
            logger.info("✅ 依賴套件安裝完成")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 依賴套件安裝失敗: {e}")
            return False
    
    def setup_environment(self):
        """設定環境變數"""
        if self.env_file.exists():
            logger.info("📝 載入環境變數...")
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
            logger.info("✅ 環境變數載入完成")
        else:
            logger.warning("⚠️  環境變數檔案不存在，使用預設配置")
    
    def check_services(self):
        """檢查外部服務連接"""
        services = {
            "MongoDB": ("localhost", 27017),
            "PostgreSQL": ("localhost", 5432),
            "Redis": ("localhost", 6379),
            "Milvus": ("localhost", 19530),
            "Ollama": ("localhost", 11434)
        }
        
        logger.info("🔍 檢查外部服務連接...")
        for service_name, (host, port) in services.items():
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((host, port))
                sock.close()
                
                if result == 0:
                    logger.info(f"✅ {service_name} ({host}:{port}) - 可連接")
                else:
                    logger.warning(f"⚠️  {service_name} ({host}:{port}) - 無法連接")
            except Exception as e:
                logger.warning(f"⚠️  {service_name} 檢查失敗: {e}")
    
    def run_tests(self):
        """執行測試"""
        logger.info("🧪 執行單元測試...")
        try:
            subprocess.run([
                sys.executable, "-m", "pytest", "tests/", "-v"
            ], check=True, cwd=self.project_root)
            logger.info("✅ 測試通過")
            return True
        except subprocess.CalledProcessError:
            logger.warning("⚠️  測試失敗或測試檔案不存在")
            return False
        except FileNotFoundError:
            logger.info("ℹ️  測試目錄不存在，跳過測試")
            return True
    
    def start_application(self):
        """啟動應用程式"""
        logger.info("🚀 啟動 RAG Pipeline 應用程式...")
        try:
            # 設定環境變數
            os.environ["PYTHONPATH"] = str(self.project_root)
            
            # 啟動 FastAPI 應用
            subprocess.run([
                sys.executable, "-m", "uvicorn", 
                "app.main_integrated:app", 
                "--host", "0.0.0.0", 
                "--port", "8004",
                "--reload"
            ], cwd=self.project_root)
        except KeyboardInterrupt:
            logger.info("🛑 應用程式已停止")
        except Exception as e:
            logger.error(f"❌ 應用程式啟動失敗: {e}")
    
    def run(self):
        """執行完整的本地測試流程"""
        logger.info("🎯 開始 Podwise RAG Pipeline 本地測試")
        
        # 1. 檢查 Python 版本
        if not self.check_python_version():
            return False
        
        # 2. 設定環境變數
        self.setup_environment()
        
        # 3. 檢查依賴套件
        if not self.check_dependencies():
            logger.info("📦 嘗試安裝依賴套件...")
            if not self.install_dependencies():
                return False
        
        # 4. 檢查外部服務
        self.check_services()
        
        # 5. 執行測試
        self.run_tests()
        
        # 6. 啟動應用程式
        self.start_application()
        
        return True

def main():
    """主函數"""
    runner = LocalTestRunner()
    success = runner.run()
    
    if success:
        logger.info("✅ 本地測試流程完成")
    else:
        logger.error("❌ 本地測試流程失敗")
        sys.exit(1)

if __name__ == "__main__":
    main() 