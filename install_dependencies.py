#!/usr/bin/env python3
"""
Podwise 依賴安裝腳本

安裝所有必要的 Python 依賴包

作者: Podwise Team
版本: 1.0.0
"""

import subprocess
import sys
import os
import logging
from pathlib import Path

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def install_package(package: str) -> bool:
    """安裝單個包"""
    try:
        logger.info(f"📦 安裝 {package}...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package, "--no-deps"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ {package} 安裝成功")
            return True
        else:
            logger.error(f"❌ {package} 安裝失敗: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ 安裝 {package} 時發生錯誤: {e}")
        return False

def install_from_requirements(requirements_file: str, upgrade: bool = False) -> bool:
    """從 requirements 文件安裝"""
    try:
        logger.info(f"📦 從 {requirements_file} 安裝依賴...")
        
        cmd = [sys.executable, "-m", "pip", "install", "-r", requirements_file]
        if upgrade:
            cmd.append("--upgrade")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ 從 {requirements_file} 安裝成功")
            return True
        else:
            logger.error(f"❌ 從 {requirements_file} 安裝失敗: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ 從 {requirements_file} 安裝時發生錯誤: {e}")
        return False

def install_core_packages() -> bool:
    """安裝核心包（避免版本衝突）"""
    logger.info("📦 安裝核心依賴包...")
    
    core_packages = [
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.20.0",
        "jinja2>=3.0.0",
        "python-multipart>=0.0.5",
        "aiofiles>=23.0.0",
        "httpx>=0.24.0",
        "requests>=2.28.0",
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "pydantic>=2.0.0",
        "python-dotenv>=0.19.0",
        "loguru>=0.6.0",
        "tqdm>=4.60.0",
        "click>=8.0.0",
        "openai>=1.0.0",
        "python-dateutil>=2.8.0",
        "pytz>=2022.0"
    ]
    
    success_count = 0
    for package in core_packages:
        if install_package(package):
            success_count += 1
    
    logger.info(f"📊 核心包安裝統計: {success_count}/{len(core_packages)} 個包安裝成功")
    return success_count >= len(core_packages) * 0.8  # 80% 成功率即可

def install_optional_packages() -> bool:
    """安裝可選包"""
    logger.info("📦 安裝可選依賴包...")
    
    optional_packages = [
        "scikit-learn>=1.0.0",
        "transformers>=4.20.0",
        "torch>=1.12.0",
        "sentence-transformers>=2.0.0",
        "pymilvus>=2.2.0",
        "chromadb>=0.3.0",
        "pydub>=0.25.0",
        "librosa>=0.9.0",
        "soundfile>=0.10.0",
        "psycopg2-binary>=2.9.0",
        "sqlalchemy>=1.4.0"
    ]
    
    success_count = 0
    for package in optional_packages:
        try:
            if install_package(package):
                success_count += 1
        except Exception as e:
            logger.warning(f"⚠️ {package} 安裝失敗（可選）: {e}")
    
    logger.info(f"📊 可選包安裝統計: {success_count}/{len(optional_packages)} 個包安裝成功")
    return True  # 可選包失敗不影響整體

def upgrade_pip():
    """升級 pip"""
    try:
        logger.info("🔄 升級 pip...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ], capture_output=True, text=True)
        logger.info("✅ pip 升級完成")
    except Exception as e:
        logger.warning(f"⚠️ pip 升級失敗: {e}")

def check_python_version():
    """檢查 Python 版本"""
    version = sys.version_info
    logger.info(f"🐍 Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        logger.error("❌ 需要 Python 3.8 或更高版本")
        return False
    
    logger.info("✅ Python 版本符合要求")
    return True

def clean_invalid_distributions():
    """清理無效的分發包"""
    try:
        logger.info("🧹 清理無效的分發包...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "check"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.warning("⚠️ 發現無效的分發包，嘗試修復...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", "--force-reinstall", "--no-deps", "pip"
            ], capture_output=True, text=True)
    except Exception as e:
        logger.warning(f"⚠️ 清理無效分發包失敗: {e}")

def main():
    """主函數"""
    logger.info("🚀 開始安裝 Podwise 依賴...")
    
    # 檢查 Python 版本
    if not check_python_version():
        sys.exit(1)
    
    # 清理無效分發包
    clean_invalid_distributions()
    
    # 升級 pip
    upgrade_pip()
    
    # 嘗試安裝核心依賴
    success = False
    
    # 方法 1: 嘗試核心依賴文件
    if Path("requirements_core.txt").exists():
        logger.info("📄 找到 requirements_core.txt")
        success = install_from_requirements("requirements_core.txt")
    
    # 方法 2: 如果核心依賴失敗，嘗試完整依賴文件
    if not success and Path("requirements_podwise.txt").exists():
        logger.info("📄 嘗試 requirements_podwise.txt")
        success = install_from_requirements("requirements_podwise.txt")
    
    # 方法 3: 如果都失敗，手動安裝核心包
    if not success:
        logger.warning("⚠️ 從 requirements 文件安裝失敗，嘗試手動安裝核心包...")
        success = install_core_packages()
    
    # 安裝可選包
    install_optional_packages()
    
    if success:
        logger.info("🎉 核心依賴安裝完成！")
        logger.info("💡 提示：某些可選包可能安裝失敗，但不影響基本功能")
    else:
        logger.error("❌ 核心依賴安裝失敗")
        logger.info("💡 建議：")
        logger.info("   1. 檢查網絡連接")
        logger.info("   2. 升級 pip: pip install --upgrade pip")
        logger.info("   3. 清理緩存: pip cache purge")
        sys.exit(1)

if __name__ == "__main__":
    main() 