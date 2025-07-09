import os
import json
import csv
import sys
from pathlib import Path
from typing import List, Any, Dict, Optional
import logging

# 添加父目錄到路徑以支援絕對導入
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from data_cleaning.core.mongo_cleaner import MongoCleaner
    from data_cleaning.core.stock_cancer_cleaner import StockCancerCleaner
    from data_cleaning.utils.file_format_detector import FileFormatDetector
except ImportError:
    # Fallback: 相對導入
    from core.mongo_cleaner import MongoCleaner
    from core.stock_cancer_cleaner import StockCancerCleaner
    from utils.file_format_detector import FileFormatDetector

logger = logging.getLogger(__name__)

from core.episode_cleaner import EpisodeCleaner
from core.podcast_cleaner import PodcastCleaner
from core.longtext_cleaner import LongTextCleaner
from core.youtube_cleaner import YouTubeCleaner

class CleanerOrchestrator:
    """統一調用各清理模組，支援自動格式偵測與批次處理。"""
    def __init__(self, output_dir: str = '../../data/cleaned_data'):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.episode_cleaner = EpisodeCleaner()
        self.podcast_cleaner = PodcastCleaner()
        self.longtext_cleaner = LongTextCleaner()
        self.mongo_cleaner = MongoCleaner()
        self.stock_cancer_cleaner = StockCancerCleaner()
        
        # 配置 YouTube 清理器，啟用檔案名稱清理
        youtube_config = {
            "fields_to_clean": {
                "filename": {
                    "enabled": True,
                    "clean_type": "filename",
                    "description": "清理檔案名稱，使用與內文相同的清理邏輯"
                }
            }
        }
        self.youtube_cleaner = YouTubeCleaner(youtube_config)

    def clean_file(self, file_path: str) -> str:
        """自動偵測格式並清理單一檔案，回傳輸出檔案路徑。"""
        fmt = FileFormatDetector.detect_format(file_path)
        basename = os.path.basename(file_path)
        
        # 檢查是否為 YouTube 資料，如果是則使用 YouTube 清理器的檔案清理功能
        if fmt == 'json':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 檢查是否為 YouTube 資料
                if self._is_youtube_data_single(data):
                    # 使用 YouTube 清理器的檔案清理功能
                    cleaned_file_path = self.youtube_cleaner.clean_file(file_path)
                    # 移動到輸出目錄
                    output_path = os.path.join(self.output_dir, os.path.basename(cleaned_file_path))
                    if cleaned_file_path != output_path:
                        import shutil
                        shutil.move(cleaned_file_path, output_path)
                    return output_path
                else:
                    # 使用一般 JSON 清理
                    cleaned = self._clean_json_data(data, basename)
                    output_path = os.path.join(self.output_dir, f"{basename}")
            except Exception as e:
                logger.error(f"處理 JSON 檔案失敗: {e}")
                # 如果解析失敗，使用一般清理
                cleaned = self._clean_json_data({}, basename)
                output_path = os.path.join(self.output_dir, f"{basename}")
        elif fmt == 'csv':
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
            cleaned = self.episode_cleaner.batch_clean(data)
            output_path = os.path.join(self.output_dir, f"{basename}")
        else:  # txt or long text
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            cleaned = self.longtext_cleaner.clean(text)
            output_path = os.path.join(self.output_dir, f"{basename}")
        
        # 檢查是否為 MongoDB 資料格式
        if isinstance(cleaned, list) and cleaned and isinstance(cleaned[0], dict):
            # 檢查是否包含 MongoDB 特有欄位
            mongo_fields = ['_id', 'text', 'file', 'created', 'episode_number']
            if any(field in cleaned[0] for field in mongo_fields):
                # 先檢查是否為股癌資料
                if self._contains_stock_cancer_data(cleaned):
                    cleaned = self.stock_cancer_cleaner.batch_clean_documents(cleaned)
                # 檢查是否為 YouTube 資料
                elif self._contains_youtube_data(cleaned):
                    cleaned = self.youtube_cleaner.batch_clean_documents(cleaned)
                else:
                    cleaned = self.mongo_cleaner.batch_clean_documents(cleaned)
        
        # 寫入清理後的檔案
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=2)
        return output_path

    def _is_youtube_data_single(self, data: Dict[str, Any]) -> bool:
        """檢查單一資料是否為 YouTube 資料"""
        if not isinstance(data, dict):
            return False
        
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

    def _clean_json_data(self, data: Any, basename: str) -> Any:
        """根據檔名自動選擇清理器。"""
        if isinstance(data, list):
            if 'episode' in basename.lower():
                return self.episode_cleaner.batch_clean(data)
            if 'podcast' in basename.lower():
                return self.podcast_cleaner.batch_clean(data)
            # 對於一般列表，假設每個項目都是字典或字串
            cleaned_items = []
            for item in data:
                if isinstance(item, dict):
                    # 如果是字典，檢查是否包含文本欄位
                    cleaned_item = {}
                    for key, value in item.items():
                        if isinstance(value, str):
                            cleaned_item[key] = self.longtext_cleaner.clean(value)
                        else:
                            cleaned_item[key] = value
                    cleaned_items.append(cleaned_item)
                else:
                    cleaned_items.append(self.longtext_cleaner.clean(str(item)))
            return cleaned_items
        if isinstance(data, dict):
            if 'episode' in basename.lower():
                return self.episode_cleaner.clean(data)
            if 'podcast' in basename.lower():
                return self.podcast_cleaner.clean(data)
            # 對於一般字典，清理所有字串欄位
            cleaned_dict = {}
            for key, value in data.items():
                if isinstance(value, str):
                    cleaned_dict[key] = self.longtext_cleaner.clean(value)
                else:
                    cleaned_dict[key] = value
            return cleaned_dict
        if isinstance(data, str):
            return self.longtext_cleaner.clean(data)
        return data

    def batch_clean_files(self, file_paths: List[str]) -> List[str]:
        """批次清理多個檔案，回傳所有輸出檔案路徑。"""
        return [self.clean_file(fp) for fp in file_paths]
    
    def _contains_stock_cancer_data(self, data_list: List[Dict[str, Any]]) -> bool:
        """檢查資料列表中是否包含股癌資料"""
        if not data_list:
            return False
        
        # 檢查前幾個文檔
        sample_size = min(5, len(data_list))
        for i in range(sample_size):
            doc = data_list[i]
            
            # 檢查 podcast_id
            if doc.get('podcast_id') == '1500839292':
                return True
            
            # 檢查標題是否包含股癌關鍵字
            title = doc.get('episode_title', '').lower()
            stock_cancer_keywords = ['股癌', '謝孟恭', '孟恭', 'stock cancer']
            if any(keyword in title for keyword in stock_cancer_keywords):
                return True
        
        return False
    
    def _contains_youtube_data(self, data_list: List[Dict[str, Any]]) -> bool:
        """檢查資料列表中是否包含 YouTube 資料"""
        if not data_list:
            return False
        
        # 檢查前幾個文檔
        sample_size = min(5, len(data_list))
        for i in range(sample_size):
            doc = data_list[i]
            
            # 檢查是否有 YouTube 特有的欄位結構
            youtube_fields = ['view_count', 'like_count', 'comment_count', 'comments']
            if all(field in doc for field in youtube_fields):
                return True
            
            # 檢查 URL 是否包含 YouTube 相關關鍵字
            url = doc.get('url', '').lower()
            if 'youtube.com' in url or 'youtu.be' in url:
                return True
            
            # 檢查標題是否包含 YouTube 特有標記
            title = doc.get('title', doc.get('episode_title', '')).lower()
            youtube_keywords = ['觀看次數', '訂閱', '按讚', '分享', '留言', 'youtube', 'yt']
            if any(keyword in title for keyword in youtube_keywords):
                return True
        
        return False 