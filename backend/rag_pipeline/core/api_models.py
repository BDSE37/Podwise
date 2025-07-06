"""
統一 API 模型定義

整合所有 API 相關的請求回應模型，包含：
- 查詢處理模型
- 用戶管理模型
- 向量搜尋模型
- 內容處理模型
- 系統資訊模型

作者: Podwise Team
版本: 2.0.0
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator


# ==================== 查詢處理模型 ====================

class QueryRequest(BaseModel):
    """查詢請求模型"""
    query: str = Field(description="查詢內容")
    user_id: Optional[str] = Field(default="test_user", description="用戶 ID")
    session_id: Optional[str] = Field(default=None, description="會話 ID")
    category_filter: Optional[str] = Field(default=None, description="類別過濾器")
    use_advanced_features: bool = Field(default=False, description="是否使用進階功能")
    use_openai_search: bool = Field(default=True, description="是否使用 OpenAI 搜尋")
    use_llm_generation: bool = Field(default=True, description="是否使用 LLM 生成")

    @validator('query')
    def validate_query(cls, v: str) -> str:
        """驗證查詢內容"""
        if not v.strip():
            raise ValueError("查詢內容不能為空")
        return v.strip()

    @validator('user_id')
    def validate_user_id(cls, v: str) -> str:
        """驗證用戶 ID"""
        if not v.strip():
            raise ValueError("用戶 ID 不能為空")
        return v.strip()


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


class UserQueryRequest(BaseModel):
    """用戶查詢請求模型（FastAPI 專用）"""
    user_id: str = Field(..., description="用戶 ID", min_length=1)
    query: str = Field(..., description="查詢內容", min_length=1)
    session_id: Optional[str] = Field(default=None, description="會話 ID")
    
    @validator('user_id')
    def validate_user_id(cls, v: str) -> str:
        """驗證用戶 ID"""
        if not v.strip():
            raise ValueError("用戶 ID 不能為空")
        return v.strip()
    
    @validator('query')
    def validate_query(cls, v: str) -> str:
        """驗證查詢內容"""
        if not v.strip():
            raise ValueError("查詢內容不能為空")
        return v.strip()


class UserQueryResponse(BaseModel):
    """用戶查詢回應模型（FastAPI 專用）"""
    user_id: str
    query: str
    response: str
    category: str
    confidence: float
    recommendations: List[Dict[str, Any]]
    reasoning: str
    processing_time: float
    timestamp: str


# ==================== 用戶管理模型 ====================

class UserValidationRequest(BaseModel):
    """用戶驗證請求模型"""
    user_id: str = Field(..., description="用戶 ID", min_length=1)
    
    @validator('user_id')
    def validate_user_id(cls, v: str) -> str:
        """驗證用戶 ID"""
        if not v.strip():
            raise ValueError("用戶 ID 不能為空")
        return v.strip()


class UserValidationResponse(BaseModel):
    """用戶驗證回應模型"""
    user_id: str
    is_valid: bool
    has_history: bool
    preferred_category: Optional[str] = None
    message: str


class ChatHistoryRequest(BaseModel):
    """聊天歷史請求模型"""
    user_id: str = Field(description="用戶 ID")
    limit: int = Field(default=50, description="返回數量限制")

    @validator('user_id')
    def validate_user_id(cls, v: str) -> str:
        """驗證用戶 ID"""
        if not v.strip():
            raise ValueError("用戶 ID 不能為空")
        return v.strip()


class ChatHistoryResponse(BaseModel):
    """聊天歷史回應模型"""
    user_id: str
    history: List[Dict[str, Any]]
    total: int


# ==================== 向量搜尋模型 ====================

class VectorSearchRequest(BaseModel):
    """向量搜尋請求模型"""
    query: str = Field(description="搜尋查詢")
    top_k: int = Field(default=5, description="返回結果數量")
    category_filter: Optional[str] = Field(default=None, description="類別過濾器")
    use_milvus: bool = Field(default=True, description="是否使用 Milvus")
    use_knn: bool = Field(default=True, description="是否使用 KNN")
    use_tags: bool = Field(default=True, description="是否使用標籤")

    @validator('query')
    def validate_query(cls, v: str) -> str:
        """驗證查詢內容"""
        if not v.strip():
            raise ValueError("查詢內容不能為空")
        return v.strip()


class VectorSearchResponse(BaseModel):
    """向量搜尋回應模型"""
    query: str = Field(description="搜尋查詢")
    results: List[Dict[str, Any]] = Field(description="搜尋結果")
    total: int = Field(description="結果總數")
    processing_time: float = Field(description="處理時間")
    milvus_results: List[Dict[str, Any]] = Field(default_factory=list, description="Milvus 結果")
    knn_results: Optional[Dict[str, Any]] = Field(default=None, description="KNN 結果")
    tag_results: Optional[Dict[str, Any]] = Field(default=None, description="標籤結果")


# ==================== 內容處理模型 ====================

class ContentProcessRequest(BaseModel):
    """內容處理請求模型"""
    content: str = Field(description="處理內容")
    title: Optional[str] = Field(default=None, description="標題")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元數據")

    @validator('content')
    def validate_content(cls, v: str) -> str:
        """驗證內容"""
        if not v.strip():
            raise ValueError("內容不能為空")
        return v.strip()


class ContentProcessResponse(BaseModel):
    """內容處理回應模型"""
    content: str = Field(description="原始內容")
    title: Optional[str] = Field(default=None, description="標題")
    processed_result: Dict[str, Any] = Field(description="處理結果")
    timestamp: str = Field(description="時間戳")
    category: str = Field(description="分類")
    confidence: float = Field(description="信心度")
    keywords: List[str] = Field(default_factory=list, description="關鍵詞")
    summary: str = Field(description="摘要")
    tags: List[str] = Field(default_factory=list, description="標籤")


# ==================== 系統資訊模型 ====================

class SystemInfoResponse(BaseModel):
    """系統資訊回應模型"""
    version: str = Field(description="版本號")
    timestamp: str = Field(description="時間戳")
    environment: str = Field(description="環境")
    debug: bool = Field(description="除錯模式")
    components: Dict[str, bool] = Field(description="組件狀態")
    features: List[str] = Field(description="功能列表")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="配置資訊")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="統計資訊")


class HealthCheckResponse(BaseModel):
    """健康檢查回應模型"""
    status: str = Field(description="狀態")
    timestamp: str = Field(description="時間戳")
    components: Dict[str, bool] = Field(description="組件狀態")
    rag_pipeline_health: Dict[str, Any] = Field(default_factory=dict, description="RAG Pipeline 健康狀態")
    web_search_available: bool = Field(description="Web 搜尋可用性")


# ==================== 錯誤處理模型 ====================

class ErrorResponse(BaseModel):
    """錯誤回應模型"""
    error: str = Field(description="錯誤類型")
    detail: str = Field(description="錯誤詳情")
    timestamp: str = Field(description="時間戳")
    error_code: Optional[str] = Field(default=None, description="錯誤代碼")
    suggestions: Optional[List[str]] = Field(default=None, description="建議解決方案")


# ==================== 配置模型 ====================

class ConfigRequest(BaseModel):
    """配置請求模型"""
    config_type: str = Field(description="配置類型")
    updates: Dict[str, Any] = Field(description="更新內容")

    @validator('config_type')
    def validate_config_type(cls, v: str) -> str:
        """驗證配置類型"""
        valid_types = ["llm", "vector", "semantic", "crewai", "rag", "langfuse"]
        if v not in valid_types:
            raise ValueError(f"配置類型必須是以下之一: {', '.join(valid_types)}")
        return v


class ConfigResponse(BaseModel):
    """配置回應模型"""
    config_type: str = Field(description="配置類型")
    status: str = Field(description="更新狀態")
    message: str = Field(description="訊息")
    updated_fields: List[str] = Field(default_factory=list, description="更新的欄位")
    timestamp: str = Field(description="時間戳")


# ==================== 監控模型 ====================

class MonitoringRequest(BaseModel):
    """監控請求模型"""
    metric_type: str = Field(description="指標類型")
    time_range: Optional[str] = Field(default="24h", description="時間範圍")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="過濾條件")

    @validator('metric_type')
    def validate_metric_type(cls, v: str) -> str:
        """驗證指標類型"""
        valid_types = ["performance", "accuracy", "usage", "errors", "custom"]
        if v not in valid_types:
            raise ValueError(f"指標類型必須是以下之一: {', '.join(valid_types)}")
        return v


class MonitoringResponse(BaseModel):
    """監控回應模型"""
    metric_type: str = Field(description="指標類型")
    data: Dict[str, Any] = Field(description="監控數據")
    summary: Dict[str, Any] = Field(description="摘要統計")
    timestamp: str = Field(description="時間戳")


# ==================== 工具函數 ====================

def create_error_response(error_type: str, detail: str, error_code: Optional[str] = None) -> ErrorResponse:
    """創建錯誤回應"""
    return ErrorResponse(
        error=error_type,
        detail=detail,
        timestamp=datetime.now().isoformat(),
        error_code=error_code
    )


def create_success_response(data: Dict[str, Any], message: str = "Success") -> Dict[str, Any]:
    """創建成功回應"""
    return {
        "status": "success",
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }


# ==================== 模型驗證工具 ====================

def validate_query_request(request: QueryRequest) -> bool:
    """驗證查詢請求"""
    return bool(request.query and request.user_id)


def validate_vector_search_request(request: VectorSearchRequest) -> bool:
    """驗證向量搜尋請求"""
    return bool(request.query and request.top_k > 0)


def validate_content_process_request(request: ContentProcessRequest) -> bool:
    """驗證內容處理請求"""
    return bool(request.content)


# ==================== 模型轉換工具 ====================

def query_request_to_user_query_request(query_request: QueryRequest) -> UserQueryRequest:
    """轉換查詢請求模型"""
    return UserQueryRequest(
        user_id=query_request.user_id,
        query=query_request.query,
        session_id=query_request.session_id
    )


def user_query_response_to_query_response(user_response: UserQueryResponse) -> QueryResponse:
    """轉換用戶查詢回應模型"""
    return QueryResponse(
        query=user_response.query,
        response=user_response.response,
        timestamp=user_response.timestamp,
        status="success",
        confidence=user_response.confidence,
        category=user_response.category,
        processing_time=user_response.processing_time,
        metadata={
            "recommendations": user_response.recommendations,
            "reasoning": user_response.reasoning
        }
    ) 