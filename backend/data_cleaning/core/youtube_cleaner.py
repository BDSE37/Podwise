"""
通用 YouTube 清理器
專門處理任何 YouTube 頻道的資料

清理邏輯：
- 標題：移除表情符號、特殊符號、YouTube 特有標記
- 作者：清理頻道名稱，移除官方標記
- 觀看次數、按讚數、評論數：標準化數字格式
- 評論：清理評論內容
- 檔案名稱：使用與內文相同的清理邏輯
- 針對 YouTube 資料格式進行優化
- 支援自定義欄位清理配置
"""

import re
import sys
import logging
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

# 添加父目錄到路徑以支援絕對導入
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from data_cleaning.core.base_cleaner import BaseCleaner
    from data_cleaning.core.longtext_cleaner import LongTextCleaner
except ImportError:
    # Fallback: 相對導入
    from core.base_cleaner import BaseCleaner
    from core.longtext_cleaner import LongTextCleaner


class YouTubeCleaner(BaseCleaner):
    """通用 YouTube 清理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 YouTube 清理器
        
        Args:
            config: 清理配置字典，包含以下選項：
                - fields_to_clean: 需要清理的欄位列表
                - title_clean_rules: 標題清理規則
                - author_clean_rules: 作者清理規則
                - number_clean_rules: 數字欄位清理規則
                - comment_clean_rules: 評論清理規則
                - filename_clean_rules: 檔案名稱清理規則
        """
        self.longtext_cleaner = LongTextCleaner()
        self.logger = logging.getLogger(__name__)
        
        # 預設配置
        self.default_config = {
            "fields_to_clean": {
                "title": {
                    "enabled": True,
                    "clean_type": "title",
                    "description": "清理標題，移除表情符號和特殊標記"
                },
                "author": {
                    "enabled": True,
                    "clean_type": "author",
                    "description": "清理作者欄位，移除官方標記"
                },
                "view_count": {
                    "enabled": True,
                    "clean_type": "number",
                    "description": "清理觀看次數，標準化為數字"
                },
                "like_count": {
                    "enabled": True,
                    "clean_type": "number",
                    "description": "清理按讚數，標準化為數字"
                },
                "comment_count": {
                    "enabled": True,
                    "clean_type": "number",
                    "description": "清理評論數，標準化為整數"
                },
                "comments": {
                    "enabled": True,
                    "clean_type": "list",
                    "description": "清理評論列表"
                },
                "description": {
                    "enabled": False,
                    "clean_type": "text",
                    "description": "清理描述欄位"
                },
                "content": {
                    "enabled": False,
                    "clean_type": "text",
                    "description": "清理內容欄位"
                },
                "summary": {
                    "enabled": False,
                    "clean_type": "text",
                    "description": "清理摘要欄位"
                },
                "filename": {
                    "enabled": False,
                    "clean_type": "filename",
                    "description": "清理檔案名稱，使用與內文相同的清理邏輯"
                }
            },
            "title_clean_rules": {
                "remove_emoji": True,
                "remove_special_symbols": True,
                "remove_youtube_patterns": True,
                "normalize_format": True
            },
            "author_clean_rules": {
                "remove_official_tags": True,
                "remove_special_symbols": True
            },
            "number_clean_rules": {
                "remove_prefixes": ["觀看次數：", "讚數：", "留言數："],
                "remove_suffixes": ["次", "個", "萬", "千"],
                "extract_numbers_only": True
            },
            "comment_clean_rules": {
                "remove_emoji": True,
                "remove_special_symbols": True,
                "normalize_text": True
            },
            "filename_clean_rules": {
                "remove_emoji": True,
                "remove_special_symbols": True,
                "remove_youtube_patterns": True,
                "remove_invalid_chars": True,
                "normalize_format": True,
                "max_length": 100,
                "replace_spaces": True,
                "allowed_extensions": [".json", ".txt", ".csv"]
            }
        }
        
        # 合併自定義配置
        self.config = self._merge_config(self.default_config, config or {})
        
    def _merge_config(self, default: Dict[str, Any], custom: Dict[str, Any]) -> Dict[str, Any]:
        """合併預設配置和自定義配置"""
        merged = default.copy()
        
        # 合併欄位配置
        if "fields_to_clean" in custom:
            for field, field_config in custom["fields_to_clean"].items():
                if field in merged["fields_to_clean"]:
                    merged["fields_to_clean"][field].update(field_config)
                else:
                    merged["fields_to_clean"][field] = field_config
        
        # 合併清理規則
        for rule_type in ["title_clean_rules", "author_clean_rules", "number_clean_rules", "comment_clean_rules", "filename_clean_rules"]:
            if rule_type in custom:
                merged[rule_type].update(custom[rule_type])
        
        return merged
        
    def clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理 YouTube 資料
        Args:
            data: 包含各種欄位的字典
        Returns:
            清理後的資料字典
        """
        cleaned_data = data.copy()
        
        # 根據配置清理各個欄位
        for field_name, field_config in self.config["fields_to_clean"].items():
            if not field_config.get("enabled", True):
                continue
                
            if field_name in cleaned_data:
                clean_type = field_config.get("clean_type", "text")
                
                if clean_type == "title":
                    cleaned_data[field_name] = self._clean_youtube_title(cleaned_data[field_name])
                elif clean_type == "author":
                    cleaned_data[field_name] = self._clean_author(cleaned_data[field_name])
                elif clean_type == "number":
                    cleaned_data[field_name] = self._clean_number_field(cleaned_data[field_name])
                elif clean_type == "list":
                    cleaned_data[field_name] = self._clean_list_field(cleaned_data[field_name])
                elif clean_type == "filename":
                    cleaned_data[field_name] = self._clean_filename(cleaned_data[field_name])
                elif clean_type == "text":
                    cleaned_data[field_name] = self.longtext_cleaner.clean(cleaned_data[field_name])
        
        return cleaned_data
    
    def _clean_filename(self, filename: str) -> str:
        """
        清理檔案名稱，使用與內文相同的清理邏輯
        Args:
            filename: 原始檔案名稱
        Returns:
            清理後的檔案名稱
        """
        if not filename:
            return ""
        
        rules = self.config["filename_clean_rules"]
        
        # 分離檔案名稱和副檔名
        name, ext = os.path.splitext(filename)
        
        # 使用與標題相同的清理邏輯
        # 1. 移除表情符號
        if rules.get("remove_emoji"):
            name = self._remove_emoji_and_symbols(name)
        
        # 2. 移除特殊符號
        if rules.get("remove_special_symbols"):
            # 只保留字母、數字、中文和基本符號
            allowed_chars = set(' -_.()[]{}')
            name = ''.join(c for c in name if c.isalnum() or '\u4e00' <= c <= '\u9fff' or c in allowed_chars)
        
        # 3. 移除 YouTube 特有模式（與標題清理相同）
        if rules.get("remove_youtube_patterns"):
            name = self._remove_youtube_title_patterns(name)
        
        # 4. 移除檔案系統不允許的字元
        if rules.get("remove_invalid_chars"):
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                name = name.replace(char, '')
        
        # 5. 標準化格式（與標題清理相同）
        if rules.get("normalize_format"):
            name = self._normalize_youtube_title(name)
        
        # 6. 替換空白
        if rules.get("replace_spaces"):
            name = name.replace(' ', '_')
        
        # 7. 限制長度
        max_length = rules.get("max_length", 100)
        if len(name) > max_length:
            name = name[:max_length]
        
        # 8. 確保檔案名稱不為空
        if not name:
            name = "cleaned_file"
        
        # 9. 檢查副檔名是否允許
        allowed_extensions = rules.get("allowed_extensions", [".json", ".txt", ".csv"])
        if ext.lower() not in [ext.lower() for ext in allowed_extensions]:
            ext = ".json"  # 預設使用 .json
        
        return name + ext
    
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
            # 讀取原始檔案
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 清理資料
            cleaned_data = self.clean(data)
            
            # 處理檔案名稱
            original_path = Path(file_path)
            original_name = original_path.name
            
            # 如果啟用了檔案名稱清理
            if self.config["fields_to_clean"].get("filename", {}).get("enabled", False):
                cleaned_name = self._clean_filename(original_name)
            else:
                cleaned_name = original_name
            
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
                    if self.config["fields_to_clean"].get("filename", {}).get("enabled", False):
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
    
    def _clean_number_field(self, value: Any) -> str:
        """清理數字欄位"""
        if not value:
            return "0"
        
        value_str = str(value)
        rules = self.config["number_clean_rules"]
        
        # 移除前綴
        if rules.get("remove_prefixes"):
            for prefix in rules["remove_prefixes"]:
                value_str = value_str.replace(prefix, "")
        
        # 移除後綴
        if rules.get("remove_suffixes"):
            for suffix in rules["remove_suffixes"]:
                value_str = value_str.replace(suffix, "")
        
        # 只保留數字
        if rules.get("extract_numbers_only"):
            value_str = re.sub(r'[^\d]', '', value_str)
        
        return value_str if value_str else "0"
    
    def _clean_list_field(self, value: Any) -> List[str]:
        """清理列表欄位（如評論）"""
        if not isinstance(value, list):
            return []
        
        rules = self.config["comment_clean_rules"]
        cleaned_list = []
        
        for item in value:
            if isinstance(item, str):
                cleaned_item = item
                
                # 移除表情符號
                if rules.get("remove_emoji"):
                    cleaned_item = self._remove_emoji_and_symbols(cleaned_item)
                
                # 移除特殊符號
                if rules.get("remove_special_symbols"):
                    allowed_chars = set(' .,!?()[]{}:;\'"#@&+=%$*-_/')
                    cleaned_item = ''.join(c for c in cleaned_item if c.isalnum() or '\u4e00' <= c <= '\u9fff' or c in allowed_chars)
                
                # 標準化文本
                if rules.get("normalize_text"):
                    cleaned_item = re.sub(r'\s+', ' ', cleaned_item).strip()
                
                cleaned_list.append(cleaned_item)
            else:
                cleaned_list.append(str(item))
        
        return cleaned_list
    
    def _is_youtube_data(self, data: Dict[str, Any]) -> bool:
        """檢查是否為 YouTube 資料"""
        # 檢查是否有 YouTube 特有的欄位結構
        youtube_fields = ['view_count', 'like_count', 'comment_count', 'comments']
        if all(field in data for field in youtube_fields):
            return True
        
        # 檢查 URL 是否包含 YouTube 相關關鍵字
        url = data.get('url', '').lower()
        if 'youtube.com' in url or 'youtu.be' in url:
            return True
        
        # 檢查標題是否包含 YouTube 特有標記
        title = data.get('title', '').lower()
        youtube_keywords = ['觀看次數', '訂閱', '按讚', '分享', '留言', 'youtube', 'yt']
        if any(keyword in title for keyword in youtube_keywords):
            return True
        
        return False
    
    def _clean_youtube_title(self, title: str) -> str:
        """
        清理 YouTube 標題
        Args:
            title: 原始標題
        Returns:
            清理後的標題
        """
        if not title:
            return ""
        
        rules = self.config["title_clean_rules"]
        
        # 移除表情符號和特殊符號
        if rules.get("remove_emoji"):
            title = self._remove_emoji_and_symbols(title)
        
        # 移除 YouTube 特有的標題模式
        if rules.get("remove_youtube_patterns"):
            title = self._remove_youtube_title_patterns(title)
        
        # 標準化標題格式
        if rules.get("normalize_format"):
            title = self._normalize_youtube_title(title)
        
        return title
    
    def _remove_emoji_and_symbols(self, text: str) -> str:
        """移除表情符號和特殊符號"""
        # 移除 Unicode 表情符號
        emoji_pattern = re.compile(
            "[\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U0001F900-\U0001F9FF"  # supplemental symbols
            "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
            "]+", flags=re.UNICODE)
        text = emoji_pattern.sub('', text)
        
        # 移除特殊符號（保留中文、英文、數字和基本標點，包括 URL 相關字元）
        allowed_chars = set(' .,!?()[]{}:;\'"#@&+=%$*-_/')
        text = ''.join(c for c in text if c.isalnum() or '\u4e00' <= c <= '\u9fff' or c in allowed_chars)
        
        return text
    
    def _remove_youtube_title_patterns(self, title: str) -> str:
        """移除 YouTube 特有的標題模式"""
        # YouTube 頻道特有的標題模式
        patterns = [
            # 表情符號和特殊符號
            r'🚩', r'🎯', r'💡', r'🔥', r'⭐', r'🌟', r'✨', r'💎', r'🏆', r'🎉',
            r'📚', r'📖', r'📝', r'📋', r'📌', r'📍', r'🎪', r'🎭', r'🎨', r'🎬',
            r'🎤', r'🎧', r'🎵', r'🎶', r'🎹', r'🎸', r'🎺', r'🎻', r'🥁', r'🎷',
            r'🏠', r'🏡', r'🏢', r'🏣', r'🏤', r'🏥', r'🏦', r'🏨', r'🏩', r'🏪',
            r'🏫', r'🏬', r'🏭', r'🏯', r'🏰', r'💒', r'🗼', r'🗽', r'⛪', r'🕌',
            r'🛕', r'⛩️', r'🕍', r'⛪', r'🛐', r'📿', r'💎', r'🔮', r'🔯', r'🕉️',
            
            # YouTube 特有標記
            r'【.*?】',  # 【吳淡如Ｘ林香蘭】
            r'\[.*?\]',  # [吳淡如Ｘ林香蘭]
            r'（.*?）',  # （吳淡如Ｘ林香蘭）
            r'\(.*?\)',  # (吳淡如Ｘ林香蘭)
            
            # 分隔符號
            r'Ｘ', r'X', r'x',  # 交叉符號
            r'｜', r'|',  # 分隔線
            r'•', r'·', r'·',  # 點號
            r'→', r'←', r'↑', r'↓',  # 箭頭
            r'⇒', r'⇐', r'⇑', r'⇓',  # 雙箭頭
            
            # 數字和單位
            r'\d+次',  # 觀看次數
            r'\d+個',  # 個數
            r'\d+個讚',  # 讚數
            r'\d+個留言',  # 留言數
            
            # 時間標記
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
            r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',
            r'\d{1,2}月\d{1,2}日',
            r'\d{1,2}:\d{2}',
            
            # 其他標記
            r'官方', r'唯一', r'頻道', r'Official',
            r'訂閱', r'按讚', r'分享', r'留言',
            r'觀看次數', r'讚數', r'留言數',
            r'新影片', r'最新', r'熱門', r'推薦',
        ]
        
        for pattern in patterns:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        
        return title
    
    def _normalize_youtube_title(self, title: str) -> str:
        """標準化 YouTube 標題格式"""
        # 移除多餘空白
        title = re.sub(r'\s+', ' ', title)
        
        # 移除開頭的標點符號
        title = re.sub(r'^[^\w\u4e00-\u9fff]+', '', title)
        
        # 移除結尾的標點符號
        title = re.sub(r'[^\w\u4e00-\u9fff]+$', '', title)
        
        return title.strip()
    
    def _clean_author(self, author: str) -> str:
        """清理作者欄位"""
        if not author:
            return ""
        
        rules = self.config["author_clean_rules"]
        
        # 移除特殊符號和標記
        if rules.get("remove_special_symbols"):
            author = self._remove_emoji_and_symbols(author)
        
        # 移除多餘的標記
        if rules.get("remove_official_tags"):
            patterns = [
                r'（Official官方唯一頻道）',
                r'\(Official官方唯一頻道\)',
                r'【Official官方唯一頻道】',
                r'\[Official官方唯一頻道\]',
                r'Official官方唯一頻道',
                r'官方唯一頻道',
                r'官方頻道',
                r'唯一頻道',
                r'（Official）',
                r'\(Official\)',
                r'【Official】',
                r'\[Official\]',
                r'Official',
            ]
            
            for pattern in patterns:
                author = re.sub(pattern, '', author, flags=re.IGNORECASE)
        
        return author.strip()
    
    def get_config(self) -> Dict[str, Any]:
        """取得當前配置"""
        return self.config.copy()
    
    def update_config(self, new_config: Dict[str, Any]):
        """更新配置"""
        self.config = self._merge_config(self.config, new_config)
    
    def add_custom_field(self, field_name: str, field_config: Dict[str, Any]):
        """添加自定義欄位"""
        self.config["fields_to_clean"][field_name] = field_config
    
    def remove_field(self, field_name: str):
        """移除欄位"""
        if field_name in self.config["fields_to_clean"]:
            del self.config["fields_to_clean"][field_name]
    
    def batch_clean_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批次清理 YouTube 文檔
        
        Args:
            documents: 文檔列表
            
        Returns:
            清理後的文檔列表
        """
        cleaned_docs = []
        
        for i, doc in enumerate(documents):
            try:
                cleaned_doc = self.clean(doc)
                cleaned_docs.append(cleaned_doc)
                
                if (i + 1) % 100 == 0:
                    self.logger.info(f"已清理 {i + 1}/{len(documents)} 個 YouTube 文檔")
                    
            except Exception as e:
                self.logger.error(f"清理第 {i + 1} 個 YouTube 文檔失敗: {e}")
                # 保留原始文檔，不添加清理狀態資訊
                cleaned_docs.append(doc)
        
        return cleaned_docs
    
    def clean_youtube_collection(self, collection_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """清理 YouTube collection 資料"""
        try:
            self.logger.info("開始清理 YouTube collection 資料")
            
            # 批次清理
            cleaned_docs = self.batch_clean_documents(collection_data)
            
            # 只返回清理後的文檔列表
            result = {
                "cleaned_documents": cleaned_docs
            }
            
            self.logger.info(f"YouTube collection 清理完成，共清理 {len(cleaned_docs)} 個文檔")
            return result
            
        except Exception as e:
            self.logger.error(f"清理 YouTube collection 失敗: {e}")
            return {
                "status": "failed",
                "error": str(e)
            } 