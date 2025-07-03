"""
API 模型定義
統一定義所有 API 相關的請求回應模型
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    """查詢請求模型"""
    query: str = Field(description="查詢內容")
    user_id: Optional[str] = Field(default="test_user", description="用戶 ID")
    session_id: Optional[str] = Field(default=None, description="會話 ID")
    category_filter: Optional[str] = Field(default=None, description="類別過濾器")
    use_advanced_features: bool = Field(default=False, description="是否使用進階功能")
    use_openai_search: bool = Field(default=True, description="是否使用 OpenAI 搜尋")
    use_llm_generation: bool = Field(default=True, description="是否使用 LLM 生成")

class QueryResponse(BaseModel):
    """查詢回應模型"""
    query: str = Field(description="原始查詢")
    response: str = Field(description="回應內容")
    timestamp: str = Field(description="時間戳")
    status: str = Field(description="狀態")
    confidence: Optional[float] = Field(default=None, description="信心度")
    sources: Optional[List[str]] = Field(default=None, description="來源列表")
    processing_time: Optional[float] = Field(default=None, description="處理時間")
    level_used: Optional[str] = Field(default=None, description="使用的層級")
    category: Optional[str] = Field(default=None, description="分類")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元數據")
    components_used: Optional[List[str]] = Field(default=None, description="使用的組件")

class VectorSearchRequest(BaseModel):
    """向量搜尋請求模型"""
    query: str = Field(description="搜尋查詢")
    top_k: int = Field(default=5, description="返回結果數量")
    category_filter: Optional[str] = Field(default=None, description="類別過濾器")

class VectorSearchResponse(BaseModel):
    """向量搜尋回應模型"""
    query: str = Field(description="搜尋查詢")
    results: List[Dict[str, Any]] = Field(description="搜尋結果")
    total: int = Field(description="結果總數")
    processing_time: float = Field(description="處理時間")

class ContentProcessRequest(BaseModel):
    """內容處理請求模型"""
    content: str = Field(description="處理內容")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元數據")

class ContentProcessResponse(BaseModel):
    """內容處理回應模型"""
    content: str = Field(description="原始內容")
    processed_result: Dict[str, Any] = Field(description="處理結果")
    timestamp: str = Field(description="時間戳")

class ChatHistoryRequest(BaseModel):
    """聊天歷史請求模型"""
    user_id: str = Field(description="用戶 ID")
    limit: int = Field(default=50, description="返回數量限制")

class ChatHistoryResponse(BaseModel):
    """聊天歷史回應模型"""
    user_id: str = Field(description="用戶 ID")
    history: List[Dict[str, Any]] = Field(description="聊天歷史")
    total: int = Field(description="歷史記錄總數")

class SystemInfoResponse(BaseModel):
    """系統資訊回應模型"""
    version: str = Field(description="版本號")
    timestamp: str = Field(description="時間戳")
    environment: str = Field(description="環境")
    debug: bool = Field(description="除錯模式")
    components: Dict[str, bool] = Field(description="組件狀態")
    features: List[str] = Field(description="功能列表")

class HealthCheckResponse(BaseModel):
    """健康檢查回應模型"""
    status: str = Field(description="狀態")
    timestamp: str = Field(description="時間戳")
    components: Dict[str, bool] = Field(description="組件狀態") 