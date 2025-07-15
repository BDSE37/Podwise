#!/usr/bin/env python3
"""
Debug 腳本：追蹤 chunk_id 在處理過程中的變化
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

def trace_chunk_id():
    """追蹤 chunk_id 的變化"""
    # 設定路徑
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    stage3_path = project_root / "backend/vector_pipeline/data/stage3_tagging"
    
    print(f"🔍 追蹤 chunk_id 變化")
    print(f"📁 檢查目錄: {stage3_path}")
    
    # 找到第一個 JSON 檔案
    rss_dirs = [d for d in stage3_path.iterdir() if d.is_dir() and d.name.startswith("RSS_")]
    
    if not rss_dirs:
        print("❌ 沒有找到 RSS 目錄")
        return
    
    first_rss_dir = rss_dirs[0]
    json_files = list(first_rss_dir.glob("*.json"))
    
    if not json_files:
        print("❌ 沒有找到 JSON 檔案")
        return
    
    first_json_file = json_files[0]
    print(f"📄 檢查檔案: {first_json_file.name}")
    
    try:
        with open(first_json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chunks = data.get('chunks', [])
        if not chunks:
            print("❌ 沒有 chunks")
            return
        
        # 檢查第一個 chunk
        first_chunk = chunks[0]
        print(f"\n🔍 原始 chunk 資料:")
        print(f"   chunk_id: {first_chunk.get('chunk_id')} (型態: {type(first_chunk.get('chunk_id'))})")
        
        # 模擬 ensure_field_has_value 的處理
        def ensure_field_has_value(value: Any, field_name: str, default_value: Any, max_length: Optional[int] = None) -> Any:
            print(f"   🔧 ensure_field_has_value: {field_name} = {value} (型態: {type(value)})")
            
            if value is None or value == '' or value == 'null' or value == 'None':
                print(f"   ✅ 使用預設值: {default_value}")
                return default_value
            
            # 處理 Decimal 類型
            if hasattr(value, '__class__') and value.__class__.__name__ == 'Decimal':
                value = float(value)
                print(f"   🔧 Decimal 轉 float: {value}")
            
            # 如果是字串且超過最大長度，截斷
            if isinstance(value, str) and max_length:
                if len(value) > max_length:
                    result = value[:max_length]
                    print(f"   🔧 字串截斷: {value} -> {result}")
                    return result
            
            print(f"   ✅ 返回原值: {value} (型態: {type(value)})")
            return value
        
        # 模擬處理過程
        print(f"\n🔧 模擬處理過程:")
        original_chunk_id = first_chunk.get('chunk_id')
        processed_chunk_id = ensure_field_has_value(original_chunk_id, 'chunk_id', 'unknown_0', 64)
        
        print(f"\n📊 處理結果:")
        print(f"   原始: {original_chunk_id} (型態: {type(original_chunk_id)})")
        print(f"   處理後: {processed_chunk_id} (型態: {type(processed_chunk_id)})")
        
        # 檢查是否有其他問題
        print(f"\n🔍 檢查其他可能問題:")
        
        # 檢查 JSON 序列化
        test_dict = {'chunk_id': processed_chunk_id}
        json_str = json.dumps(test_dict, ensure_ascii=False)
        print(f"   JSON 序列化: {json_str}")
        
        # 檢查 JSON 反序列化
        parsed_dict = json.loads(json_str)
        print(f"   JSON 反序列化: {parsed_dict['chunk_id']} (型態: {type(parsed_dict['chunk_id'])})")
        
        # 檢查是否有隱藏的 list 轉換
        if isinstance(processed_chunk_id, str):
            # 檢查是否被意外轉換為 list
            test_list = [processed_chunk_id]
            print(f"   List 測試: {test_list} (型態: {type(test_list)})")
            
            # 檢查是否在某個地方被當作 list 處理
            if len(test_list) == 1:
                single_item = test_list[0]
                print(f"   單一項目: {single_item} (型態: {type(single_item)})")
        
    except Exception as e:
        print(f"❌ 處理失敗: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    trace_chunk_id() 