#!/usr/bin/env python3
"""
Podwise 穩健啟動腳本

啟動所有服務，確保即使某些服務失敗也會繼續啟動其他服務：
1. 後端 RAG Pipeline 服務 (FastAPI)
2. 前端服務 (FastAPI + HTML)
3. TTS 服務
4. STT 服務
5. LLM 服務
6. ML Pipeline 服務
7. 統一 API 網關

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
import requests
from typing import Dict, Any, Optional

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RobustPodwiseManager:
    """穩健的 Podwise 服務管理器"""
    
    def __init__(self):
        self.processes = {}
        self.running = False
        self.service_status = {}
        
    def check_port_available(self, port: int) -> bool:
        """檢查端口是否可用"""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return True
        except OSError:
            return False
    
    def wait_for_service(self, port: int, timeout: int = 30) -> bool:
        """等待服務啟動"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=2)
                if response.status_code == 200:
                    return True
            except:
                pass
            time.sleep(1)
        return False
    
    def start_service(self, service_name: str, service_func, port: int, timeout: int = 30) -> Optional[subprocess.Popen]:
        """啟動單個服務"""
        try:
            # 檢查端口是否被佔用
            if not self.check_port_available(port):
                logger.warning(f"⚠️ 端口 {port} 已被佔用，嘗試終止現有進程")
                self.kill_process_on_port(port)
                time.sleep(2)
            
            logger.info(f"🚀 啟動 {service_name} (端口: {port})")
            process = service_func(port)
            
            if process:
                # 等待服務啟動
                if self.wait_for_service(port, timeout):
                    logger.info(f"✅ {service_name} 啟動成功 (PID: {process.pid})")
                    self.service_status[service_name] = "running"
                    return process
                else:
                    logger.warning(f"⚠️ {service_name} 啟動超時，但進程仍在運行")
                    self.service_status[service_name] = "timeout"
                    return process
            else:
                logger.error(f"❌ {service_name} 啟動失敗")
                self.service_status[service_name] = "failed"
                return None
                
        except Exception as e:
            logger.error(f"❌ 啟動 {service_name} 時發生錯誤: {e}")
            self.service_status[service_name] = "error"
            return None
    
    def kill_process_on_port(self, port: int):
        """終止佔用指定端口的進程"""
        try:
            cmd = f"lsof -ti:{port} | xargs kill -9"
            subprocess.run(cmd, shell=True, capture_output=True)
        except:
            pass
    
    def start_backend_rag_pipeline(self, port: int = 8005):
        """啟動後端 RAG Pipeline 服務"""
        try:
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
            return process
            
        except Exception as e:
            logger.error(f"❌ 啟動後端 RAG Pipeline 服務失敗: {e}")
            return None
    
    def start_frontend_service(self, port: int = 8000):
        """啟動前端服務"""
        try:
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
            return process
            
        except Exception as e:
            logger.error(f"❌ 啟動前端服務失敗: {e}")
            return None
    
    def start_tts_service(self, port: int = 8002):
        """啟動 TTS 服務"""
        try:
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
            return process
            
        except Exception as e:
            logger.error(f"❌ 啟動 TTS 服務失敗: {e}")
            return None
    
    def start_stt_service(self, port: int = 8003):
        """啟動 STT 服務"""
        try:
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
            return process
            
        except Exception as e:
            logger.error(f"❌ 啟動 STT 服務失敗: {e}")
            return None
    
    def start_llm_service(self, port: int = 8004):
        """啟動 LLM 服務"""
        try:
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
            return process
            
        except Exception as e:
            logger.error(f"❌ 啟動 LLM 服務失敗: {e}")
            return None
    
    def start_ml_pipeline_service(self, port: int = 8006):
        """啟動 ML Pipeline 服務"""
        try:
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
            return process
            
        except Exception as e:
            logger.error(f"❌ 啟動 ML Pipeline 服務失敗: {e}")
            return None
    
    def start_unified_api_gateway(self, port: int = 8008):
        """啟動統一 API 網關"""
        try:
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
            return process
            
        except Exception as e:
            logger.error(f"❌ 啟動統一 API 網關失敗: {e}")
            return None
    
    def start_all_services(self):
        """啟動所有服務"""
        logger.info("🚀 開始啟動 Podwise 所有服務...")
        
        # 定義所有服務及其啟動順序
        services = [
            ("LLM 服務", self.start_llm_service, 8004, 30),
            ("TTS 服務", self.start_tts_service, 8002, 30),
            ("STT 服務", self.start_stt_service, 8003, 30),
            ("ML Pipeline 服務", self.start_ml_pipeline_service, 8006, 30),
            ("後端 RAG Pipeline 服務", self.start_backend_rag_pipeline, 8005, 45),
            ("統一 API 網關", self.start_unified_api_gateway, 8008, 30),
            ("前端服務", self.start_frontend_service, 8000, 30),
        ]
        
        successful_services = 0
        total_services = len(services)
        
        for service_name, start_func, port, timeout in services:
            try:
                process = self.start_service(service_name, start_func, port, timeout)
                if process:
                    successful_services += 1
                    logger.info(f"✅ {service_name} 啟動完成")
                else:
                    logger.warning(f"⚠️ {service_name} 啟動失敗，繼續啟動其他服務")
                
                # 服務間隔
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ {service_name} 啟動異常: {e}")
        
        self.running = True
        
        # 總結啟動結果
        logger.info("🎉 服務啟動完成！")
        logger.info(f"📊 啟動統計: {successful_services}/{total_services} 個服務成功啟動")
        
        # 顯示服務狀態
        self.print_service_status()
        
        # 顯示訪問地址
        self.print_access_urls()
    
    def print_service_status(self):
        """打印服務狀態"""
        logger.info("📊 服務狀態:")
        for service_name, status in self.service_status.items():
            if status == "running":
                logger.info(f"✅ {service_name}: 運行中")
            elif status == "timeout":
                logger.warning(f"⚠️ {service_name}: 啟動超時")
            elif status == "failed":
                logger.error(f"❌ {service_name}: 啟動失敗")
            else:
                logger.error(f"❌ {service_name}: 啟動錯誤")
    
    def print_access_urls(self):
        """打印訪問地址"""
        logger.info("🌐 服務訪問地址:")
        
        urls = [
            ("📱 前端服務", "http://localhost:8000"),
            ("🔧 後端 RAG Pipeline", "http://localhost:8005"),
            ("📖 RAG API 文檔", "http://localhost:8005/docs"),
            ("🎵 TTS 服務", "http://localhost:8002"),
            ("🎤 STT 服務", "http://localhost:8003"),
            ("🧠 LLM 服務", "http://localhost:8004"),
            ("📊 ML Pipeline", "http://localhost:8006"),
            ("🌐 API 網關", "http://localhost:8008"),
        ]
        
        for name, url in urls:
            logger.info(f"   {name}: {url}")
    
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
    service_manager = RobustPodwiseManager()
    signal_handler.service_manager = service_manager
    
    try:
        # 啟動所有服務
        service_manager.start_all_services()
        
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