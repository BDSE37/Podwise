"""
MongoDB 資料清理器
專門處理 MongoDB 文檔的清理功能
"""

import re
import logging
import sys
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


class MongoCleaner(BaseCleaner):
    """MongoDB 文檔清理器"""
    
    def __init__(self):
        """初始化 MongoDB 清理器"""
        self.longtext_cleaner = LongTextCleaner()
        self.logger = logging.getLogger(__name__)
    
    def clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理 MongoDB 文檔
        
        Args:
            data: MongoDB 文檔字典
            
        Returns:
            清理後的文檔字典
        """
        try:
            cleaned_doc = data.copy()
            
            # 清理文本欄位
            if 'text' in cleaned_doc:
                cleaned_doc['text'] = self.longtext_cleaner.clean(cleaned_doc['text'])
            
            if 'title' in cleaned_doc:
                cleaned_doc['title'] = self._clean_title(cleaned_doc['title'])
            
            # 清理檔案名稱
            if 'file' in cleaned_doc:
                cleaned_doc['file'] = self._clean_filename(cleaned_doc['file'])
            
            # 清理其他文本欄位
            text_fields = ['description', 'content', 'summary', 'transcript']
            for field in text_fields:
                if field in cleaned_doc:
                    cleaned_doc[field] = self.longtext_cleaner.clean(cleaned_doc[field])
            
            # 添加清理時間戳
            cleaned_doc['cleaned_at'] = datetime.now().isoformat()
            cleaned_doc['cleaning_status'] = 'completed'
            
            return cleaned_doc
            
        except Exception as e:
            self.logger.error(f"清理 MongoDB 文檔失敗: {e}")
            data['cleaning_status'] = 'error'
            data['error_message'] = str(e)
            return data
    
    def _clean_title(self, title: str) -> str:
        """清理標題"""
        if not title:
            return ""
        
        # 移除表情符號和特殊字元
        cleaned = re.sub(r'[^\u4e00-\u9fff\w\s\-_\.]', '', title)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _clean_filename(self, filename: str) -> str:
        """清理檔案名稱"""
        if not filename:
            return ""
        
        # 移除表情符號和特殊字元
        cleaned = re.sub(r'[^\u4e00-\u9fff\w\s\-_\.]', '', filename)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def batch_clean_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批次清理 MongoDB 文檔
        
        Args:
            documents: MongoDB 文檔列表
            
        Returns:
            清理後的文檔列表
        """
        cleaned_docs = []
        
        for i, doc in enumerate(documents):
            try:
                cleaned_doc = self.clean(doc)
                cleaned_docs.append(cleaned_doc)
                
                if (i + 1) % 100 == 0:
                    self.logger.info(f"已清理 {i + 1}/{len(documents)} 個文檔")
                    
            except Exception as e:
                self.logger.error(f"清理第 {i + 1} 個文檔失敗: {e}")
                doc['cleaning_status'] = 'error'
                doc['error_message'] = str(e)
                cleaned_docs.append(doc)
        
        return cleaned_docs
    
    def clean_collection_data(self, collection_data: List[Dict[str, Any]], 
                            collection_name: str) -> Dict[str, Any]:
        """
        清理整個 collection 的資料
        
        Args:
            collection_data: Collection 資料列表
            collection_name: Collection 名稱
            
        Returns:
            清理結果統計
        """
        try:
            self.logger.info(f"開始清理 collection: {collection_name}")
            
            # 批次清理
            cleaned_docs = self.batch_clean_documents(collection_data)
            
            # 統計結果
            total_docs = len(cleaned_docs)
            success_count = len([doc for doc in cleaned_docs if doc.get('cleaning_status') == 'completed'])
            error_count = total_docs - success_count
            
            result = {
                "collection_name": collection_name,
                "total_documents": total_docs,
                "successful_cleans": success_count,
                "failed_cleans": error_count,
                "cleaned_documents": cleaned_docs,
                "cleaning_time": datetime.now().isoformat()
            }
            
            self.logger.info(f"Collection {collection_name} 清理完成: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"清理 collection {collection_name} 失敗: {e}")
            return {
                "collection_name": collection_name,
                "status": "failed",
                "error": str(e)
            } 