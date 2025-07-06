#!/usr/bin/env python3
"""
Podwise API 主模組

提供統一的 API 服務入口點。

作者: Podwise Team
版本: 1.0.0
"""

import logging
import sys
from pathlib import Path

# 添加專案路徑
sys.path.append(str(Path(__file__).parent.parent))

from app import app

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_api_server():
    """運行 API 服務器"""
    try:
        import uvicorn
        logger.info("🚀 啟動 Podwise API 服務器...")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except ImportError:
        logger.error("❌ uvicorn 未安裝，無法運行 API 服務器")
        logger.info("💡 請執行: pip install uvicorn[standard]")


def main():
    """主函數"""
    logger.info("📋 Podwise API 模組初始化...")
    run_api_server()


if __name__ == "__main__":
    main() 