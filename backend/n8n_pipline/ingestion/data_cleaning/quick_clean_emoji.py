#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速清理表情符號腳本
專門用於清理 comment_data 中的表情符號
"""

import os
import sys
import shutil
from pathlib import Path

# 添加父目錄到路徑
sys.path.append(str(Path(__file__).parent.parent))

def quick_clean_emoji():
    """快速清理 comment_data 中的表情符號"""
    print("=== 快速清理 comment_data 表情符號 ===")
    
    from data_cleaning import UnifiedCleaner
    
    # 建立清理器
    cleaner = UnifiedCleaner()
    
    # 來源和目標目錄
    source_dir = "backend/vaderSentiment/comment_data"
    target_dir = "backend/data_cleaning/batch_input"
    
    # 確保目標目錄存在
    os.makedirs(target_dir, exist_ok=True)
    
    # 複製檔案到 batch_input
    copied_count = 0
    json_files = []
    
    for filename in os.listdir(source_dir):
        if filename.endswith('.json'):
            source_file = os.path.join(source_dir, filename)
            target_file = os.path.join(target_dir, filename)
            
            shutil.copy2(source_file, target_file)
            json_files.append(target_file)
            copied_count += 1
            print(f"已複製: {filename}")
    
    print(f"共複製 {copied_count} 個檔案到 batch_input")
    
    if not json_files:
        print("沒有找到 JSON 檔案")
        return
    
    # 批次清理
    print("\n=== 開始清理表情符號 ===")
    cleaned_files = cleaner.batch_clean_files(json_files)
    
    print(f"\n=== 清理完成 ===")
    print(f"共處理 {len(cleaned_files)} 個檔案")
    print(f"清理後的檔案位置: {target_dir}")
    
    # 顯示清理範例
    if cleaned_files:
        print("\n=== 清理範例 ===")
        try:
            with open(cleaned_files[0], 'r', encoding='utf-8') as f:
                import json
                data = json.load(f)
                if 'content' in data:
                    content = data['content']
                    print(f"原始長度: {len(content)} 字元")
                    print(f"內容預覽: {content[:100]}...")
        except Exception as e:
            print(f"讀取範例檔案失敗: {e}")

if __name__ == "__main__":
    quick_clean_emoji() 