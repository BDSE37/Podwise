#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查 JSON 檔案結構的腳本
"""

import json
import sys

def check_structure(file_path):
    """檢查檔案結構"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"檔案: {file_path}")
        print(f"資料類型: {type(data)}")
        
        if isinstance(data, dict):
            print("主要欄位:")
            for key, value in list(data.items())[:10]:  # 只顯示前10個欄位
                if isinstance(value, str):
                    print(f"  {key}: {value[:100]}...")
                else:
                    print(f"  {key}: {type(value)}")
        
        elif isinstance(data, list):
            print(f"列表長度: {len(data)}")
            if len(data) > 0:
                print("第一個項目欄位:")
                first_item = data[0]
                if isinstance(first_item, dict):
                    for key, value in list(first_item.items())[:10]:
                        if isinstance(value, str):
                            print(f"  {key}: {value[:100]}...")
                        else:
                            print(f"  {key}: {type(value)}")
        
        # 檢查是否包含股癌相關資訊
        if isinstance(data, dict):
            title = data.get('episode_title', '')
            podcast_id = data.get('podcast_id', '')
            print(f"\n標題: {title}")
            print(f"Podcast ID: {podcast_id}")
        
        elif isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            title = first_item.get('episode_title', '')
            podcast_id = first_item.get('podcast_id', '')
            print(f"\n第一個項目標題: {title}")
            print(f"第一個項目 Podcast ID: {podcast_id}")
        
    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python check_data_structure.py <檔案路徑>")
        sys.exit(1)
    
    check_structure(sys.argv[1]) 