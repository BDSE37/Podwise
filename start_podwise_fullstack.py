#!/usr/bin/env python3
"""
Podwise 全棧啟動腳本

啟動前後端所有服務：
1. 後端 RAG Pipeline 服務 (FastAPI)
2. 前端服務 (FastAPI + HTML)
3. TTS 服務
4. 其他微服務

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
from typing import List, Dict, Any
import asyncio
import uvicorn
from multiprocessing import Process, Manager
import threading

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PodwiseServiceManager:
    """Podwise 服務管理器"""
    
    def __init__(self):
        self.processes = {}
        self.manager = Manager()
        self.running = self.manager.Value('b', False)
        
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
    
    def start_tts_service(self, port: int = 8002):
        """啟動 TTS 服務"""
        try:
            logger.info(f"🚀 啟動 TTS 服務 (端口: {port})")
            
            # 切換到 tts 目錄
            tts_dir = Path(__file__).parent / "backend" / "tts"
            os.chdir(tts_dir)
            
            # 啟動 TTS 服務
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
            
            self.processes[f"tts_{port}"] = process
            logger.info(f"✅ TTS 服務已啟動 (PID: {process.pid})")
            
            return process
            
        except Exception as e:
            logger.error(f"❌ 啟動 TTS 服務失敗: {e}")
            return None
    
    def start_stt_service(self, port: int = 8003):
        """啟動 STT 服務"""
        try:
            logger.info(f"🚀 啟動 STT 服務 (端口: {port})")
            
            # 切換到 stt 目錄
            stt_dir = Path(__file__).parent / "backend" / "stt"
            os.chdir(stt_dir)
            
            # 啟動 STT 服務
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
            
            self.processes[f"stt_{port}"] = process
            logger.info(f"✅ STT 服務已啟動 (PID: {process.pid})")
            
            return process
            
        except Exception as e:
            logger.error(f"❌ 啟動 STT 服務失敗: {e}")
            return None
    
    def start_llm_service(self, port: int = 8004):
        """啟動 LLM 服務"""
        try:
            logger.info(f"🚀 啟動 LLM 服務 (端口: {port})")
            
            # 切換到 llm 目錄
            llm_dir = Path(__file__).parent / "backend" / "llm"
            os.chdir(llm_dir)
            
            # 啟動 LLM 服務
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
            
            self.processes[f"llm_{port}"] = process
            logger.info(f"✅ LLM 服務已啟動 (PID: {process.pid})")
            
            return process
            
        except Exception as e:
            logger.error(f"❌ 啟動 LLM 服務失敗: {e}")
            return None
    
    def start_ml_pipeline_service(self, port: int = 8006):
        """啟動 ML Pipeline 服務"""
        try:
            logger.info(f"🚀 啟動 ML Pipeline 服務 (端口: {port})")
            
            # 切換到 ml_pipeline 目錄
            ml_pipeline_dir = Path(__file__).parent / "backend" / "ml_pipeline"
            os.chdir(ml_pipeline_dir)
            
            # 啟動 ML Pipeline 服務
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
            
            self.processes[f"ml_pipeline_{port}"] = process
            logger.info(f"✅ ML Pipeline 服務已啟動 (PID: {process.pid})")
            
            return process
            
        except Exception as e:
            logger.error(f"❌ 啟動 ML Pipeline 服務失敗: {e}")
            return None
    
    def start_unified_api_gateway(self, port: int = 8008):
        """啟動統一 API 網關"""
        try:
            logger.info(f"🚀 啟動統一 API 網關 (端口: {port})")
            
            # 切換到 backend 目錄
            backend_dir = Path(__file__).parent / "backend"
            os.chdir(backend_dir)
            
            # 啟動統一 API 網關
            cmd = [
                sys.executable, "-m", "uvicorn", 
                "unified_api_gateway:app", 
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
            
            self.processes[f"api_gateway_{port}"] = process
            logger.info(f"✅ 統一 API 網關已啟動 (PID: {process.pid})")
            
            return process
            
        except Exception as e:
            logger.error(f"❌ 啟動統一 API 網關失敗: {e}")
            return None
    
    def start_all_services(self):
        """啟動所有服務"""
        logger.info("🚀 開始啟動 Podwise 全棧服務...")
        
        # 啟動順序很重要
        services = [
            ("LLM 服務", self.start_llm_service, 8004),
            ("TTS 服務", self.start_tts_service, 8002),
            ("STT 服務", self.start_stt_service, 8003),
            ("ML Pipeline 服務", self.start_ml_pipeline_service, 8006),
            ("後端 RAG Pipeline 服務", self.start_backend_rag_pipeline, 8005),
            ("統一 API 網關", self.start_unified_api_gateway, 8008),
            ("前端服務", self.start_frontend_service, 8000),
        ]
        
        for service_name, start_func, port in services:
            try:
                process = start_func(port)
                if process:
                    # 等待服務啟動
                    time.sleep(3)
                    logger.info(f"✅ {service_name} 啟動完成")
                else:
                    logger.warning(f"⚠️ {service_name} 啟動失敗")
            except Exception as e:
                logger.error(f"❌ {service_name} 啟動異常: {e}")
        
        self.running.value = True
        logger.info("🎉 所有服務啟動完成！")
        logger.info("📱 前端服務: http://localhost:8000")
        logger.info("🔧 後端 RAG Pipeline: http://localhost:8005")
        logger.info("🎵 TTS 服務: http://localhost:8002")
        logger.info("🎤 STT 服務: http://localhost:8003")
        logger.info("🧠 LLM 服務: http://localhost:8004")
        logger.info("📊 ML Pipeline: http://localhost:8006")
        logger.info("🌐 API 網關: http://localhost:8008")
    
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
        
        self.running.value = False
        logger.info("✅ 所有服務已停止")
    
    def monitor_services(self):
        """監控服務狀態"""
        while self.running.value:
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
    service_manager = PodwiseServiceManager()
    signal_handler.service_manager = service_manager
    
    try:
        # 啟動所有服務
        service_manager.start_all_services()
        
        # 啟動監控線程
        monitor_thread = threading.Thread(target=service_manager.monitor_services)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 主循環
        while service_manager.running.value:
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