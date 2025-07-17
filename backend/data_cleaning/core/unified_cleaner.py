#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統一清理模組
整合所有清理功能，提供統一的 OOP 介面
符合 Google Clean Code 原則
"""

import re
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import logging

# 添加父目錄到路徑以支援絕對導入
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from data_cleaning.core.base_cleaner import BaseCleaner
    from data_cleaning.core.longtext_cleaner import LongTextCleaner
except ImportError:
    # Fallback: 相對導入
    from core.base_cleaner import BaseCleaner
    from core.longtext_cleaner import LongTextCleaner


class UnifiedCleaner(BaseCleaner):
    """
    統一清理器
    整合所有清理功能，提供統一的 OOP 介面
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化統一清理器
        
        Args:
            config: 清理配置
        """
        self.longtext_cleaner = LongTextCleaner()
        self.logger = logging.getLogger(__name__)
        
        # 預設配置
        self.config = {
            "enable_emoji_removal": True,
            "enable_html_removal": True,
            "enable_special_char_removal": True,
            "enable_json_format_fix": True,
            "enable_filename_cleaning": True,
            "preserve_urls": True,
            "max_filename_length": 100
        }
        
        # 合併自定義配置
        if config:
            self.config.update(config)
    
    def clean(self, data: Any) -> Any:
        """
        清理資料（實現 BaseCleaner 介面）
        
        Args:
            data: 要清理的資料
            
        Returns:
            清理後的資料
        """
        if isinstance(data, str):
            return self.clean_text(data)
        elif isinstance(data, dict):
            return self.clean_dict(data)
        elif isinstance(data, list):
            return self.clean_list(data)
        else:
            return data
    
    def clean_text(self, text: str) -> str:
        """
        清理文本內容
        
        Args:
            text: 原始文本
            
        Returns:
            清理後的文本
        """
        if not text or not isinstance(text, str):
            return ""
        
        # 使用 LongTextCleaner 進行基礎清理
        cleaned_text = self.longtext_cleaner.clean(text)
        
        # 額外的清理步驟
        if self.config["enable_html_removal"]:
            cleaned_text = self._remove_html_tags(cleaned_text)
        
        if self.config["enable_special_char_removal"]:
            cleaned_text = self._remove_special_chars(cleaned_text)
        
        return cleaned_text
    
    def clean_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理字典資料
        
        Args:
            data: 原始字典
            
        Returns:
            清理後的字典
        """
        cleaned_data = data.copy()
        
        # 清理所有字串欄位
        for key, value in cleaned_data.items():
            if isinstance(value, str):
                cleaned_data[key] = self.clean_text(value)
            elif isinstance(value, dict):
                cleaned_data[key] = self.clean_dict(value)
            elif isinstance(value, list):
                cleaned_data[key] = self.clean_list(value)
        
        # 添加清理資訊
        cleaned_data['cleaned_at'] = datetime.now().isoformat()
        cleaned_data['cleaner_type'] = 'unified_cleaner'
        
        return cleaned_data
    
    def clean_list(self, data: List[Any]) -> List[Any]:
        """
        清理列表資料
        
        Args:
            data: 原始列表
            
        Returns:
            清理後的列表
        """
        return [self.clean(item) for item in data]
    
    def clean_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """
        清理檔案內容和檔案名稱
        
        Args:
            file_path: 輸入檔案路徑
            output_path: 輸出檔案路徑（可選）
            
        Returns:
            清理後的檔案路徑
        """
        try:
            # 讀取檔案
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 清理資料
            cleaned_data = self.clean(data)
            
            # 處理檔案名稱
            original_path = Path(file_path)
            if self.config["enable_filename_cleaning"]:
                cleaned_name = self._clean_filename(original_path.name)
            else:
                cleaned_name = original_path.name
            
            # 決定輸出路徑
            if output_path:
                output_file = Path(output_path)
            else:
                output_file = original_path.parent / cleaned_name
            
            # 寫入清理後的檔案
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"檔案清理完成: {file_path} -> {output_file}")
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"清理檔案失敗 {file_path}: {e}")
            raise
    
    def fix_json_format(self, file_path: str) -> bool:
        """
        修正 JSON 格式（整合自 vaderSentiment）
        
        Args:
            file_path: 檔案路徑
            
        Returns:
            是否修正成功
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 如果已經是字典格式，不需要修正
            if isinstance(data, dict):
                return True
            
            # 如果是列表，合併 content
            if isinstance(data, list):
                contents = []
                for item in data:
                    if isinstance(item, dict) and 'content' in item and isinstance(item['content'], str):
                        contents.append(item['content'])
                
                merged_content = '\n'.join(contents)
                new_data = {"content": merged_content, "filename": Path(file_path).name}
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, ensure_ascii=False, indent=2)
                
                self.logger.info(f"JSON 格式修正完成: {file_path}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"修正 JSON 格式失敗 {file_path}: {e}")
            return False
    
    def batch_clean_files(self, file_paths: List[str], output_dir: Optional[str] = None) -> List[str]:
        """
        批次清理多個檔案
        
        Args:
            file_paths: 檔案路徑列表
            output_dir: 輸出目錄（可選）
            
        Returns:
            清理後的檔案路徑列表
        """
        cleaned_files = []
        
        for i, file_path in enumerate(file_paths):
            try:
                if output_dir:
                    # 生成輸出檔案名稱
                    original_name = Path(file_path).name
                    if self.config["enable_filename_cleaning"]:
                        cleaned_name = self._clean_filename(original_name)
                    else:
                        cleaned_name = original_name
                    
                    output_path = Path(output_dir) / cleaned_name
                else:
                    output_path = None
                
                cleaned_file = self.clean_file(file_path, str(output_path) if output_path else None)
                cleaned_files.append(cleaned_file)
                
                if (i + 1) % 10 == 0:
                    self.logger.info(f"已清理 {i + 1}/{len(file_paths)} 個檔案")
                    
            except Exception as e:
                self.logger.error(f"清理檔案失敗 {file_path}: {e}")
                cleaned_files.append(file_path)  # 保留原始檔案路徑
        
        return cleaned_files
    
    def _remove_html_tags(self, text: str) -> str:
        """移除 HTML 標籤"""
        return re.sub(r'<[^>]+>', '', text)
    
    def _remove_special_chars(self, text: str) -> str:
        """移除特殊字元，保留中英文、數字和基本標點"""
        if self.config["preserve_urls"]:
            # 保留 URL 相關字元
            allowed_chars = set(' .,!?()[]{}:;\'"#@&+=%$*-_/')
        else:
            allowed_chars = set(' .,!?()[]{}:;\'"#@&+=%$*-_')
        
        return ''.join(c for c in text if c.isalnum() or '\u4e00' <= c <= '\u9fff' or c in allowed_chars)
    
    def _clean_filename(self, filename: str) -> str:
        """
        清理檔案名稱
        
        Args:
            filename: 原始檔案名稱
            
        Returns:
            清理後的檔案名稱
        """
        if not filename:
            return "cleaned_file.json"
        
        # 分離檔案名稱和副檔名
        name, ext = os.path.splitext(filename)
        
        # 移除表情符號和特殊字元
        name = self.clean_text(name)
        
        # 移除檔案系統不允許的字元
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '')
        
        # 替換空白為底線
        name = name.replace(' ', '_')
        
        # 限制長度
        max_length = self.config["max_filename_length"]
        if len(name) > max_length:
            name = name[:max_length]
        
        # 確保檔案名稱不為空
        if not name:
            name = "cleaned_file"
        
        # 確保副檔名
        if not ext:
            ext = ".json"
        
        return name + ext
    
    def get_config(self) -> Dict[str, Any]:
        """取得當前配置"""
        return self.config.copy()
    
    def update_config(self, new_config: Dict[str, Any]):
        """更新配置"""
        self.config.update(new_config)
    
    def batch_fix_json_format(self, directory: str) -> int:
        """
        批次修正目錄中的 JSON 格式
        
        Args:
            directory: 目錄路徑
            
        Returns:
            修正的檔案數量
        """
        fixed_count = 0
        error_files = []
        
        for filename in os.listdir(directory):
            if not filename.endswith('.json'):
                continue
            
            file_path = os.path.join(directory, filename)
            if self.fix_json_format(file_path):
                fixed_count += 1
            else:
                error_files.append(filename)
        
        self.logger.info(f"JSON 格式修正完成: 成功 {fixed_count} 個檔案")
        if error_files:
            self.logger.warning(f"修正失敗的檔案: {error_files}")
        
        return fixed_count
    
    def quick_clean_emoji_from_folder(self, source_dir: str, target_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        快速清理指定資料夾中所有 JSON 檔案的表情符號
        
        Args:
            source_dir: 來源資料夾路徑
            target_dir: 目標資料夾路徑（可選）
            
        Returns:
            處理結果統計
        """
        import shutil
        
        source_path = Path(source_dir)
        if target_dir:
            target_path = Path(target_dir)
        else:
            target_path = source_path
        
        # 確保目標目錄存在
        target_path.mkdir(parents=True, exist_ok=True)
        
        # 統計資訊
        stats = {
            'total_files': 0,
            'processed_files': 0,
            'cleaned_files': [],
            'errors': []
        }
        
        # 處理所有 JSON 檔案
        for json_file in source_path.glob("*.json"):
            stats['total_files'] += 1
            
            try:
                # 複製檔案到目標目錄
                target_file = target_path / json_file.name
                shutil.copy2(json_file, target_file)
                
                # 清理檔案內容
                cleaned_file = self.clean_file(str(target_file))
                stats['cleaned_files'].append(cleaned_file)
                stats['processed_files'] += 1
                
                self.logger.info(f"已清理: {json_file.name}")
                
            except Exception as e:
                error_msg = f"處理檔案 {json_file.name} 失敗: {e}"
                stats['errors'].append(error_msg)
                self.logger.error(error_msg)
        
        self.logger.info(f"表情符號清理完成: 總計 {stats['total_files']} 個檔案，"
                        f"成功處理 {stats['processed_files']} 個檔案")
        
        return stats