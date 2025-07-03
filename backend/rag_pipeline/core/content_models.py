"""
內容處理相關的資料模型
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class ContentCategory(BaseModel):
    """內容類別模型"""
    main_category: str = Field(description="主要類別")
    sub_category: str = Field(description="子類別")
    tags: List[str] = Field(description="標籤列表")

class ContentMetadata(BaseModel):
    """內容元數據模型"""
    title: str = Field(description="標題")
    author: str = Field(description="作者")
    publish_date: datetime = Field(description="發布日期")
    category: ContentCategory = Field(description="內容類別")
    source: str = Field(description="來源")
    url: Optional[str] = Field(description="原始URL")
    organization: str = Field(default="", description="發布機構")
    topics: List[str] = Field(default_factory=list, description="主題標籤")
    likes: int = Field(default=0, description="點讚數")
    views: int = Field(default=0, description="瀏覽數")
    comments: int = Field(default=0, description="評論數")
    source_system: str = Field(default="", description="來源系統標識")
    sensitivity_level: str = Field(default="public", description="數據敏感度級別")
    version: str = Field(default="1.0", description="文檔版本")
    paragraph_metadata: List[Dict[str, Any]] = Field(default_factory=list, description="段落級 Metadata")

class ContentSummary(BaseModel):
    """內容摘要模型"""
    main_points: List[str] = Field(description="主要觀點")
    key_insights: List[str] = Field(description="關鍵洞察")
    action_items: List[str] = Field(description="行動項目")
    sentiment: str = Field(description="情感傾向")

class ParagraphMetadata(BaseModel):
    """段落級 Metadata 模型"""
    paragraph_id: str = Field(description="段落唯一標識")
    content: str = Field(description="段落內容")
    position: int = Field(description="段落位置")
    likes: int = Field(default=0, description="段落點讚數")
    comments: int = Field(default=0, description="段落評論數")
    tags: List[str] = Field(default_factory=list, description="段落標籤")
    related_paragraphs: List[str] = Field(default_factory=list, description="相關段落 ID") 