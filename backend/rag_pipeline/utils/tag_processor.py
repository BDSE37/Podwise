"""
標籤處理器
用於處理 podcast 標籤分類
"""

from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field
import pandas as pd
from pathlib import Path
import json

class TagCategory(BaseModel):
    """標籤類別模型"""
    
    main_category: str = Field(description="主要類別")
    sub_categories: List[str] = Field(description="子類別列表")
    tags: List[str] = Field(description="標籤列表")
    weight: float = Field(description="權重", ge=0, le=1)
    
class TagProcessor:
    """標籤處理器"""
    
    def __init__(self, tag_file: str):
        """
        初始化標籤處理器
        
        Args:
            tag_file: 標籤檔案路徑
        """
        self.tag_file = Path(tag_file)
        self.tag_categories: Dict[str, TagCategory] = {}
        self.tag_mapping: Dict[str, str] = {}
        self._load_tags()
        
    def _load_tags(self):
        """載入標籤資料"""
        try:
            # 嘗試讀取 Excel 檔案，如果失敗則讀取 CSV
            try:
            df = pd.read_excel(self.tag_file)
            except Exception:
                # 如果 Excel 讀取失敗，嘗試讀取 CSV
                df = pd.read_csv(self.tag_file)
            
            # 處理每個類別
            for _, row in df.iterrows():
                main_category = row["主要類別"]
                sub_category = row["子類別"]
                
                # 處理標籤欄位（支援逗號分隔的多個標籤）
                tags_str = row["標籤"]
                if isinstance(tags_str, str):
                    # 分割標籤並清理
                    tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
                else:
                    tags = []
                
                weight = float(row.get("權重", 1.0))
                
                # 更新類別
                if main_category not in self.tag_categories:
                    self.tag_categories[main_category] = TagCategory(
                        main_category=main_category,
                        sub_categories=[],
                        tags=[],
                        weight=weight
                    )
                
                # 更新子類別和標籤
                category = self.tag_categories[main_category]
                if sub_category not in category.sub_categories:
                    category.sub_categories.append(sub_category)
                category.tags.extend(tags)
                
                # 更新標籤映射
                for tag in tags:
                    self.tag_mapping[tag.strip()] = main_category
                    
        except Exception as e:
            print(f"載入標籤檔案時發生錯誤: {str(e)}")
            raise
            
    def categorize_content(
        self,
        content: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分類內容
        
        Args:
            content: 內容文本
            title: 標題（可選）
            
        Returns:
            Dict[str, Any]: 分類結果
        """
        try:
            # 合併標題和內容
            text = f"{title} {content}" if title else content
            
            # 計算類別得分
            scores = {category: 0.0 for category in self.tag_categories}
            
            # 計算每個類別的得分
            for category, tag_category in self.tag_categories.items():
                # 計算標籤匹配
                for tag in tag_category.tags:
                    if tag in text:
                        scores[category] += tag_category.weight
                        
                # 計算子類別匹配
                for sub_category in tag_category.sub_categories:
                    if sub_category in text:
                        scores[category] += tag_category.weight * 0.5
                        
            # 找出得分最高的類別
            main_category = max(scores.items(), key=lambda x: x[1])[0]
            
            # 找出相關的子類別
            sub_categories = []
            for sub_category in self.tag_categories[main_category].sub_categories:
                if sub_category in text:
                    sub_categories.append(sub_category)
                    
            # 找出相關的標籤
            matched_tags = []
            for tag in self.tag_categories[main_category].tags:
                if tag in text:
                    matched_tags.append(tag)
                    
            return {
                "main_category": main_category,
                "sub_categories": sub_categories,
                "tags": matched_tags,
                "confidence": scores[main_category] / max(scores.values()) if max(scores.values()) > 0 else 0
            }
            
        except Exception as e:
            print(f"分類內容時發生錯誤: {str(e)}")
            return {}
            
    def get_category_tags(self, category: str) -> List[str]:
        """
        獲取類別的所有標籤
        
        Args:
            category: 類別名稱
            
        Returns:
            List[str]: 標籤列表
        """
        return self.tag_categories.get(category, TagCategory(
            main_category=category,
            sub_categories=[],
            tags=[],
            weight=1.0
        )).tags
        
    def get_sub_categories(self, category: str) -> List[str]:
        """
        獲取類別的所有子類別
        
        Args:
            category: 類別名稱
            
        Returns:
            List[str]: 子類別列表
        """
        return self.tag_categories.get(category, TagCategory(
            main_category=category,
            sub_categories=[],
            tags=[],
            weight=1.0
        )).sub_categories
        
    def get_tag_category(self, tag: str) -> Optional[str]:
        """
        獲取標籤所屬的類別
        
        Args:
            tag: 標籤名稱
            
        Returns:
            Optional[str]: 類別名稱
        """
        return self.tag_mapping.get(tag)
        
    def export_tags(self, output_file: str):
        """
        導出標籤資料
        
        Args:
            output_file: 輸出檔案路徑
        """
        try:
            # 準備導出資料
            export_data = {
                category: {
                    "sub_categories": cat.sub_categories,
                    "tags": cat.tags,
                    "weight": cat.weight
                }
                for category, cat in self.tag_categories.items()
            }
            
            # 寫入檔案
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"導出標籤資料時發生錯誤: {str(e)}")
            raise 