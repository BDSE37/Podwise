#!/usr/bin/env python3
"""
Podwise RAG Pipeline - MCP 整合模組

整合 Model Context Protocol (MCP) 以增強 RAG Pipeline 功能：
- 外部工具整合
- 資源管理
- 動態工具調用
- 上下文管理

作者: Podwise Team
版本: 1.0.0
"""

import asyncio
import logging
import yaml
import json
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# 導入 Langfuse 追蹤
from .langfuse_tracking import langfuse_trace

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """MCP 工具定義"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable


@dataclass
class MCPResource:
    """MCP 資源定義"""
    uri: str
    mime_type: str
    content: bytes
    metadata: Dict[str, Any]


class PodwiseMCPIntegration:
    """
    Podwise MCP 整合類別
    
    提供與外部工具和資源的整合功能
    """
    
    def __init__(self, 
                 config_path: str = "config/mcp_config.yaml",
                 enable_tools: bool = True,
                 enable_resources: bool = True):
        """
        初始化 MCP 整合
        
        Args:
            config_path: MCP 配置檔案路徑
            enable_tools: 是否啟用工具功能
            enable_resources: 是否啟用資源功能
        """
        self.config_path = config_path
        self.enable_tools = enable_tools
        self.enable_resources = enable_resources
        
        # 載入配置
        self.config = self._load_config()
        
        # 註冊的工具
        self.registered_tools: Dict[str, MCPTool] = {}
        
        # 資源快取
        self.resource_cache: Dict[str, MCPResource] = {}
        
        # 初始化工具
        self._initialize_tools()
        
        logger.info("✅ Podwise MCP 整合初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """載入 MCP 配置"""
        try:
            config_file = Path(__file__).parent.parent / self.config_path
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                logger.warning(f"MCP 配置檔案不存在: {config_file}")
                return {"mcp": {}}
        except Exception as e:
            logger.error(f"載入 MCP 配置失敗: {e}")
            return {"mcp": {}}
    
    def _initialize_tools(self):
        """初始化內建工具"""
        if not self.enable_tools:
            return
        
        # 註冊 Podcast 搜尋工具
        self.register_tool(
            name="search_podcasts",
            description="搜尋 Podcast 資訊",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜尋查詢"},
                    "category": {"type": "string", "description": "Podcast 類別"},
                    "limit": {"type": "integer", "description": "結果數量限制"}
                },
                "required": ["query"]
            },
            handler=self._search_podcasts_handler
        )
        
        # 註冊情感分析工具
        self.register_tool(
            name="analyze_sentiment",
            description="分析文本情感",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要分析的文本"},
                    "analyzer_type": {"type": "string", "enum": ["chinese", "vader"], "description": "分析器類型"}
                },
                "required": ["text"]
            },
            handler=self._analyze_sentiment_handler
        )
        
        # 註冊 Apple Podcast 排名工具
        self.register_tool(
            name="get_apple_podcast_ranking",
            description="獲取 Apple Podcast 排名資訊",
            input_schema={
                "type": "object",
                "properties": {
                    "rss_id": {"type": "string", "description": "Podcast RSS ID"},
                    "include_details": {"type": "boolean", "description": "是否包含詳細資訊"}
                },
                "required": ["rss_id"]
            },
            handler=self._get_apple_ranking_handler
        )
        
        # 註冊向量搜尋工具
        self.register_tool(
            name="vector_search",
            description="執行向量搜尋",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜尋查詢"},
                    "top_k": {"type": "integer", "description": "返回結果數量"},
                    "similarity_threshold": {"type": "number", "description": "相似度閾值"}
                },
                "required": ["query"]
            },
            handler=self._vector_search_handler
        )
        
        # 註冊內容分類工具
        self.register_tool(
            name="classify_content",
            description="分類內容",
            input_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "要分類的內容"},
                    "categories": {"type": "array", "items": {"type": "string"}, "description": "可選分類列表"}
                },
                "required": ["content"]
            },
            handler=self._classify_content_handler
        )
        
        logger.info(f"✅ 已註冊 {len(self.registered_tools)} 個 MCP 工具")
    
    def register_tool(self, name: str, description: str, input_schema: Dict[str, Any], handler: Callable):
        """
        註冊 MCP 工具
        
        Args:
            name: 工具名稱
            description: 工具描述
            input_schema: 輸入參數 schema
            handler: 工具處理函數
        """
        self.registered_tools[name] = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler
        )
        logger.info(f"✅ 註冊 MCP 工具: {name}")
    
    async def list_available_tools(self) -> List[Dict[str, Any]]:
        """
        列出可用的工具
        
        Returns:
            List[Dict[str, Any]]: 可用工具列表
        """
        tools = []
        
        for tool_name, tool in self.registered_tools.items():
            tools.append({
                "name": tool_name,
                "description": tool.description,
                "input_schema": tool.input_schema
            })
        
        return tools
    
    @langfuse_trace("tool_call")
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        調用工具
        
        Args:
            tool_name: 工具名稱
            arguments: 工具參數
            
        Returns:
            Dict[str, Any]: 工具調用結果
        """
        try:
            if tool_name not in self.registered_tools:
                raise ValueError(f"工具 '{tool_name}' 不存在")
            
            tool = self.registered_tools[tool_name]
            result = await tool.handler(arguments)
            
            return {
                "success": True,
                "tool_name": tool_name,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"調用工具 '{tool_name}' 失敗: {e}")
            return {
                "success": False,
                "tool_name": tool_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _search_podcasts_handler(self, arguments: Dict[str, Any]) -> str:
        """Podcast 搜尋工具處理器"""
        query = arguments.get("query", "")
        category = arguments.get("category", "")
        limit = arguments.get("limit", 10)
        
        # 模擬搜尋結果
        results = [
            {"title": "科技早知道", "category": "technology", "rating": 4.5},
            {"title": "商業就是這樣", "category": "business", "rating": 4.2},
            {"title": "學習成長", "category": "education", "rating": 4.7}
        ]
        
        if category:
            results = [r for r in results if r["category"] == category]
        
        return f"找到 {len(results)} 個相關 Podcast: {results[:limit]}"
    
    async def _analyze_sentiment_handler(self, arguments: Dict[str, Any]) -> str:
        """情感分析工具處理器"""
        text = arguments.get("text", "")
        analyzer_type = arguments.get("analyzer_type", "chinese")
        
        # 模擬情感分析結果
        sentiment_scores = {
            "positive": 0.7,
            "negative": 0.1,
            "neutral": 0.2
        }
        
        if "很棒" in text or "很好" in text:
            label = "positive"
        elif "糟糕" in text or "不好" in text:
            label = "negative"
        else:
            label = "neutral"
        
        return f"情感分析結果: {label} (信心度: 0.85), 分析器: {analyzer_type}"
    
    async def _get_apple_ranking_handler(self, arguments: Dict[str, Any]) -> str:
        """Apple Podcast 排名工具處理器"""
        rss_id = arguments.get("rss_id", "")
        include_details = arguments.get("include_details", False)
        
        # 模擬 Apple Podcast 排名數據
        ranking_data = {
            "rss_id": rss_id,
            "apple_rating": 4.5,
            "apple_review_count": 1250,
            "user_click_rate": 0.75,
            "comment_sentiment_score": 0.8
        }
        
        if include_details:
            return f"詳細排名資訊: {json.dumps(ranking_data, ensure_ascii=False, indent=2)}"
        else:
            return f"Apple Podcast 排名: {ranking_data['apple_rating']}/5 星 ({ranking_data['apple_review_count']} 評論)"
    
    async def _vector_search_handler(self, arguments: Dict[str, Any]) -> str:
        """向量搜尋工具處理器"""
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 5)
        similarity_threshold = arguments.get("similarity_threshold", 0.7)
        
        # 模擬向量搜尋結果
        results = [
            {"id": "1", "title": "相關 Podcast 1", "similarity": 0.95},
            {"id": "2", "title": "相關 Podcast 2", "similarity": 0.88},
            {"id": "3", "title": "相關 Podcast 3", "similarity": 0.82}
        ]
        
        # 過濾相似度
        filtered_results = [r for r in results if r["similarity"] >= similarity_threshold]
        
        return f"向量搜尋結果: 找到 {len(filtered_results)} 個相關結果 (閾值: {similarity_threshold})"
    
    async def _classify_content_handler(self, arguments: Dict[str, Any]) -> str:
        """內容分類工具處理器"""
        content = arguments.get("content", "")
        categories = arguments.get("categories", ["business", "education", "technology", "entertainment"])
        
        # 簡單的關鍵字分類
        category_keywords = {
            "business": ["商業", "投資", "創業", "市場", "經濟"],
            "education": ["教育", "學習", "課程", "知識", "培訓"],
            "technology": ["科技", "技術", "程式", "AI", "創新"],
            "entertainment": ["娛樂", "音樂", "電影", "遊戲", "休閒"]
        }
        
        scores = {}
        for category in categories:
            score = 0
            for keyword in category_keywords.get(category, []):
                if keyword in content:
                    score += 1
            scores[category] = score
        
        # 找出最高分的分類
        best_category = max(scores.items(), key=lambda x: x[1])
        
        return f"內容分類結果: {best_category[0]} (信心度: {best_category[1]}/{len(category_keywords.get(best_category[0], []))})"
    
    async def add_resource(self, uri: str, mime_type: str, content: bytes, metadata: Optional[Dict[str, Any]] = None):
        """
        添加資源
        
        Args:
            uri: 資源 URI
            mime_type: MIME 類型
            content: 資源內容
            metadata: 元數據
        """
        if not self.enable_resources:
            return
        
        self.resource_cache[uri] = MCPResource(
            uri=uri,
            mime_type=mime_type,
            content=content,
            metadata=metadata or {}
        )
        logger.info(f"✅ 已添加資源: {uri}")
    
    async def get_resource(self, uri: str) -> Optional[MCPResource]:
        """
        獲取資源
        
        Args:
            uri: 資源 URI
            
        Returns:
            Optional[MCPResource]: 資源對象
        """
        return self.resource_cache.get(uri)
    
    async def list_resources(self) -> List[str]:
        """
        列出所有資源 URI
        
        Returns:
            List[str]: 資源 URI 列表
        """
        return list(self.resource_cache.keys())
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "tools_enabled": self.enable_tools,
            "resources_enabled": self.enable_resources,
            "registered_tools_count": len(self.registered_tools),
            "cached_resources_count": len(self.resource_cache),
            "config_loaded": bool(self.config)
        }
    
    async def enhance_response(self, 
                              original_content: str, 
                              user_query: str, 
                              category: str = "其他",
                              context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        使用 MCP 工具增強回應內容
        
        Args:
            original_content: 原始回應內容
            user_query: 用戶查詢
            category: 查詢分類
            context: 上下文資訊
            
        Returns:
            Dict[str, Any]: 增強結果
        """
        try:
            enhanced_content = original_content
            
            # 使用情感分析工具分析原始內容
            sentiment_result = await self.call_tool("analyze_sentiment", {
                "text": original_content,
                "analyzer_type": "chinese"
            })
            
            # 使用內容分類工具確認分類
            classification_result = await self.call_tool("classify_content", {
                "content": original_content,
                "categories": ["business", "education", "technology", "entertainment"]
            })
            
            # 根據分類和情感分析結果增強內容
            if sentiment_result.get("success"):
                sentiment_info = sentiment_result.get("result", "")
                if "positive" in sentiment_info.lower():
                    enhanced_content += "\n\n💡 小提醒：這個推薦看起來很受歡迎喔！"
                elif "negative" in sentiment_info.lower():
                    enhanced_content += "\n\n⚠️ 注意：這個內容可能需要您進一步評估。"
            
            # 添加分類相關的建議
            if classification_result.get("success"):
                class_info = classification_result.get("result", "")
                if "business" in class_info.lower():
                    enhanced_content += "\n\n💼 商業類內容：建議您關注實用性和風險管理。"
                elif "education" in class_info.lower():
                    enhanced_content += "\n\n📚 教育類內容：建議您關注學習效果和實用性。"
            
            # 使用向量搜尋工具提供額外建議
            search_result = await self.call_tool("vector_search", {
                "query": user_query,
                "top_k": 3,
                "similarity_threshold": 0.7
            })
            
            if search_result.get("success"):
                enhanced_content += f"\n\n🔍 相關搜尋：{search_result.get('result', '')}"
            
            return {
                "success": True,
                "enhanced_content": enhanced_content,
                "original_content": original_content,
                "enhancements_applied": [
                    "sentiment_analysis",
                    "content_classification", 
                    "vector_search"
                ],
                "metadata": {
                    "sentiment_result": sentiment_result,
                    "classification_result": classification_result,
                    "search_result": search_result
                }
            }
            
        except Exception as e:
            logger.error(f"MCP 回應增強失敗: {e}")
            return {
                "success": False,
                "enhanced_content": original_content,
                "error": str(e)
            }
    
    def get_config(self) -> Dict[str, Any]:
        """獲取配置"""
        return self.config


# 全域實例
_mcp_integration_instance: Optional[PodwiseMCPIntegration] = None


def get_mcp_integration() -> PodwiseMCPIntegration:
    """獲取 MCP 整合實例（單例模式）"""
    global _mcp_integration_instance
    if _mcp_integration_instance is None:
        _mcp_integration_instance = PodwiseMCPIntegration()
    return _mcp_integration_instance


async def main():
    """主函數 - 用於測試"""
    # 創建 MCP 整合實例
    mcp = PodwiseMCPIntegration()
    
    # 列出可用工具
    tools = await mcp.list_available_tools()
    print(f"可用工具數量: {len(tools)}")
    
    # 測試工具調用
    result = await mcp.call_tool("analyze_sentiment", {
        "text": "這個 Podcast 真的很棒！",
        "analyzer_type": "chinese"
    })
    
    print(f"工具調用結果: {result}")
    
    # 健康檢查
    health = await mcp.health_check()
    print(f"健康狀態: {health['status']}")


if __name__ == "__main__":
    asyncio.run(main()) 