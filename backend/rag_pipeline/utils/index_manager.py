"""
索引管理器
整合 podcast 標籤來優化搜索和檢索功能
"""

from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field
import pandas as pd
from pathlib import Path
import json
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class IndexEntry(BaseModel):
    """索引條目模型"""
    
    id: str = Field(description="唯一識別碼")
    title: str = Field(description="標題")
    content: str = Field(description="內容")
    tags: List[str] = Field(description="標籤列表")
    main_category: str = Field(description="主要類別")
    sub_categories: List[str] = Field(description="子類別列表")
    metadata: Dict[str, Any] = Field(description="元數據")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
class IndexManager:
    """索引管理器"""
    
    def __init__(self, tag_file: str):
        """
        初始化索引管理器
        
        Args:
            tag_file: 標籤檔案路徑
        """
        self.tag_file = Path(tag_file)
        self.entries: Dict[str, IndexEntry] = {}
        self.tag_index: Dict[str, Set[str]] = {}
        self.category_index: Dict[str, Set[str]] = {}
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words="english",
            ngram_range=(1, 2)
        )
        self.content_vectors = None
        self._load_tags()
        
    def _load_tags(self):
        """載入標籤資料"""
        try:
            # 讀取 Excel 檔案
            df = pd.read_excel(self.tag_file)
            
            # 初始化索引
            for _, row in df.iterrows():
                main_category = str(row["主要類別"])
                sub_category = str(row["子類別"])
                tags = str(row["標籤"]).split(",") if isinstance(row["標籤"], str) else []
                
                # 更新類別索引
                if main_category not in self.category_index:
                    self.category_index[main_category] = set()
                self.category_index[main_category].add(sub_category)
                
                # 更新標籤索引
                for tag in tags:
                    tag = tag.strip()
                    if tag not in self.tag_index:
                        self.tag_index[tag] = set()
                    self.tag_index[tag].add(main_category)
                    
        except Exception as e:
            print(f"載入標籤檔案時發生錯誤: {str(e)}")
            raise
            
    def add_entry(self, entry: IndexEntry):
        """
        添加索引條目
        
        Args:
            entry: 索引條目
        """
        try:
            # 更新條目
            self.entries[entry.id] = entry
            
            # 更新標籤索引
            for tag in entry.tags:
                if tag not in self.tag_index:
                    self.tag_index[tag] = set()
                self.tag_index[tag].add(entry.id)
                
            # 更新類別索引
            if entry.main_category not in self.category_index:
                self.category_index[entry.main_category] = set()
            self.category_index[entry.main_category].add(entry.id)
            
            # 更新向量
            self._update_vectors()
            
        except Exception as e:
            print(f"添加索引條目時發生錯誤: {str(e)}")
            raise
            
    def _update_vectors(self):
        """更新內容向量"""
        try:
            # 準備文本
            texts = [entry.content for entry in self.entries.values()]
            
            # 更新向量
            self.content_vectors = self.vectorizer.fit_transform(texts)
            
        except Exception as e:
            print(f"更新向量時發生錯誤: {str(e)}")
            raise
            
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        搜索內容
        
        Args:
            query: 搜索查詢
            filters: 過濾條件
            top_k: 返回結果數量
            
        Returns:
            List[Dict[str, Any]]: 搜索結果
        """
        try:
            # 轉換查詢向量
            query_vector = self.vectorizer.transform([query])
            
            # 計算相似度
            similarities = cosine_similarity(query_vector, self.content_vectors).flatten()
            
            # 獲取候選結果
            candidates = []
            for idx, similarity in enumerate(similarities):
                entry_id = list(self.entries.keys())[idx]
                entry = self.entries[entry_id]
                
                # 應用過濾條件
                if filters:
                    if not self._apply_filters(entry, filters):
                        continue
                        
                candidates.append({
                    "id": entry_id,
                    "similarity": float(similarity),
                    "entry": entry
                })
                
            # 排序並返回結果
            candidates.sort(key=lambda x: x["similarity"], reverse=True)
            return candidates[:top_k]
            
        except Exception as e:
            print(f"搜索內容時發生錯誤: {str(e)}")
            return []
            
    def _apply_filters(self, entry: IndexEntry, filters: Dict[str, Any]) -> bool:
        """
        應用過濾條件
        
        Args:
            entry: 索引條目
            filters: 過濾條件
            
        Returns:
            bool: 是否符合過濾條件
        """
        try:
            for key, value in filters.items():
                if key == "tags":
                    if not any(tag in entry.tags for tag in value):
                        return False
                elif key == "main_category":
                    if entry.main_category != value:
                        return False
                elif key == "sub_categories":
                    if not any(cat in entry.sub_categories for cat in value):
                        return False
                elif key in entry.metadata:
                    if entry.metadata[key] != value:
                        return False
            return True
            
        except Exception as e:
            print(f"應用過濾條件時發生錯誤: {str(e)}")
            return False
            
    def get_related_entries(
        self,
        entry_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        獲取相關條目
        
        Args:
            entry_id: 條目ID
            top_k: 返回結果數量
            
        Returns:
            List[Dict[str, Any]]: 相關條目列表
        """
        try:
            if entry_id not in self.entries:
                return []
                
            entry = self.entries[entry_id]
            entry_idx = list(self.entries.keys()).index(entry_id)
            
            # 計算相似度
            similarities = cosine_similarity(
                self.content_vectors[entry_idx:entry_idx+1],
                self.content_vectors
            ).flatten()
            
            # 獲取相關條目
            related = []
            for idx, similarity in enumerate(similarities):
                if idx != entry_idx:
                    related_id = list(self.entries.keys())[idx]
                    related.append({
                        "id": related_id,
                        "similarity": float(similarity),
                        "entry": self.entries[related_id]
                    })
                    
            # 排序並返回結果
            related.sort(key=lambda x: x["similarity"], reverse=True)
            return related[:top_k]
            
        except Exception as e:
            print(f"獲取相關條目時發生錯誤: {str(e)}")
            return []
            
    def get_tag_statistics(self) -> Dict[str, Any]:
        """
        獲取標籤統計資訊
        
        Returns:
            Dict[str, Any]: 統計資訊
        """
        try:
            stats = {
                "total_entries": len(self.entries),
                "tag_counts": {},
                "category_counts": {},
                "sub_category_counts": {}
            }
            
            # 統計標籤
            for entry in self.entries.values():
                for tag in entry.tags:
                    stats["tag_counts"][tag] = stats["tag_counts"].get(tag, 0) + 1
                    
                # 統計類別
                stats["category_counts"][entry.main_category] = \
                    stats["category_counts"].get(entry.main_category, 0) + 1
                    
                # 統計子類別
                for sub_category in entry.sub_categories:
                    stats["sub_category_counts"][sub_category] = \
                        stats["sub_category_counts"].get(sub_category, 0) + 1
                        
            return stats
            
        except Exception as e:
            print(f"獲取標籤統計資訊時發生錯誤: {str(e)}")
            return {}
            
    def export_index(self, output_file: str):
        """
        導出索引資料
        
        Args:
            output_file: 輸出檔案路徑
        """
        try:
            # 準備導出資料
            export_data = {
                "entries": {
                    entry_id: entry.dict()
                    for entry_id, entry in self.entries.items()
                },
                "tag_index": {
                    tag: list(entry_ids)
                    for tag, entry_ids in self.tag_index.items()
                },
                "category_index": {
                    category: list(entry_ids)
                    for category, entry_ids in self.category_index.items()
                }
            }
            
            # 寫入檔案
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"導出索引資料時發生錯誤: {str(e)}")
            raise 