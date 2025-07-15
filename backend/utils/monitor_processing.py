#!/usr/bin/env python3
"""
處理狀態監控腳本
"""

import json
import time
from pathlib import Path
from datetime import datetime

def check_processing_status():
    """檢查處理狀態"""
    try:
        stage3_path = Path("backend/vector_pipeline/data/stage3_tagging")
        stage4_path = Path("backend/vector_pipeline/data/stage4_embedding_prep")
        
        stage3_count = len(list(stage3_path.rglob("*.json")))
        stage4_count = len(list(stage4_path.rglob("*.json")))
        
        remaining = stage3_count - stage4_count
        progress_percent = (stage4_count / stage3_count * 100) if stage3_count > 0 else 0
        
        # 檢查是否有處理程序在運行
        import subprocess
        result = subprocess.run(['pgrep', '-f', 'batch_process_with_progress'], 
                              capture_output=True, text=True)
        is_running = result.returncode == 0
        
        # 檢查最近的處理時間
        latest_file_time = None
        if stage4_path.exists():
            latest_files = list(stage4_path.rglob("*.json"))
            if latest_files:
                latest_file = max(latest_files, key=lambda f: f.stat().st_mtime)
                latest_file_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "stage3_files": stage3_count,
            "stage4_files": stage4_count,
            "processed": stage4_count,
            "remaining": remaining,
            "progress_percent": round(progress_percent, 1),
            "is_running": is_running,
            "latest_processed": latest_file_time.isoformat() if latest_file_time else None,
            "status": "complete" if remaining == 0 else "running" if is_running else "stopped"
        }
        
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "status": "error"
        }

def main():
    """主函數"""
    print("🔍 Podwise 批次處理狀態監控")
    print("=" * 50)
    
    status = check_processing_status()
    
    if "error" in status:
        print(f"❌ 檢查失敗: {status['error']}")
        return
    
    print(f"📊 處理進度: {status['processed']}/{status['stage3_files']} ({status['progress_percent']}%)")
    print(f"⏳ 剩餘檔案: {status['remaining']}")
    print(f"🔄 處理狀態: {status['status']}")
    print(f"⚡ 程序運行: {'✅ 是' if status['is_running'] else '❌ 否'}")
    
    if status['latest_processed']:
        latest_time = datetime.fromisoformat(status['latest_processed'])
        time_diff = datetime.now() - latest_time
        print(f"🕐 最近處理: {latest_time.strftime('%Y-%m-%d %H:%M:%S')} ({time_diff.total_seconds()/60:.1f} 分鐘前)")
    
    if status['remaining'] > 0 and not status['is_running']:
        print("\n⚠️ 警告: 還有檔案未處理，但程序未運行")
        print("💡 建議執行: python backend/utils/robust_batch_processor.py")
    
    if status['remaining'] == 0:
        print("\n🎉 恭喜！所有檔案處理完成！")

if __name__ == "__main__":
    main() 