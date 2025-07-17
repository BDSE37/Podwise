#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Podwise 統一服務啟動器
整合所有後端服務，提供統一的啟動介面
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

# 添加後端路徑
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from core.podwise_service_manager import podwise_service
from unified_api_gateway import app as api_gateway_app
import uvicorn

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PodwiseServiceLauncher:
    """Podwise 服務啟動器"""
    
    def __init__(self):
        """初始化啟動器"""
        self.services = {
            "api_gateway": {
                "name": "統一 API Gateway",
                "port": 8008,
                "app": api_gateway_app,
                "description": "整合所有功能的統一 API 服務"
            }
        }
        
        self.running_services = {}
    
    def start_service(self, service_name: str) -> bool:
        """啟動指定服務"""
        if service_name not in self.services:
            logger.error(f"未知服務: {service_name}")
            return False
        
        service_config = self.services[service_name]
        
        try:
            logger.info(f"🚀 啟動 {service_config['name']}...")
            
            # 啟動 FastAPI 服務
            uvicorn.run(
                service_config["app"],
                host="0.0.0.0",
                port=service_config["port"],
                reload=False,
                log_level="info"
            )
            
            self.running_services[service_name] = service_config
            logger.info(f"✅ {service_config['name']} 啟動成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ {service_config['name']} 啟動失敗: {e}")
            return False
    
    def start_all_services(self) -> Dict[str, bool]:
        """啟動所有服務"""
        results = {}
        
        logger.info("🎯 開始啟動所有 Podwise 服務...")
        
        for service_name in self.services:
            results[service_name] = self.start_service(service_name)
        
        return results
    
    def list_services(self) -> Dict[str, Dict[str, Any]]:
        """列出所有可用服務"""
        return self.services
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """獲取服務狀態"""
        if service_name not in self.services:
            return {"error": "服務不存在"}
        
        service_config = self.services[service_name]
        is_running = service_name in self.running_services
        
        return {
            "name": service_config["name"],
            "port": service_config["port"],
            "description": service_config["description"],
            "status": "running" if is_running else "stopped",
            "url": f"http://localhost:{service_config['port']}" if is_running else None
        }
    
    def stop_all_services(self):
        """停止所有服務"""
        logger.info("🛑 停止所有服務...")
        self.running_services.clear()
        logger.info("✅ 所有服務已停止")

def main():
    """主函數"""
    launcher = PodwiseServiceLauncher()
    
    # 檢查命令行參數
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            # 列出所有服務
            services = launcher.list_services()
            print("\n📋 可用的 Podwise 服務:")
            print("=" * 50)
            for name, config in services.items():
                print(f"🔧 {name}: {config['name']}")
                print(f"   📝 {config['description']}")
                print(f"   🌐 端口: {config['port']}")
                print()
        
        elif command == "start":
            # 啟動指定服務
            if len(sys.argv) > 2:
                service_name = sys.argv[2]
                success = launcher.start_service(service_name)
                if success:
                    print(f"✅ {service_name} 啟動成功")
                else:
                    print(f"❌ {service_name} 啟動失敗")
            else:
                print("請指定要啟動的服務名稱")
                print("可用服務:", list(launcher.services.keys()))
        
        elif command == "start-all":
            # 啟動所有服務
            results = launcher.start_all_services()
            print("\n📊 服務啟動結果:")
            for service, success in results.items():
                status = "✅ 成功" if success else "❌ 失敗"
                print(f"   {service}: {status}")
        
        elif command == "status":
            # 檢查服務狀態
            if len(sys.argv) > 2:
                service_name = sys.argv[2]
                status = launcher.get_service_status(service_name)
                print(f"\n📊 {service_name} 狀態:")
                for key, value in status.items():
                    print(f"   {key}: {value}")
            else:
                print("請指定要檢查的服務名稱")
        
        else:
            print("未知命令。可用命令:")
            print("  list      - 列出所有服務")
            print("  start     - 啟動指定服務")
            print("  start-all - 啟動所有服務")
            print("  status    - 檢查服務狀態")
    
    else:
        # 預設啟動統一 API Gateway
        print("🚀 啟動 Podwise 統一 API Gateway...")
        print("📝 使用 'python main.py list' 查看所有可用服務")
        print("=" * 50)
        
        success = launcher.start_service("api_gateway")
        if success:
            print("✅ 服務啟動成功")
            print("🌐 訪問地址: http://localhost:8008")
            print("📚 API 文檔: http://localhost:8008/docs")
        else:
            print("❌ 服務啟動失敗")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 收到中斷信號，正在關閉服務...")
        launcher = PodwiseServiceLauncher()
        launcher.stop_all_services()
        print("✅ 服務已關閉")
    except Exception as e:
        logger.error(f"❌ 程式執行錯誤: {e}")
        sys.exit(1) 