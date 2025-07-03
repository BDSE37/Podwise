"""
文檔處理工具
處理文檔並生成結構化的 Metadata
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import json

# 從 core 模組導入已定義的模型
from ..core.content_models import ParagraphMetadata

class DocumentMetadata(BaseModel):
    """文檔 Metadata 模型"""
    
    # 基本資訊
    title: str = Field(description="文檔標題")
    author: str = Field(description="作者")
    publish_date: datetime = Field(description="發布日期")
    organization: str = Field(description="發布機構")
    
    # 主題分類
    topics: List[str] = Field(description="主題標籤")
    category: str = Field(description="主要分類")
    
    # 互動數據
    likes: int = Field(default=0, description="點讚數")
    views: int = Field(default=0, description="瀏覽數")
    comments: int = Field(default=0, description="評論數")
    
    # 系統資訊
    source_system: str = Field(description="來源系統標識")
    import_date: datetime = Field(default_factory=datetime.now, description="數據導入日期")
    last_update: datetime = Field(default_factory=datetime.now, description="最後更新時間")
    
    # 安全級別
    sensitivity_level: str = Field(
        default="public",
        description="數據敏感度級別",
        pattern="^(public|internal|confidential|restricted)$"
    )
    
    # 版本控制
    version: str = Field(default="1.0", description="文檔版本")
    
    # 段落級 Metadata
    paragraph_metadata: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="段落級 Metadata"
    )

class DocumentProcessor:
    """文檔處理器"""
    
    def __init__(self):
        """初始化文檔處理器"""
        pass
        
    def process_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        split_paragraphs: bool = True
    ) -> Dict[str, Any]:
        """
        處理文檔並生成結構化的 Metadata
        
        Args:
            content: 文檔內容
            metadata: 原始 Metadata
            split_paragraphs: 是否分割段落
            
        Returns:
            Dict[str, Any]: 處理後的文檔和 Metadata
        """
        try:
            # 創建文檔 Metadata
            doc_metadata = DocumentMetadata(
                title=metadata.get("title", ""),
                author=metadata.get("author", ""),
                publish_date=metadata.get("publish_date", datetime.now()),
                organization=metadata.get("organization", ""),
                topics=metadata.get("topics", []),
                category=metadata.get("category", ""),
                likes=metadata.get("likes", 0),
                views=metadata.get("views", 0),
                comments=metadata.get("comments", 0),
                source_system=metadata.get("source_system", ""),
                sensitivity_level=metadata.get("sensitivity_level", "public"),
                version=metadata.get("version", "1.0")
            )
            
            # 處理段落
            if split_paragraphs:
                paragraphs = self._split_paragraphs(content)
                doc_metadata.paragraph_metadata = [
                    self._process_paragraph(p, i, metadata)
                    for i, p in enumerate(paragraphs)
                ]
                
            # 更新時間戳
            doc_metadata.last_update = datetime.now()
            
            return {
                "content": content,
                "metadata": doc_metadata.dict()
            }
            
        except Exception as e:
            print(f"處理文檔時發生錯誤: {str(e)}")
            raise
            
    def _split_paragraphs(self, content: str) -> List[str]:
        """
        分割文檔為段落
        
        Args:
            content: 文檔內容
            
        Returns:
            List[str]: 段落列表
        """
        # 使用空行分割段落
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        return paragraphs
        
    def _process_paragraph(
        self,
        content: str,
        position: int,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        處理段落並生成 Metadata
        
        Args:
            content: 段落內容
            position: 段落位置
            metadata: 原始 Metadata
            
        Returns:
            Dict[str, Any]: 段落 Metadata
        """
        paragraph_metadata = ParagraphMetadata(
            paragraph_id=f"p_{position}",
            content=content,
            position=position,
            likes=metadata.get("paragraph_likes", {}).get(str(position), 0),
            comments=metadata.get("paragraph_comments", {}).get(str(position), 0),
            tags=metadata.get("paragraph_tags", {}).get(str(position), []),
            related_paragraphs=metadata.get("related_paragraphs", {}).get(str(position), [])
        )
        
        return paragraph_metadata.dict()
        
    def update_metadata(
        self,
        current_metadata: Dict[str, Any],
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新文檔 Metadata
        
        Args:
            current_metadata: 當前 Metadata
            updates: 更新內容
            
        Returns:
            Dict[str, Any]: 更新後的 Metadata
        """
        try:
            # 更新基本資訊
            for key, value in updates.items():
                if key in current_metadata:
                    if isinstance(value, dict) and isinstance(current_metadata[key], dict):
                        current_metadata[key].update(value)
                    else:
                        current_metadata[key] = value
                        
            # 更新時間戳
            current_metadata["last_update"] = datetime.now().isoformat()
            
            return current_metadata
            
        except Exception as e:
            print(f"更新 Metadata 時發生錯誤: {str(e)}")
            raise 