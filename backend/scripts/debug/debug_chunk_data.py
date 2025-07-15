#!/usr/bin/env python3
"""
Debug 腳本：檢查 stage3_tagging 中的資料結構
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

def check_chunk_data():
    """檢查 chunk 資料結構"""
    # 設定路徑
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    stage3_path = project_root / "backend/vector_pipeline/data/stage3_tagging"
    
    print(f"🔍 檢查目錄: {stage3_path}")
    
    if not stage3_path.exists():
        print(f"❌ 目錄不存在: {stage3_path}")
        return
    
    # 找到第一個 JSON 檔案
    rss_dirs = [d for d in stage3_path.iterdir() if d.is_dir() and d.name.startswith("RSS_")]
    
    if not rss_dirs:
        print("❌ 沒有找到 RSS 目錄")
        return
    
    first_rss_dir = rss_dirs[0]
    print(f"📁 檢查目錄: {first_rss_dir.name}")
    
    json_files = list(first_rss_dir.glob("*.json"))
    
    if not json_files:
        print("❌ 沒有找到 JSON 檔案")
        return
    
    first_json_file = json_files[0]
    print(f"📄 檢查檔案: {first_json_file.name}")
    
    try:
        with open(first_json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n📊 檔案結構:")
        print(f"   - 總 chunks 數量: {len(data.get('chunks', []))}")
        
        # 檢查前 3 個 chunks
        chunks = data.get('chunks', [])
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n🔍 Chunk {i+1}:")
            print(f"   - chunk_id: {chunk.get('chunk_id')} (型態: {type(chunk.get('chunk_id'))})")
            print(f"   - chunk_index: {chunk.get('chunk_index')} (型態: {type(chunk.get('chunk_index'))})")
            print(f"   - chunk_text 長度: {len(chunk.get('chunk_text', ''))}")
            print(f"   - enhanced_tags: {chunk.get('enhanced_tags')} (型態: {type(chunk.get('enhanced_tags'))})")
            
            # 詳細檢查 chunk_id
            chunk_id = chunk.get('chunk_id')
            if isinstance(chunk_id, list):
                print(f"   ⚠️  chunk_id 是 list，內容: {chunk_id}")
                if len(chunk_id) > 0:
                    print(f"   - 第一個元素: {chunk_id[0]} (型態: {type(chunk_id[0])})")
            else:
                print(f"   ✅ chunk_id 不是 list")
        
        # 檢查是否有其他欄位是 list
        print(f"\n🔍 檢查所有欄位型態:")
        if chunks:
            sample_chunk = chunks[0]
            for key, value in sample_chunk.items():
                if isinstance(value, list):
                    print(f"   ⚠️  {key}: {type(value)} = {value}")
                else:
                    print(f"   ✅ {key}: {type(value)} = {str(value)[:50]}...")
        
    except Exception as e:
        print(f"❌ 讀取檔案失敗: {str(e)}")

if __name__ == "__main__":
    check_chunk_data() 