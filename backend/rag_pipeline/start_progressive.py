#!/usr/bin/env python3
"""
Podwise RAG Pipeline 漸進式整合啟動腳本
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """檢查 Python 版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        logger.error("❌ 需要 Python 3.10 或更高版本")
        return False
    logger.info(f"✅ Python 版本: {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """檢查依賴套件"""
    required_packages = ["fastapi", "uvicorn", "pydantic", "requests"]
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            logger.warning(f"⚠️  缺少套件: {package}")
            return False
    
    logger.info("✅ 核心依賴套件已安裝")
    return True

def setup_environment():
    """設定環境變數"""
    # 設定基本環境變數
    os.environ["PYTHONPATH"] = str(Path(__file__).parent)
    os.environ["ENVIRONMENT"] = "development"
    os.environ["DEBUG"] = "true"
    
    # 設定本地服務配置
    os.environ["OLLAMA_HOST"] = "http://localhost:11434"
    os.environ["OLLAMA_MODEL"] = "qwen2.5:8b"
    
    logger.info("✅ 環境變數設定完成")

def start_application():
    """啟動應用程式"""
    logger.info("🚀 啟動漸進式整合應用程式...")
    logger.info("📖 API 文件: http://localhost:8006/docs")
    logger.info("🔍 健康檢查: http://localhost:8006/health")
    logger.info("🌐 根端點: http://localhost:8006/")
    logger.info("🔧 組件狀態: http://localhost:8006/api/v1/components/status")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.progressive_integration:app", 
            "--host", "0.0.0.0", 
            "--port", "8006",
            "--reload"
        ])
    except KeyboardInterrupt:
        logger.info("🛑 應用程式已停止")
    except Exception as e:
        logger.error(f"❌ 應用程式啟動失敗: {e}")

def main():
    """主函數"""
    logger.info("🎯 開始 Podwise RAG Pipeline 漸進式整合")
    
    # 1. 檢查 Python 版本
    if not check_python_version():
        sys.exit(1)
    
    # 2. 設定環境變數
    setup_environment()
    
    # 3. 檢查依賴套件
    if not check_dependencies():
        logger.error("❌ 缺少必要依賴套件")
        sys.exit(1)
    
    # 4. 啟動應用程式
    start_application()

if __name__ == "__main__":
    main() 