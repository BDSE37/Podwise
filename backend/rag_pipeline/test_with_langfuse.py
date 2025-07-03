#!/usr/bin/env python3
"""
Podwise RAG Pipeline 整合 Langfuse 的本地測試腳本
使用您現有的 Langfuse 配置
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

def install_dependencies():
    """安裝依賴套件"""
    logger.info("📦 安裝依賴套件...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        logger.info("✅ 依賴套件安裝完成")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 依賴套件安裝失敗: {e}")
        return False

def check_dependencies():
    """檢查依賴套件"""
    required_packages = ["fastapi", "uvicorn", "pydantic", "langfuse"]
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            logger.warning(f"⚠️  缺少套件: {package}")
            return False
    
    logger.info("✅ 核心依賴套件已安裝")
    return True

def setup_environment():
    """設定環境變數，整合現有的 Langfuse 配置"""
    # 設定基本環境變數
    os.environ["PYTHONPATH"] = str(Path(__file__).parent)
    os.environ["ENVIRONMENT"] = "development"
    os.environ["DEBUG"] = "true"
    
    # 設定本地服務配置
    os.environ["MONGODB_URI"] = "mongodb://localhost:27017/podwise_test"
    os.environ["POSTGRES_HOST"] = "localhost"
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["MILVUS_HOST"] = "localhost"
    os.environ["OLLAMA_HOST"] = "http://localhost:11434"
    
    # 整合現有的 Langfuse 配置
    # 檢查是否有現有的 Langfuse 配置
    langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    
    if langfuse_public_key and langfuse_secret_key:
        logger.info("✅ 發現現有的 Langfuse 配置")
        logger.info(f"🔑 Langfuse Host: {os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')}")
        os.environ["LANGFUSE_ENABLED"] = "true"
    else:
        logger.info("ℹ️  Langfuse API Key 未設定，追蹤功能將停用")
        os.environ["LANGFUSE_ENABLED"] = "false"
    
    logger.info("✅ 環境變數設定完成")

def test_langfuse_connection():
    """測試 Langfuse 連接"""
    try:
        # 導入您的 Langfuse 客戶端
        sys.path.append(str(Path(__file__).parent.parent))
        from utils.langfuse_client import langfuse
        
        # 測試連接
        trace = langfuse.trace(
            name="test_connection",
            metadata={"test": True}
        )
        trace.update(metadata={"status": "connected"})
        logger.info("✅ Langfuse 連接測試成功")
        return True
    except Exception as e:
        logger.warning(f"⚠️  Langfuse 連接測試失敗: {e}")
        return False

def check_services():
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

def start_application():
    """啟動應用程式"""
    logger.info("🚀 啟動 RAG Pipeline 應用程式...")
    logger.info("📖 API 文件: http://localhost:8004/docs")
    logger.info("🔍 健康檢查: http://localhost:8004/health")
    logger.info("📊 Langfuse 追蹤: https://cloud.langfuse.com")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main_integrated:app", 
            "--host", "0.0.0.0", 
            "--port", "8004",
            "--reload"
        ])
    except KeyboardInterrupt:
        logger.info("🛑 應用程式已停止")
    except Exception as e:
        logger.error(f"❌ 應用程式啟動失敗: {e}")

def main():
    """主函數"""
    logger.info("🎯 開始 Podwise RAG Pipeline 本地測試 (整合 Langfuse)")
    
    # 1. 檢查 Python 版本
    if not check_python_version():
        sys.exit(1)
    
    # 2. 設定環境變數
    setup_environment()
    
    # 3. 檢查依賴套件
    if not check_dependencies():
        logger.info("📦 嘗試安裝依賴套件...")
        if not install_dependencies():
            sys.exit(1)
    
    # 4. 檢查外部服務
    check_services()
    
    # 5. 測試 Langfuse 連接
    test_langfuse_connection()
    
    # 6. 啟動應用程式
    start_application()

if __name__ == "__main__":
    main() 