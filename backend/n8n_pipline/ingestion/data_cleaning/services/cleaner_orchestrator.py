#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import csv
import sys
from pathlib import Path
from typing import List, Any, Dict, Optional
import logging

# 添加父目錄到路徑以支援絕對導入
sys.path.append(str(Path(__file__).parent.parent.parent))

# 絕對導入所需模組
from data_cleaning.core.mongo_cleaner        import MongoCleaner
from data_cleaning.stock_cancer.stock_cancer_cleaner import StockCancerCleaner
from data_cleaning.utils.file_format_detector import FileFormatDetector
from data_cleaning.core.episode_cleaner      import EpisodeCleaner
from data_cleaning.core.podcast_cleaner      import PodcastCleaner
from data_cleaning.core.longtext_cleaner     import LongTextCleaner
from data_cleaning.core.youtube_cleaner      import YouTubeCleaner

logger = logging.getLogger(__name__)

class CleanerOrchestrator:
    """統一調用各清理模組，支援自動格式偵測與批次處理。"""

    def __init__(self):
        # 初始化各清理器實例，不創建任何目錄
        self.episode_cleaner      = EpisodeCleaner()
        self.podcast_cleaner      = PodcastCleaner()
        self.longtext_cleaner     = LongTextCleaner()
        self.mongo_cleaner        = MongoCleaner()
        self.stock_cancer_cleaner = StockCancerCleaner()

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

    def clean_file(self, file_path: str) -> Dict[str, Any]:
        """自動偵測並清理單一檔案內容，回傳清理後的資料結構。"""
        fmt = FileFormatDetector.detect_format(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            if fmt == 'json':
                data = json.load(f)
            elif fmt == 'csv':
                reader = csv.DictReader(f)
                data = list(reader)
            elif fmt == 'text':
                data = f.read()
            else:
                raise ValueError(f"Unsupported format: {fmt}")

        if fmt == 'json':
            if isinstance(data, list):
                return self._clean_list(data)
            else:
                return self._clean_single(data)
        elif fmt == 'csv':
            return self._clean_list(data)
        elif fmt == 'text':
            return self.longtext_cleaner.clean_text(data)

    def batch_clean_folder(self, input_folder: str, output_folder: str) -> List[str]:
        """遞迴掃描並清理資料夾下所有支援的檔案，回傳所有清理後的檔案路徑。"""
        # 確保輸出資料夾已存在
        os.makedirs(output_folder, exist_ok=True)

        cleaned_paths: List[str] = []
        for root, _, files in os.walk(input_folder):
            rel_root = os.path.relpath(root, input_folder)
            target_root = os.path.join(output_folder, rel_root)
            os.makedirs(target_root, exist_ok=True)

            for fn in files:
                src = os.path.join(root, fn)
                try:
                    cleaned = self.clean_file(src)
                    # 輸出檔案
                    ext = os.path.splitext(fn)[1].lower()
                    out_fn = fn
                    out_path = os.path.join(target_root, out_fn)
                    if isinstance(cleaned, (dict, list)):
                        with open(out_path, 'w', encoding='utf-8') as fw:
                            json.dump(cleaned, fw, ensure_ascii=False, indent=2)
                    else:
                        with open(out_path, 'w', encoding='utf-8') as fw:
                            fw.write(cleaned)
                    cleaned_paths.append(out_path)
                except Exception as e:
                    logger.warning(f"Skip {src}: {e}")
        return cleaned_paths

    def _clean_single(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        if self._is_youtube_data_single(doc):
            return self.youtube_cleaner.clean_document(doc)
        elif self._is_stock_cancer_data(doc):
            return self.stock_cancer_cleaner.clean_document(doc)
        elif 'episode_title' in doc:
            return self.episode_cleaner.clean_document(doc)
        elif 'podcast_title' in doc:
            return self.podcast_cleaner.clean_document(doc)
        else:
            return self.longtext_cleaner.clean_document(doc)

    def _clean_list(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self._clean_single(doc) for doc in data_list]

    def _is_youtube_data_single(self, doc: Dict[str, Any]) -> bool:
        youtube_fields = ['video_id', 'channel_title', 'description']
        if all(f in doc for f in youtube_fields):
            return True
        url = doc.get('url', '').lower()
        if 'youtube.com' in url or 'youtu.be' in url:
            return True
        title = doc.get('title', doc.get('episode_title', '')).lower()
        youtube_keywords = ['觀看次數', '訂閱', '按讚', '分享', '留言', 'youtube', 'yt']
        return any(k in title for k in youtube_keywords)

    def _is_stock_cancer_data(self, data_list: Any) -> bool:
        if not isinstance(data_list, list):
            return False
        sample = data_list[:5]
        for doc in sample:
            if doc.get('podcast_id') == '1500839292':
                return True
            title = doc.get('episode_title', '').lower()
            keywords = ['股癌', '謝孟恭', 'stock cancer']
            if any(k in title for k in keywords):
                return True
        return False
