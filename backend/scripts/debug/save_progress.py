#!/usr/bin/env python3
"""
保存處理進度，避免重複處理
"""

import json
import os
from pathlib import Path
from datetime import datetime

def save_processing_progress():
    """保存處理進度"""
    try:
        # 檢查已處理的檔案
        stage4_path = Path("/home/bai/Desktop/Podwise/backend/vector_pipeline/data/stage4_embedding_prep")
        processed_files = []
        
        if stage4_path.exists():
            for json_file in stage4_path.rglob("*.json"):
                processed_files.append(str(json_file))
        
        # 保存進度資訊
        progress_info = {
            "timestamp": datetime.now().isoformat(),
            "processed_files_count": len(processed_files),
            "processed_files": processed_files,
            "stage4_path": str(stage4_path),
            "note": "關機前保存的進度，明天可從此處繼續"
        }
        
        # 保存到檔案
        progress_file = Path("/home/bai/Desktop/Podwise/backend/utils/processing_progress.json")
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_info, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 進度已保存至: {progress_file}")
        print(f"📊 已處理檔案數: {len(processed_files)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 保存進度失敗: {str(e)}")
        return False

if __name__ == "__main__":
    save_processing_progress() 