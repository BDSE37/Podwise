#!/usr/bin/env python3
"""
確保處理持續進行的腳本
"""

import subprocess
import time
import os
from pathlib import Path

def check_if_processing():
    """檢查是否有處理程序在運行"""
    try:
        result = subprocess.run(['pgrep', '-f', 'batch_process_with_progress'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def start_processing():
    """啟動處理程序"""
    try:
        # 切換到正確的目錄
        os.chdir('/home/bai/Desktop/Podwise/backend')
        
        # 啟動處理程序
        subprocess.Popen([
            '/home/bai/Desktop/Podwise/.venv/bin/python',
            'utils/batch_process_with_progress.py'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("✅ 處理程序已啟動")
        return True
    except Exception as e:
        print(f"❌ 啟動處理程序失敗: {e}")
        return False

def main():
    """主函數"""
    print("🔍 檢查處理狀態...")
    
    if check_if_processing():
        print("✅ 處理程序正在運行")
    else:
        print("❌ 沒有處理程序在運行，正在啟動...")
        start_processing()
    
    # 顯示進度
    stage3_count = len(list(Path("backend/vector_pipeline/data/stage3_tagging").rglob("*.json")))
    stage4_count = len(list(Path("backend/vector_pipeline/data/stage4_embedding_prep").rglob("*.json")))
    
    print(f"📊 進度: {stage4_count}/{stage3_count} ({stage4_count/stage3_count*100:.1f}%)")
    print(f"⏳ 剩餘: {stage3_count - stage4_count} 個檔案")

if __name__ == "__main__":
    main() 