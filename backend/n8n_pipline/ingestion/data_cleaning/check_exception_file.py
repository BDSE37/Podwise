#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查例外處理檔案結構的腳本
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
                    
            # 檢查是否有 name 欄位
            if 'name' in data:
                print(f"\n找到 'name' 欄位: {data['name']}")
                
            # 檢查是否有其他可能的標題欄位
            title_fields = ['title', 'episode_title', 'name', 'episode_name']
            for field in title_fields:
                if field in data:
                    print(f"找到 '{field}' 欄位: {data[field]}")
        
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
                            
                    # 檢查是否有 name 欄位
                    if 'name' in first_item:
                        print(f"\n找到 'name' 欄位: {first_item['name']}")
                        
                    # 檢查是否有其他可能的標題欄位
                    title_fields = ['title', 'episode_title', 'name', 'episode_name']
                    for field in title_fields:
                        if field in first_item:
                            print(f"找到 '{field}' 欄位: {first_item[field]}")
        
    except Exception as e:
        print(f"❌ 讀取檔案失敗: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python check_exception_file.py <檔案路徑>")
        sys.exit(1)
    
    check_structure(sys.argv[1]) 