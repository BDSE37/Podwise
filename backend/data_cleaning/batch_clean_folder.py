#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批次清理資料夾腳本
- 遞迴處理指定資料夾（含所有子資料夾）下的所有 .json/.csv/.txt 檔案
- 清理結果統一輸出到 ../../data/cleaned_data
- 若 batch_input 資料夾不存在則自動建立

用法：
    python batch_clean_folder.py --input-folder batch_input --output-folder batch_output
    # 可加 --output-folder 指定輸出資料夾
    請直接cd Podwise/backend/data_cleaning 這個資料夾
    將待清理的檔案放進batch_input
    執行上面的程式
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List

# 動態導入清理協調器
sys.path.append(str(Path(__file__).parent))
from services.cleaner_orchestrator import CleanerOrchestrator

def find_supported_files(root_dir: str, exts=(".json", ".csv", ".txt")) -> List[str]:
    """遞迴尋找所有支援的檔案"""
    files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            if fname.lower().endswith(exts):
                files.append(os.path.join(dirpath, fname))
    return files

def main():
    parser = argparse.ArgumentParser(description="批次清理指定資料夾下所有支援檔案")
    parser.add_argument('--input-folder', type=str, default="backend/data_cleaning/batch_input", help='要清理的資料夾路徑')
    parser.add_argument('--output-folder', type=str, default="../../data/cleaned_data", help='清理結果輸出資料夾')
    args = parser.parse_args()

    input_folder = args.input_folder
    output_folder = args.output_folder

    # 若 input_folder 不存在則自動建立
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)

    print(f"[INFO] 掃描資料夾: {input_folder}")
    files = find_supported_files(input_folder)
    print(f"[INFO] 共找到 {len(files)} 個支援檔案")
    if not files:
        print("[INFO] 沒有可處理的檔案，請將資料放入指定資料夾後再執行。")
        return

    orchestrator = CleanerOrchestrator(output_dir=output_folder)
    success, fail = 0, 0
    for f in files:
        try:
            print(f"[INFO] 清理檔案: {f}")
            out = orchestrator.clean_file(f)
            print(f"[OK] 輸出: {out}")
            success += 1
        except Exception as e:
            print(f"[ERROR] 處理失敗: {f} | {e}")
            fail += 1
    print(f"[SUMMARY] 成功: {success}，失敗: {fail}")

if __name__ == "__main__":
    main() 