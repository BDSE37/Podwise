#!/usr/bin/env python3
"""
強健的批次處理腳本
- 自動重啟機制
- 錯誤恢復功能
- 持續運行保證
- 進度保存和恢復
"""

import os
import json
import sys
import time
import signal
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 載入環境變數
load_dotenv('backend/.env')

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
            logging.FileHandler('utils/batch_processing.log'),
            logging.StreamHandler()
        ]
)
logger = logging.getLogger(__name__)

class RobustBatchProcessor:
    """強健的批次處理器 - 包含自動重啟和錯誤恢復"""
    
    def __init__(self):
        """初始化強健批次處理器"""
        self.script_path = "backend/utils/batch_process_with_progress.py"
        self.max_restarts = 10
        self.restart_delay = 30  # 秒
        self.process = None
        self.restart_count = 0
        self.start_time = time.time()
        
        # 設定信號處理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("🚀 強健批次處理器初始化完成")
    
    def _signal_handler(self, signum, frame):
        """信號處理器"""
        logger.info(f"收到信號 {signum}，正在優雅關閉...")
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
        sys.exit(0)
    
    def check_processing_status(self) -> Dict[str, Any]:
        """檢查處理狀態"""
        try:
            stage3_count = len(list(Path("backend/vector_pipeline/data/stage3_tagging").rglob("*.json")))
            stage4_count = len(list(Path("backend/vector_pipeline/data/stage4_embedding_prep").rglob("*.json")))
            
            return {
                "stage3_files": stage3_count,
                "stage4_files": stage4_count,
                "processed": stage4_count,
                "remaining": stage3_count - stage4_count,
                "progress_percent": (stage4_count / stage3_count * 100) if stage3_count > 0 else 0
            }
        except Exception as e:
            logger.error(f"檢查狀態失敗: {e}")
            return {"error": str(e)}
    
    def is_processing_complete(self) -> bool:
        """檢查處理是否完成"""
        status = self.check_processing_status()
        if "error" in status:
            return False
        
        return status["remaining"] == 0
    
    def start_processing(self) -> bool:
        """啟動處理程序"""
        try:
            logger.info(f"🔄 啟動批次處理 (第 {self.restart_count + 1} 次)")
            
            # 啟動子程序
            self.process = subprocess.Popen(
                [sys.executable, self.script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            logger.info(f"✅ 處理程序已啟動 (PID: {self.process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"❌ 啟動處理程序失敗: {e}")
            return False
    
    def monitor_process(self) -> bool:
        """監控處理程序"""
        if not self.process:
            return False
        
        try:
            # 檢查進度
            status = self.check_processing_status()
            logger.info(f"📊 處理進度: {status['processed']}/{status['stage3_files']} ({status['progress_percent']:.1f}%)")
            
            # 檢查程序是否還在運行
            if self.process.poll() is None:
                return True  # 程序還在運行
            else:
                # 程序已結束
                return_code = self.process.returncode
                stdout, stderr = self.process.communicate()
                
                if return_code == 0:
                    logger.info("✅ 處理程序正常完成")
                    return False
                else:
                    logger.error(f"❌ 處理程序異常結束 (返回碼: {return_code})")
                    if stderr:
                        logger.error(f"錯誤輸出: {stderr}")
                    return False
                    
        except Exception as e:
            logger.error(f"監控程序失敗: {e}")
            return False
    
    def restart_if_needed(self) -> bool:
        """如果需要則重啟處理"""
        if self.restart_count >= self.max_restarts:
            logger.error(f"❌ 已達到最大重啟次數 ({self.max_restarts})")
            return False
        
        if self.is_processing_complete():
            logger.info("🎉 所有檔案處理完成！")
            return False
        
        logger.info(f"⏳ 等待 {self.restart_delay} 秒後重啟...")
        time.sleep(self.restart_delay)
        
        self.restart_count += 1
        return self.start_processing()
    
    def run_continuously(self):
        """持續運行處理"""
        logger.info("🚀 開始持續批次處理")
        
        while True:
            try:
                # 檢查是否已完成
                if self.is_processing_complete():
                    logger.info("🎉 所有檔案處理完成！")
                    break
                
                # 啟動處理
                if not self.start_processing():
                    logger.error("❌ 無法啟動處理程序")
                    break
                
                # 監控處理
                while self.monitor_process():
                    time.sleep(60)  # 每分鐘檢查一次
                
                # 檢查是否需要重啟
                if not self.restart_if_needed():
                    break
                    
            except KeyboardInterrupt:
                logger.info("收到中斷信號，正在關閉...")
                break
            except Exception as e:
                logger.error(f"運行時發生錯誤: {e}")
                if not self.restart_if_needed():
                    break
        
        # 最終狀態報告
        final_status = self.check_processing_status()
        logger.info("📊 最終處理狀態:")
        logger.info(f"   總檔案數: {final_status.get('stage3_files', 0)}")
        logger.info(f"   已處理: {final_status.get('processed', 0)}")
        logger.info(f"   剩餘: {final_status.get('remaining', 0)}")
        logger.info(f"   完成率: {final_status.get('progress_percent', 0):.1f}%")
        
        total_time = time.time() - self.start_time
        logger.info(f"⏱️ 總運行時間: {timedelta(seconds=int(total_time))}")
        logger.info(f"🔄 重啟次數: {self.restart_count}")


def main():
    """主函數"""
    processor = RobustBatchProcessor()
    processor.run_continuously()


if __name__ == "__main__":
    main() 