"""
內容處理器
用於處理教育、商業類別的資料，並生成摘要
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import json
import os
from pathlib import Path

# 從 core 模組導入已定義的模型
from ..core.content_models import ContentCategory, ContentMetadata, ContentSummary
    
class ContentProcessor:
    """內容處理器"""
    
    def __init__(self, data_dir: str):
        """
        初始化內容處理器
        
        Args:
            data_dir: 資料目錄路徑
        """
        self.data_dir = Path(data_dir)
        self.categories = {
            "教育": ["自我成長", "學習方法", "職涯發展"],
            "商業": ["股票", "投資理財", "市場分析"]
        }
        
    def load_dcard_data(self) -> List[Dict[str, Any]]:
        """
        載入 Dcard 資料
        
        Returns:
            List[Dict[str, Any]]: 處理後的資料列表
        """
        processed_data = []
        
        # 遍歷資料目錄
        for file_path in self.data_dir.glob("**/*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                # 處理每篇文章
                for post in data:
                    processed_post = self._process_post(post)
                    if processed_post:
                        processed_data.append(processed_post)
                        
            except Exception as e:
                print(f"處理文件 {file_path} 時發生錯誤: {str(e)}")
                continue
                
        return processed_data
        
    def _process_post(self, post: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        處理單篇文章
        
        Args:
            post: 原始文章資料
            
        Returns:
            Optional[Dict[str, Any]]: 處理後的文章資料
        """
        try:
            # 提取基本資訊
            title = post.get("title", "")
            content = post.get("content", "")
            author = post.get("author", "")
            publish_date = post.get("created_at", "")
            
            # 分類內容
            category = self._categorize_content(title, content)
            
            # 生成摘要
            summary = self._generate_summary(content, category)
            
            # 建立元數據
            metadata = ContentMetadata(
                title=title,
                author=author,
                publish_date=datetime.fromisoformat(publish_date),
                category=category,
                source="Dcard",
                url=post.get("url")
            )
            
            return {
                "metadata": metadata.dict(),
                "content": content,
                "summary": summary.dict()
            }
            
        except Exception as e:
            print(f"處理文章時發生錯誤: {str(e)}")
            return None
            
    def _categorize_content(self, title: str, content: str) -> ContentCategory:
        """
        分類內容
        
        Args:
            title: 文章標題
            content: 文章內容
            
        Returns:
            ContentCategory: 內容類別
        """
        # 關鍵字匹配
        keywords = {
            "教育": ["學習", "成長", "教育", "課程", "知識"],
            "商業": ["股票", "投資", "理財", "市場", "交易"],
            "自我成長": ["自我提升", "目標", "習慣", "時間管理"],
            "股票": ["股價", "技術分析", "基本面", "交易策略"]
        }
        
        # 計算類別得分
        scores = {
            "教育": 0,
            "商業": 0,
            "自我成長": 0,
            "股票": 0
        }
        
        # 分析標題和內容
        text = f"{title} {content}"
        for category, words in keywords.items():
            for word in words:
                if word in text:
                    if category in ["教育", "商業"]:
                        scores[category] += 2
                    else:
                        scores[category] += 1
                        
        # 確定主要類別
        main_category = max(scores.items(), key=lambda x: x[1])[0]
        
        # 確定子類別
        if main_category == "教育":
            sub_category = "自我成長" if scores["自我成長"] > 0 else "其他"
        else:
            sub_category = "股票" if scores["股票"] > 0 else "其他"
            
        # 生成標籤
        tags = []
        for category, score in scores.items():
            if score > 0 and category not in [main_category, sub_category]:
                tags.append(category)
                
        return ContentCategory(
            main_category=main_category,
            sub_category=sub_category,
            tags=tags
        )
        
    def _generate_summary(self, content: str, category: ContentCategory) -> ContentSummary:
        """
        生成內容摘要
        
        Args:
            content: 文章內容
            category: 內容類別
            
        Returns:
            ContentSummary: 內容摘要
        """
        # 根據類別使用不同的摘要策略
        if category.main_category == "教育":
            return self._generate_education_summary(content)
        else:
            return self._generate_business_summary(content)
            
    def _generate_education_summary(self, content: str) -> ContentSummary:
        """
        生成教育類內容摘要
        
        Args:
            content: 文章內容
            
        Returns:
            ContentSummary: 內容摘要
        """
        # 實現教育類內容摘要邏輯
        return ContentSummary(
            main_points=["主要觀點1", "主要觀點2"],
            key_insights=["關鍵洞察1", "關鍵洞察2"],
            action_items=["行動項目1", "行動項目2"],
            sentiment="正面"
        )
        
    def _generate_business_summary(self, content: str) -> ContentSummary:
        """
        生成商業類內容摘要
        
        Args:
            content: 文章內容
            
        Returns:
            ContentSummary: 內容摘要
        """
        # 實現商業類內容摘要邏輯
        return ContentSummary(
            main_points=["市場分析1", "市場分析2"],
            key_insights=["投資建議1", "投資建議2"],
            action_items=["交易策略1", "交易策略2"],
            sentiment="中性"
        )
        
    def process_text_file(self, file_path: str) -> Dict[str, Any]:
        """
        處理文字檔案
        
        Args:
            file_path: 檔案路徑
            
        Returns:
            Dict[str, Any]: 處理結果
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # 分類內容
            category = self._categorize_content("", content)
            
            # 生成摘要
            summary = self._generate_summary(content, category)
            
            return {
                "content": content,
                "category": category.dict(),
                "summary": summary.dict()
            }
            
        except Exception as e:
            print(f"處理文字檔案時發生錯誤: {str(e)}")
            return {} 