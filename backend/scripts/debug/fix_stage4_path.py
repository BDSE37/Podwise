#!/usr/bin/env python3
"""
修復 stage4_embedding_prep 路徑問題
"""

import os
from pathlib import Path

def fix_stage4_path():
    """修復 stage4_embedding_prep 路徑"""
    try:
        # 取得當前腳本目錄
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent
        
        # 建立正確的 stage4 路徑
        stage4_path = project_root / "backend/vector_pipeline/data/stage4_embedding_prep"
        
        print(f"🔧 修復 stage4_embedding_prep 路徑...")
        print(f"   當前目錄: {current_dir}")
        print(f"   專案根目錄: {project_root}")
        print(f"   Stage4 路徑: {stage4_path}")
        
        # 確保目錄存在
        stage4_path.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ 成功建立/確認目錄: {stage4_path}")
        
        # 檢查目錄是否真的存在
        if stage4_path.exists():
            print(f"✅ 目錄確認存在")
            return True
        else:
            print(f"❌ 目錄建立失敗")
            return False
            
    except Exception as e:
        print(f"❌ 修復失敗: {str(e)}")
        return False

if __name__ == "__main__":
    fix_stage4_path() 