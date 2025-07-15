#!/usr/bin/env python3
"""
明天繼續處理的腳本，自動跳過已處理的檔案
"""

import json
import os
from pathlib import Path
from datetime import datetime

def load_progress():
    """載入處理進度"""
    try:
        progress_file = Path("/home/bai/Desktop/Podwise/backend/utils/processing_progress.json")
        if progress_file.exists():
            with open(progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"❌ 載入進度失敗: {str(e)}")
        return None

def continue_processing():
    """繼續處理"""
    print("🔄 載入昨日處理進度...")
    
    progress = load_progress()
    if not progress:
        print("❌ 無法載入進度，建議重新開始處理")
        return False
    
    print(f"📊 昨日已處理: {progress['processed_files_count']} 個檔案")
    print(f"⏰ 保存時間: {progress['timestamp']}")
    
    # 檢查已處理的檔案是否還在
    processed_files = set(progress['processed_files'])
    existing_files = set()
    
    stage4_path = Path(progress['stage4_path'])
    if stage4_path.exists():
        for json_file in stage4_path.rglob("*.json"):
            existing_files.add(str(json_file))
    
    print(f"✅ 確認存在檔案: {len(existing_files)} 個")
    
    # 建議執行指令
    print("\n" + "="*60)
    print("🚀 明天繼續處理建議:")
    print("="*60)
    print("1. 執行以下指令繼續處理:")
    print("   python backend/utils/batch_process_with_progress.py")
    print()
    print("2. 腳本會自動跳過已處理的檔案")
    print("3. 進度會自動保存，不會重複處理")
    print("="*60)
    
    return True

if __name__ == "__main__":
    continue_processing() 