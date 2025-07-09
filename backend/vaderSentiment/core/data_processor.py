#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
資料處理器模組

負責 JSON 檔案處理、資料轉換、批次處理等功能
"""

import json
import os
import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class ProcessedItem:
    """處理後的資料項目"""
    filename: str
    content: str
    field_type: str
    original_data: Dict[str, Any]


class DataProcessor:
    """資料處理器"""
    
    def __init__(self, data_directory: str = "comment_data"):
        """
        初始化資料處理器
        
        Args:
            data_directory: 資料目錄路徑
        """
        self.data_directory = data_directory
    
    def process_json_file(self, file_path: str) -> List[ProcessedItem]:
        """
        處理單個 JSON 檔案
        
        Args:
            file_path: JSON 檔案路徑
            
        Returns:
            處理後的資料項目列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            filename = os.path.basename(file_path)
            items = []
            
            if isinstance(data, dict):
                # 單一物件
                item = self._process_item(data, filename, 0)
                if item:
                    items.append(item)
            elif isinstance(data, list):
                # 物件陣列
                for i, item_data in enumerate(data):
                    item = self._process_item(item_data, filename, i)
                    if item:
                        items.append(item)
            
            return items
            
        except Exception as e:
            print(f"處理檔案 {file_path} 時發生錯誤: {e}")
            return []
    
    def _process_item(self, item: Dict[str, Any], filename: str, index: int) -> Optional[ProcessedItem]:
        """
        處理單個資料項目
        
        Args:
            item: 資料項目
            filename: 檔案名稱
            index: 項目索引
            
        Returns:
            處理後的資料項目
        """
        if not isinstance(item, dict):
            return None
        
        # 提取文本內容
        content = self._extract_text_content(item)
        
        if not content:
            return None
        
        # 獲取欄位類型
        field_type = self._get_field_type(item)
        
        return ProcessedItem(
            filename=filename,
            content=content,
            field_type=field_type,
            original_data=item
        )
    
    def _extract_text_content(self, item: Dict[str, Any]) -> str:
        """
        提取文本內容
        
        Args:
            item: 資料項目
            
        Returns:
            提取的文本內容
        """
        # 優先順序：content > text > message > title > description
        content_fields = ['content', 'text', 'message', 'title', 'description']
        
        for field in content_fields:
            if field in item and item[field]:
                content = str(item[field]).strip()
                if content:
                    return content
        
        # 如果沒有找到標準欄位，嘗試合併所有字串欄位
        text_parts = []
        for key, value in item.items():
            if isinstance(value, str) and value.strip():
                text_parts.append(value.strip())
        
        return ' '.join(text_parts) if text_parts else ""
    
    def _get_field_type(self, item: Dict[str, Any]) -> str:
        """
        獲取欄位類型
        
        Args:
            item: 資料項目
            
        Returns:
            欄位類型
        """
        # 根據欄位名稱判斷類型
        if 'content' in item:
            return 'content'
        elif 'text' in item:
            return 'text'
        elif 'message' in item:
            return 'message'
        elif 'title' in item:
            return 'title'
        elif 'description' in item:
            return 'description'
        else:
            return 'unknown'
    
    def process_directory(self) -> List[ProcessedItem]:
        """
        處理整個目錄的 JSON 檔案
        
        Returns:
            所有處理後的資料項目
        """
        all_items = []
        
        if not os.path.exists(self.data_directory):
            print(f"目錄不存在: {self.data_directory}")
            return all_items
        
        for filename in os.listdir(self.data_directory):
            if filename.endswith('.json'):
                file_path = os.path.join(self.data_directory, filename)
                items = self.process_json_file(file_path)
                all_items.extend(items)
        
        return all_items
    
    def to_dataframe(self, items: List[ProcessedItem]) -> pd.DataFrame:
        """
        將處理後的項目轉換為 DataFrame
        
        Args:
            items: 處理後的資料項目列表
            
        Returns:
            DataFrame
        """
        data = []
        for item in items:
            data.append({
                'filename': item.filename,
                'content': item.content,
                'field_type': item.field_type,
                'content_length': len(item.content)
            })
        
        return pd.DataFrame(data)
    
    def save_to_csv(self, items: List[ProcessedItem], output_file: str) -> None:
        """
        儲存為 CSV 檔案
        
        Args:
            items: 處理後的資料項目列表
            output_file: 輸出檔案路徑
        """
        df = self.to_dataframe(items)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"已儲存 {len(items)} 個項目至: {output_file}")
    
    def fix_json_format(self, file_path: str) -> bool:
        """
        修正 JSON 格式（將 list 合併為 dict）
        
        Args:
            file_path: JSON 檔案路徑
            
        Returns:
            是否成功修正
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                # 合併所有 content 欄位
                contents = []
                for item in data:
                    if isinstance(item, dict) and 'content' in item:
                        content = str(item['content']).strip()
                        if content:
                            contents.append(content)
                
                if contents:
                    merged_content = '\n'.join(contents)
                    new_data = {"content": merged_content}
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(new_data, f, ensure_ascii=False, indent=2)
                    
                    return True
            
            return False
            
        except Exception as e:
            print(f"修正檔案 {file_path} 時發生錯誤: {e}")
            return False
    
    def batch_fix_json_format(self) -> int:
        """
        批次修正目錄下所有 JSON 檔案格式
        
        Returns:
            修正的檔案數量
        """
        fixed_count = 0
        
        if not os.path.exists(self.data_directory):
            print(f"目錄不存在: {self.data_directory}")
            return fixed_count
        
        for filename in os.listdir(self.data_directory):
            if filename.endswith('.json'):
                file_path = os.path.join(self.data_directory, filename)
                if self.fix_json_format(file_path):
                    fixed_count += 1
        
        print(f"批次修正完成，共修正 {fixed_count} 個檔案")
        return fixed_count 