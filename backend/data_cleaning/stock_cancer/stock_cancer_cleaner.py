"""
股癌 Podcast 專用清理器
專門處理 Apple Podcast ID: 1500839292 的股癌節目資料

清理邏輯：
- 標題：特殊處理，移除股癌特有的標題格式、表情符號、顏文字
- 其他文本欄位（描述、內容、評論等）：使用一般清理邏輯，與其他節目相同
"""

import re
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
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


class StockCancerCleaner(BaseCleaner):
    """股癌節目專用清理器"""
    
    def __init__(self):
        """初始化股癌清理器"""
        self.longtext_cleaner = LongTextCleaner()
        self.logger = logging.getLogger(__name__)
        self.podcast_id = "1500839292"
        self.podcast_name = "股癌"
        
    def clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理股癌節目資料
        Args:
            data: 包含 episode_title 和其他欄位的字典
        Returns:
            清理後的資料字典
        """
        cleaned_data = data.copy()
        # 特殊處理標題
        if 'episode_title' in cleaned_data:
            cleaned_data['episode_title'] = self._clean_stock_cancer_title(
                cleaned_data['episode_title']
            )
        # 其他文本欄位使用一般清理
        text_fields = ['description', 'content', 'summary']
        for field in text_fields:
            if field in cleaned_data and cleaned_data[field]:
                cleaned_data[field] = self.longtext_cleaner.clean(cleaned_data[field])
        # 添加清理資訊
        cleaned_data['cleaned_at'] = datetime.now().isoformat()
        cleaned_data['cleaning_status'] = 'completed'
        cleaned_data['cleaner_type'] = 'stock_cancer_specialized'
        return cleaned_data
    
    def _is_stock_cancer_podcast(self, data: Dict[str, Any]) -> bool:
        """檢查是否為股癌 podcast"""
        # 檢查 podcast_id
        if data.get('podcast_id') == self.podcast_id:
            return True
        
        # 檢查標題是否包含股癌相關關鍵字
        title = data.get('episode_title', '').lower()
        stock_cancer_keywords = [
            '股癌', '謝孟恭', '孟恭', '股癌謝孟恭',
            'stock cancer', 'stockcancer'
        ]
        
        return any(keyword in title for keyword in stock_cancer_keywords)
    
    def _clean_stock_cancer_specific(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """股癌專用清理邏輯"""
        cleaned = data.copy()
        
        # 1. 特殊標題處理（唯一需要特殊處理的欄位）
        if 'episode_title' in cleaned:
            cleaned['episode_title'] = self._clean_stock_cancer_title(cleaned['episode_title'])
        
        # 2. 其他所有文本欄位使用一般清理邏輯
        text_fields = ['description', 'content', 'summary', 'transcript', 'text', 'comment', 'comments']
        for field in text_fields:
            if field in cleaned:
                cleaned[field] = self.longtext_cleaner.clean(cleaned[field])
        
        # 3. 檔案名稱處理（保持簡單）
        if 'file' in cleaned:
            cleaned['file'] = self._clean_stock_cancer_filename(cleaned['file'])
        
        return cleaned
    
    def _clean_stock_cancer_title(self, title: str) -> str:
        """
        強制將標題改為 EPxxx_股癌 或 股癌_未知集數
        Args:
            title: 原始標題
        Returns:
            清理後的標題
        """
        episode_number = self._extract_episode_number(title)
        if episode_number:
            return f"EP{episode_number}_股癌"
        else:
            return "股癌_未知集數"
    
    def _extract_episode_number(self, title: str) -> Optional[str]:
        """從標題中提取集數"""
        # 股癌實際使用的集數模式
        patterns = [
            r'EP(\d+)',           # EP572
            r'第(\d+)集',         # 第572集
            r'Episode\s*(\d+)',   # Episode 572
            r'Ep\.\s*(\d+)',      # Ep. 572
            r'#(\d+)',            # #572
            r'(\d+)',             # 純數字（作為備用）
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                episode_num = match.group(1)
                # 驗證是否為合理的集數（1-9999）
                if episode_num.isdigit() and 1 <= int(episode_num) <= 9999:
                    return episode_num
        
        return None
    
    def _remove_stock_cancer_title_patterns(self, title: str) -> str:
        """移除股癌特有的標題模式"""
        # 股癌特有的標題模式（基於真實 Apple Podcast 資料）
        patterns = [
            # 集數模式（股癌實際使用格式）
            r'EP\d+\s*\|',  # EP572 |
            r'EP\d+',       # EP572
            r'第\d+集',
            r'Episode\s*\d+',
            r'Ep\.\s*\d+',
            r'#\d+',
            
            # 日期模式
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
            r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',
            r'\d{1,2}月\d{1,2}日',
            r'\d{1,2}/\d{1,2}',
            r'\d+\s*天前',  # 1 天前
            r'\d+月\d+日',  # 6月28日
            
            # 股癌特有標記
            r'【股癌】',
            r'\[股癌\]',
            r'（股癌）',
            r'股癌\s*',
            r'謝孟恭\s*',
            r'孟恭\s*',
            r'Gooaye\s*',
            
            # 時間標記
            r'\d{1,2}:\d{2}',
            r'上午\d{1,2}:\d{2}',
            r'下午\d{1,2}:\d{2}',
            r'晚上\d{1,2}:\d{2}',
            r'\d+\s*分鐘',  # 51 分鐘
            
            # 其他標記
            r'直播',
            r'錄音',
            r'重播',
            r'精選',
            r'特別版',
            r'加長版',
            r'本集節目由.*贊助',  # 贊助商標記
            r'-- Hosting provided by.*',  # 託管商標記
        ]
        
        for pattern in patterns:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        
        return title
    
    def _remove_emoji_and_kaomoji(self, text: str) -> str:
        """移除表情符號和顏文字"""
        # 移除 Unicode 表情符號
        emoji_pattern = re.compile(
            "[\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "]+", flags=re.UNICODE)
        text = emoji_pattern.sub('', text)
        
        # 移除顏文字
        kaomoji_patterns = [
            r':\)', r':\(', r':D', r':P', r':p', r':o', r':O',
            r';\)', r';\(', r';D', r';P', r';p',
            r'=\)', r'=\(', r'=D', r'=P', r'=p',
            r'8\)', r'8\(', r'8D', r'8P', r'8p',
            r'B\)', r'B\(', r'BD', r'BP', r'Bp',
            r'\^_?\^', r'\^_\^', r'\^o\^', r'\^O\^',
            r'T_T', r'T\.T', r'=_=', r'\._\.',
            r'>_<', r'<_<', r'>_>',
            r'xD', r'XD', r'xd', r'xP', r'XP', r'xp',
            r'xO', r'XO', r'xo', r'x\(', r'X\(', r'x\)', r'X\)',
            r';\^\)', r':\^\)', r':\^\(', r';\^\('
        ]
        
        for pattern in kaomoji_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text
    
    def _remove_special_chars(self, text: str) -> str:
        """移除特殊字元，保留中英文和基本標點（含網址 /）"""
        allowed_chars = set(' .,!?()[]{}:;\'"#@&+=%$*-_/')
        return ''.join(c for c in text if c.isalnum() or '\u4e00' <= c <= '\u9fff' or c in allowed_chars)
    
    def _normalize_stock_cancer_title(self, title: str) -> str:
        """標準化股癌標題格式"""
        # 移除多餘空白
        title = re.sub(r'\s+', ' ', title)
        
        # 移除開頭的標點符號
        title = re.sub(r'^[^\w\u4e00-\u9fff]+', '', title)
        
        # 移除結尾的標點符號
        title = re.sub(r'[^\w\u4e00-\u9fff]+$', '', title)
        
        # 如果標題太短，添加股癌標記
        if len(title.strip()) < 5:
            title = f"股癌_{title}"
        
        return title
    

    
    def _clean_stock_cancer_filename(self, filename: str) -> str:
        """清理股癌檔案名稱"""
        if not filename:
            return ""
        
        # 移除表情符號和特殊字元
        cleaned = self._remove_emoji_and_kaomoji(filename)
        cleaned = self._remove_special_chars(cleaned)
        
        # 添加股癌標記
        if not cleaned.startswith('股癌_'):
            cleaned = f"股癌_{cleaned}"
        
        return cleaned.strip()
    

    
    def _general_clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """一般清理（非股癌資料）"""
        cleaned = data.copy()
        
        # 使用一般清理器
        if 'episode_title' in cleaned:
            cleaned['episode_title'] = self._remove_emoji_and_kaomoji(cleaned['episode_title'])
            cleaned['episode_title'] = self._remove_special_chars(cleaned['episode_title'])
        
        if 'description' in cleaned:
            cleaned['description'] = self.longtext_cleaner.clean(cleaned['description'])
        
        cleaned['cleaned_at'] = datetime.now().isoformat()
        cleaned['cleaning_status'] = 'completed'
        cleaned['cleaner_type'] = 'general'
        
        return cleaned
    
    def batch_clean_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批次清理股癌文檔
        
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
                    self.logger.info(f"已清理 {i + 1}/{len(documents)} 個股癌文檔")
                    
            except Exception as e:
                self.logger.error(f"清理第 {i + 1} 個股癌文檔失敗: {e}")
                doc['cleaning_status'] = 'error'
                doc['error_message'] = str(e)
                cleaned_docs.append(doc)
        
        return cleaned_docs
    
    def clean_stock_cancer_collection(self, collection_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """清理股癌 collection 資料"""
        try:
            self.logger.info("開始清理股癌 collection 資料")
            
            # 批次清理
            cleaned_docs = self.batch_clean_documents(collection_data)
            
            # 統計結果
            total_docs = len(cleaned_docs)
            success_count = len([doc for doc in cleaned_docs if doc.get('cleaning_status') == 'completed'])
            error_count = total_docs - success_count
            
            # 統計股癌資料
            stock_cancer_count = len([doc for doc in cleaned_docs if self._is_stock_cancer_podcast(doc)])
            
            result = {
                "collection_name": "stock_cancer_collection",
                "total_documents": total_docs,
                "stock_cancer_documents": stock_cancer_count,
                "successful_cleans": success_count,
                "failed_cleans": error_count,
                "cleaned_documents": cleaned_docs,
                "cleaning_time": datetime.now().isoformat()
            }
            
            self.logger.info(f"股癌 collection 清理完成: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"清理股癌 collection 失敗: {e}")
            return {
                "collection_name": "stock_cancer_collection",
                "status": "failed",
                "error": str(e)
            } 