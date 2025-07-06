import re
import sys
from pathlib import Path
from typing import Any

# 添加父目錄到路徑以支援絕對導入
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from data_cleaning.core.base_cleaner import BaseCleaner
except ImportError:
    # Fallback: 相對導入
    from core.base_cleaner import BaseCleaner

class LongTextCleaner(BaseCleaner):
    """長文本（如 MongoDB RSS）清理器。"""

    def clean(self, data: Any) -> str:
        """清理長文本內容。"""
        if not isinstance(data, str):
            return ""
        text = self._remove_kaomoji(data)
        text = self._remove_emoji(text)
        text = self._remove_html_tags(text)
        text = self._remove_special_chars(text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _remove_emoji(self, text: str) -> str:
        emoji_pattern = re.compile(
            "[\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "]+", flags=re.UNICODE)
        return emoji_pattern.sub('', text)

    def _remove_kaomoji(self, text: str) -> str:
        kaomoji_patterns = [
            r':\)', r':\(', r':D', r':P', r':p', r':o', r':O', r';\)', r';\(', r';D', r';P', r';p',
            r'=\)', r'=\(', r'=D', r'=P', r'=p', r'8\)', r'8\(', r'8D', r'8P', r'8p', r'B\)', r'B\(',
            r'BD', r'BP', r'Bp', r'\^_?\^', r'\^_\^', r'\^o\^', r'\^O\^', r'T_T', r'T\.T', r'=_=',
            r'\._\.', r'>_<', r'<_<', r'>_>', r'xD', r'XD', r'xd', r'xP', r'XP', r'xp', r'xO', r'XO',
            r'x\(', r'X\(', r'x\)', r'X\)', r';\^\)', r':\^\)', r':\^\(', r';\^\('
        ]
        for pattern in kaomoji_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        return text

    def _remove_html_tags(self, text: str) -> str:
        return re.sub(r'<[^>]+>', '', text)

    def _remove_special_chars(self, text: str) -> str:
        allowed = set(' .,!?()[]{}:;\'"#@&+=%$*-_')
        return ''.join(c for c in text if c.isalnum() or '\u4e00' <= c <= '\u9fff' or c in allowed) 