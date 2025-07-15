#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小規模轉換腳本 - 處理前10個檔案供確認格式
"""

import os
import sys
import json
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from convert_to_milvus_format import MilvusDataConverter


def convert_sample_data():
    """轉換前10個檔案供確認格式"""
    print("🚀 開始小規模轉換測試...")
    
    # 建立轉換器
    converter = MilvusDataConverter()
    
    # 設定目錄
    stage3_dir = "data/stage3_tagging"
    output_dir = "data/stage4_embedding_prep"
    
    stage3_path = Path(stage3_dir)
    output_path = Path(output_dir)
    
    if not stage3_path.exists():
        print(f"❌ 目錄不存在: {stage3_dir}")
        return
    
    # 確保輸出目錄存在
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 獲取所有 JSON 檔案
    json_files = list(stage3_path.rglob("*.json"))
    
    # 只處理前10個檔案
    sample_files = json_files[:10]
    
    print(f"📁 找到 {len(json_files)} 個檔案，將處理前 {len(sample_files)} 個")
    
    total_chunks = 0
    successful_files = 0
    
    for i, json_file in enumerate(sample_files, 1):
        try:
            print(f"\n📄 處理檔案 {i}/{len(sample_files)}: {json_file.name}")
            
            # 轉換檔案
            milvus_chunks = converter.convert_file_to_milvus_format(json_file)
            
            if milvus_chunks:
                # 儲存轉換後的資料
                output_file = output_path / f"{json_file.stem}_milvus.json"
                
                output_data = {
                    "filename": json_file.name,
                    "total_chunks": len(milvus_chunks),
                    "converted_at": converter.convert_chunk_to_milvus_format.__name__,
                    "chunks": milvus_chunks
                }
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=2)
                
                successful_files += 1
                total_chunks += len(milvus_chunks)
                
                print(f"✅ 成功轉換: {len(milvus_chunks)} chunks")
                
                # 顯示第一個 chunk 的格式（僅前3個檔案）
                if i <= 3:
                    print("\n📋 第一個 chunk 格式:")
                    first_chunk = milvus_chunks[0]
                    for key, value in first_chunk.items():
                        print(f"  {key}: {type(value).__name__} = {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
                    print()
            else:
                print(f"❌ 轉換失敗: {json_file.name}")
            
        except Exception as e:
            print(f"❌ 處理檔案失敗 {json_file.name}: {e}")
    
    print(f"\n🎉 小規模轉換完成！")
    print(f"成功處理: {successful_files}/{len(sample_files)} 檔案")
    print(f"總 chunks: {total_chunks}")
    print(f"輸出目錄: {output_path}")
    
    # 顯示轉換後的檔案列表
    output_files = list(output_path.glob("*_milvus.json"))
    print(f"\n📁 轉換後的檔案:")
    for output_file in output_files:
        print(f"  {output_file.name}")


if __name__ == "__main__":
    convert_sample_data() 