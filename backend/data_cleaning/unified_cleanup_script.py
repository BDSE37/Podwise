#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統一清理腳本
整合所有清理功能，提供統一的命令列介面
符合 Google Clean Code 原則
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加父目錄到路徑
sys.path.append(str(Path(__file__).parent.parent))

def clean_comment_data():
    """清理 comment_data 資料夾"""
    from data_cleaning import UnifiedCleaner
    
    print("=== 清理 comment_data 資料夾 ===")
    
    # 建立統一清理器
    config = {
        "enable_emoji_removal": True,
        "enable_html_removal": True,
        "enable_special_char_removal": True,
        "enable_json_format_fix": True,
        "enable_filename_cleaning": True,
        "preserve_urls": True,
        "max_filename_length": 100
    }
    
    cleaner = UnifiedCleaner(config)
    
    # 來源和目標目錄
    source_dir = "backend/vaderSentiment/comment_data"
    target_dir = "backend/data_cleaning/batch_input"
    
    # 確保目標目錄存在
    os.makedirs(target_dir, exist_ok=True)
    
    # 複製檔案到 batch_input
    copied_count = 0
    for filename in os.listdir(source_dir):
        if filename.endswith('.json'):
            source_file = os.path.join(source_dir, filename)
            target_file = os.path.join(target_dir, filename)
            
            import shutil
            shutil.copy2(source_file, target_file)
            copied_count += 1
            print(f"已複製: {filename}")
    
    print(f"共複製 {copied_count} 個檔案到 batch_input")
    
    # 修正 JSON 格式
    print("\n=== 修正 JSON 格式 ===")
    fixed_count = cleaner.batch_fix_json_format(target_dir)
    print(f"修正了 {fixed_count} 個檔案的 JSON 格式")
    
    return target_dir

def clean_with_orchestrator():
    """使用協調器清理"""
    from data_cleaning.services.cleaner_orchestrator import CleanerOrchestrator
    
    print("\n=== 使用協調器清理 ===")
    
    # 建立協調器
    orchestrator = CleanerOrchestrator()
    
    # 批次清理
    batch_input_dir = "backend/data_cleaning/batch_input"
    if os.path.exists(batch_input_dir):
        # 尋找所有 JSON 檔案
        json_files = []
        for filename in os.listdir(batch_input_dir):
            if filename.endswith('.json'):
                json_files.append(os.path.join(batch_input_dir, filename))
        
        if json_files:
            print(f"找到 {len(json_files)} 個檔案需要清理")
            cleaned_files = orchestrator.batch_clean_files(json_files)
            print(f"協調器清理完成，共清理 {len(cleaned_files)} 個檔案")
            return cleaned_files
        else:
            print("沒有找到需要清理的 JSON 檔案")
    else:
        print("batch_input 目錄不存在")
    
    return []

def clean_with_unified_cleaner():
    """使用統一清理器清理"""
    from data_cleaning import UnifiedCleaner
    
    print("\n=== 使用統一清理器清理 ===")
    
    # 建立統一清理器
    cleaner = UnifiedCleaner()
    
    # 批次清理
    batch_input_dir = "backend/data_cleaning/batch_input"
    if os.path.exists(batch_input_dir):
        # 尋找所有 JSON 檔案
        json_files = []
        for filename in os.listdir(batch_input_dir):
            if filename.endswith('.json'):
                json_files.append(os.path.join(batch_input_dir, filename))
        
        if json_files:
            print(f"找到 {len(json_files)} 個檔案需要清理")
            cleaned_files = cleaner.batch_clean_files(json_files)
            print(f"統一清理器清理完成，共清理 {len(cleaned_files)} 個檔案")
            return cleaned_files
        else:
            print("沒有找到需要清理的 JSON 檔案")
    else:
        print("batch_input 目錄不存在")
    
    return []

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="統一清理腳本")
    parser.add_argument('--method', choices=['orchestrator', 'unified', 'both'], 
                       default='both', help='清理方法')
    parser.add_argument('--source', type=str, 
                       default='backend/vaderSentiment/comment_data',
                       help='來源資料夾')
    parser.add_argument('--target', type=str, 
                       default='backend/data_cleaning/batch_input',
                       help='目標資料夾')
    
    args = parser.parse_args()
    
    print("統一清理腳本")
    print("=" * 50)
    
    # 清理 comment_data
    clean_comment_data()
    
    # 根據方法選擇清理器
    if args.method in ['orchestrator', 'both']:
        clean_with_orchestrator()
    
    if args.method in ['unified', 'both']:
        clean_with_unified_cleaner()
    
    print("\n" + "=" * 50)
    print("清理完成！")
    print("\n可用的清理方法：")
    print("1. 協調器 (CleanerOrchestrator) - 自動偵測格式並清理")
    print("2. 統一清理器 (UnifiedCleaner) - 統一的清理介面")
    print("3. 批次清理 (batch_clean_folder.py) - 批次處理整個資料夾")

if __name__ == "__main__":
    main() 