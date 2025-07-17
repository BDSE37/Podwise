import re
import sys
from pathlib import Path
from typing import Dict, Any

# 添加父目錄到路徑以支援絕對導入
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from data_cleaning.core.base_cleaner import BaseCleaner
except ImportError:
    # Fallback: 相對導入
    from core.base_cleaner import BaseCleaner

class EpisodeCleaner(BaseCleaner):
    """Episode 資料清理器。"""

    def clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清理 Episode 資料。"""
        cleaned_data = data.copy()
        
        # 清理文本欄位
        text_fields = ['episode_title', 'description', 'content', 'summary']
        for field in text_fields:
            if field in cleaned_data and cleaned_data[field]:
                cleaned_data[field] = self._clean_text(cleaned_data[field])
        
        return cleaned_data

    def _clean_text(self, text: str) -> str:
        """清理文本內容。"""
        if not text:
            return ""
        
        text = self._remove_emoji(text)
        text = self._remove_kaomoji(text)
        text = self._remove_special_chars(text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def _remove_emoji(self, text: str) -> str:
        """移除表情符號。"""
        emoji_pattern = re.compile(
            "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub('', text)

    def _remove_kaomoji(self, text: str) -> str:
        """移除顏文字。"""
        kaomoji_patterns = [
            r':\)', r':\(', r':D', r':P', r':p', r':o', r':O',
            r'=\)', r'=\(', r'=D', r'=P', r'=p',
            r'^_^', r'^o^', r'^O^', r'T_T', r'T.T', r'=_=',
            r'._.', r'>_<', r'<_<', r'>_>', r'xD', r'XD'
        ]
        for pattern in kaomoji_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        return text

    def _remove_special_chars(self, text: str) -> str:
        """移除特殊字元，保留中英文和基本標點，包括 URL 相關字元。"""
        allowed = set(' .,!?()[]{}:;\'"#@&+=%$*-_/')
        return ''.join(c for c in text if c.isalnum() or '\u4e00' <= c <= '\u9fff' or c in allowed) 