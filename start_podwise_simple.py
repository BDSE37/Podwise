#!/usr/bin/env python3
"""
Podwise 簡化啟動腳本

快速啟動核心服務：
1. 後端 RAG Pipeline 服務 (FastAPI)
2. 前端服務 (FastAPI + HTML)

作者: Podwise Team
版本: 1.0.0
"""

import os
import sys
import subprocess
import time
import signal
import logging
from pathlib import Path
import threading

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimplePodwiseManager:
    """簡化 Podwise 服務管理器"""
    
    def __init__(self):
        self.processes = {}
        self.running = False
        
    def start_backend_rag_pipeline(self, port: int = 8005):
        """啟動後端 RAG Pipeline 服務"""
        try:
            logger.info(f"🚀 啟動後端 RAG Pipeline 服務 (端口: {port})")
            
            # 切換到 rag_pipeline 目錄
            rag_pipeline_dir = Path(__file__).parent / "backend" / "rag_pipeline"
            os.chdir(rag_pipeline_dir)
            
            # 啟動 RAG Pipeline 服務
            cmd = [
                sys.executable, "-m", "uvicorn", 
                "main:app", 
                "--host", "0.0.0.0", 
                "--port", str(port),
                "--reload",
                "--log-level", "info"
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes[f"rag_pipeline_{port}"] = process
            logger.info(f"✅ 後端 RAG Pipeline 服務已啟動 (PID: {process.pid})")
            
            return process
            
        except Exception as e:
            logger.error(f"❌ 啟動後端 RAG Pipeline 服務失敗: {e}")
            return None
    
    def start_frontend_service(self, port: int = 8000):
        """啟動前端服務"""
        try:
            logger.info(f"🚀 啟動前端服務 (端口: {port})")
            
            # 切換到 frontend 目錄
            frontend_dir = Path(__file__).parent / "frontend"
            os.chdir(frontend_dir)
            
            # 啟動前端服務
            cmd = [
                sys.executable, "-m", "uvicorn", 
                "fastapi_app:app", 
                "--host", "0.0.0.0", 
                "--port", str(port),
                "--reload",
                "--log-level", "info"
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes[f"frontend_{port}"] = process
            logger.info(f"✅ 前端服務已啟動 (PID: {process.pid})")
            
            return process
            
        except Exception as e:
            logger.error(f"❌ 啟動前端服務失敗: {e}")
            return None
    
    def start_core_services(self):
        """啟動核心服務"""
        logger.info("🚀 開始啟動 Podwise 核心服務...")
        
        # 先啟動後端
        backend_process = self.start_backend_rag_pipeline(8005)
        if backend_process:
            time.sleep(5)  # 等待後端啟動
            logger.info("✅ 後端服務啟動完成")
        
        # 再啟動前端
        frontend_process = self.start_frontend_service(8000)
        if frontend_process:
            time.sleep(3)  # 等待前端啟動
            logger.info("✅ 前端服務啟動完成")
        
        self.running = True
        logger.info("🎉 核心服務啟動完成！")
        logger.info("📱 前端服務: http://localhost:8000")
        logger.info("🔧 後端 RAG Pipeline: http://localhost:8005")
        logger.info("📖 API 文檔: http://localhost:8005/docs")
    
    def stop_all_services(self):
        """停止所有服務"""
        logger.info("🛑 正在停止所有服務...")
        
        for name, process in self.processes.items():
            try:
                if process and process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
                    logger.info(f"✅ {name} 已停止")
                else:
                    logger.info(f"ℹ️ {name} 已經停止")
            except Exception as e:
                logger.error(f"❌ 停止 {name} 失敗: {e}")
                try:
                    process.kill()
                except:
                    pass
        
        self.running = False
        logger.info("✅ 所有服務已停止")
    
    def monitor_services(self):
        """監控服務狀態"""
        while self.running:
            try:
                for name, process in self.processes.items():
                    if process and process.poll() is not None:
                        logger.warning(f"⚠️ {name} 已停止運行")
                
                time.sleep(10)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"監控服務時發生錯誤: {e}")
    
    def print_status(self):
        """打印服務狀態"""
        logger.info("📊 服務狀態:")
        for name, process in self.processes.items():
            if process and process.poll() is None:
                logger.info(f"✅ {name}: 運行中 (PID: {process.pid})")
            else:
                logger.info(f"❌ {name}: 已停止")


def signal_handler(signum, frame):
    """信號處理器"""
    logger.info(f"收到信號 {signum}，正在停止服務...")
    if hasattr(signal_handler, 'service_manager'):
        signal_handler.service_manager.stop_all_services()
    sys.exit(0)


def main():
    """主函數"""
    # 註冊信號處理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 創建服務管理器
    service_manager = SimplePodwiseManager()
    signal_handler.service_manager = service_manager
    
    try:
        # 啟動核心服務
        service_manager.start_core_services()
        
        # 啟動監控線程
        monitor_thread = threading.Thread(target=service_manager.monitor_services)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 主循環
        while service_manager.running:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break
        
    except KeyboardInterrupt:
        logger.info("收到中斷信號")
    except Exception as e:
        logger.error(f"運行時發生錯誤: {e}")
    finally:
        service_manager.stop_all_services()


if __name__ == "__main__":
    main() 