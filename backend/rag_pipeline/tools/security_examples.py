#!/usr/bin/env python3
"""
Podwise RAG Pipeline - 安全工具使用範例

展示如何在 FastAPI、LangChain、CrewAI 中整合 Guardrails AI 安全驗證
包含實際的使用場景和最佳實踐

作者: Podwise Team
版本: 1.0.0
"""

import asyncio
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
import logging

# 導入安全工具
from security_tool import (
    SecurityTool, SecurityConfig, SecurityLevel,
    security_check, async_security_check,
    create_security_tool, create_fastapi_middleware,
    create_langchain_validator, create_crewai_validator
)

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ===== FastAPI 整合範例 =====

def create_fastapi_app_with_security():
    """創建整合安全驗證的 FastAPI 應用"""
    
    app = FastAPI(
        title="Podwise RAG Pipeline with Security",
        description="整合 Guardrails AI 安全驗證的 RAG Pipeline",
        version="1.0.0"
    )
    
    # 創建安全工具
    security_tool = create_security_tool(
        security_level=SecurityLevel.HIGH,
        blocked_keywords=["惡意", "攻擊", "病毒", "駭客"],
        custom_patterns=[
            r"<script>.*</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"eval\s*\(",
            r"document\.cookie"
        ]
    )
    
    # 創建安全中間件
    security_middleware = create_fastapi_middleware(
        security_level=SecurityLevel.HIGH
    )
    
    # 添加中間件
    app.middleware("http")(security_middleware)
    
    @app.post("/chat")
    @security_check(security_level=SecurityLevel.HIGH, raise_on_violation=True)
    async def chat_endpoint(message: str):
        """聊天端點 - 使用安全檢查裝飾器"""
        try:
            # 這裡是您的 RAG Pipeline 邏輯
            response = f"收到安全的消息: {message}"
            return {"response": response, "status": "success"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.post("/process-content")
    async def process_content_endpoint(content: str):
        """內容處理端點 - 手動安全檢查"""
        # 手動驗證內容
        result = security_tool.validate_content(content)
        
        if not result.is_valid:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "安全驗證失敗",
                    "violations": result.violations,
                    "message": "內容包含不安全的元素"
                }
            )
        
        # 處理安全內容
        processed_content = f"已處理安全內容: {content}"
        return {"processed_content": processed_content, "status": "success"}
    
    @app.get("/security/stats")
    async def get_security_stats():
        """獲取安全驗證統計資訊"""
        stats = security_tool.get_stats()
        return {"security_stats": stats}
    
    return app


# ===== LangChain 整合範例 =====

class SecureLangChainProcessor:
    """整合安全驗證的 LangChain 處理器"""
    
    def __init__(self):
        self.security_validator = create_langchain_validator(
            security_level=SecurityLevel.MEDIUM
        )
        self.logger = logging.getLogger(__name__)
    
    @security_check(security_level=SecurityLevel.MEDIUM)
    def process_prompt(self, prompt: str) -> str:
        """處理 LangChain 提示詞"""
        # 驗證提示詞安全性
        if not self.security_validator.validate_prompt(prompt):
            raise ValueError("提示詞包含不安全內容")
        
        # 這裡是您的 LangChain 處理邏輯
        processed_prompt = f"安全處理的提示詞: {prompt}"
        return processed_prompt
    
    @security_check(security_level=SecurityLevel.HIGH)
    def process_response(self, response: str) -> str:
        """處理 LangChain 回應"""
        # 驗證回應安全性
        if not self.security_validator.validate_response(response):
            raise ValueError("回應包含不安全內容")
        
        # 這裡是您的回應處理邏輯
        processed_response = f"安全處理的回應: {response}"
        return processed_response


# ===== CrewAI 整合範例 =====

class SecureCrewAIProcessor:
    """整合安全驗證的 CrewAI 處理器"""
    
    def __init__(self):
        self.security_validator = create_crewai_validator(
            security_level=SecurityLevel.HIGH
        )
        self.logger = logging.getLogger(__name__)
    
    @async_security_check(security_level=SecurityLevel.HIGH)
    async def process_agent_input(self, input_data: str) -> str:
        """處理 CrewAI 代理輸入"""
        # 驗證代理輸入安全性
        if not self.security_validator.validate_agent_input(input_data):
            raise ValueError("代理輸入包含不安全內容")
        
        # 這裡是您的 CrewAI 代理處理邏輯
        processed_input = f"安全處理的代理輸入: {input_data}"
        return processed_input
    
    @async_security_check(security_level=Security_level.HIGH)
    async def process_agent_output(self, output_data: str) -> str:
        """處理 CrewAI 代理輸出"""
        # 驗證代理輸出安全性
        if not self.security_validator.validate_agent_output(output_data):
            raise ValueError("代理輸出包含不安全內容")
        
        # 這裡是您的代理輸出處理邏輯
        processed_output = f"安全處理的代理輸出: {output_data}"
        return processed_output


# ===== RAG Pipeline 整合範例 =====

class SecureRAGPipeline:
    """整合安全驗證的 RAG Pipeline"""
    
    def __init__(self):
        self.security_tool = create_security_tool(
            security_level=SecurityLevel.HIGH,
            blocked_keywords=[
                "惡意", "攻擊", "病毒", "駭客", "木馬",
                "釣魚", "詐騙", "色情", "暴力", "仇恨"
            ],
            custom_patterns=[
                r"<script>.*</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"eval\s*\(",
                r"document\.cookie",
                r"window\.location",
                r"alert\s*\(",
                r"confirm\s*\(",
                r"prompt\s*\("
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    @security_check(security_level=SecurityLevel.HIGH)
    async def process_user_query(self, query: str) -> Dict[str, Any]:
        """處理用戶查詢"""
        # 安全驗證已通過裝飾器處理
        
        # 這裡是您的 RAG Pipeline 邏輯
        # 1. 向量搜尋
        # 2. 內容檢索
        # 3. 回應生成
        
        response = {
            "query": query,
            "response": f"安全處理的查詢回應: {query}",
            "sources": ["source1", "source2"],
            "confidence": 0.95,
            "security_validated": True
        }
        
        return response
    
    @security_check(security_level=SecurityLevel.HIGH)
    async def process_content_chunk(self, chunk: str) -> Dict[str, Any]:
        """處理內容分塊"""
        # 安全驗證已通過裝飾器處理
        
        # 這裡是您的內容處理邏輯
        processed_chunk = {
            "original_chunk": chunk,
            "processed_chunk": f"安全處理的內容: {chunk}",
            "embedding": [0.1, 0.2, 0.3],  # 向量嵌入
            "tags": ["business", "technology"],
            "security_validated": True
        }
        
        return processed_chunk
    
    async def batch_process_content(self, contents: List[str]) -> List[Dict[str, Any]]:
        """批次處理內容"""
        results = []
        
        for content in contents:
            try:
                result = await self.process_content_chunk(content)
                results.append(result)
            except ValueError as e:
                self.logger.warning(f"內容安全驗證失敗: {e}")
                results.append({
                    "original_chunk": content,
                    "error": "安全驗證失敗",
                    "security_validated": False
                })
        
        return results


# ===== 使用範例 =====

async def main():
    """主函數 - 展示各種使用方式"""
    
    print("🚀 Podwise 安全工具使用範例")
    print("=" * 50)
    
    # 1. 基本安全工具使用
    print("\n1. 基本安全工具使用:")
    security_tool = create_security_tool(
        security_level=SecurityLevel.HIGH,
        blocked_keywords=["惡意", "攻擊"],
        custom_patterns=[r"<script>.*</script>"]
    )
    
    # 測試安全內容
    safe_content = "這是一個正常的測試內容"
    result = security_tool.validate_content(safe_content)
    print(f"安全內容驗證: {result.is_valid}")
    
    # 測試不安全內容
    unsafe_content = "這是一個惡意攻擊的內容 <script>alert('xss')</script>"
    result = security_tool.validate_content(unsafe_content)
    print(f"不安全內容驗證: {result.is_valid}")
    print(f"違規項目: {result.violations}")
    
    # 2. LangChain 整合
    print("\n2. LangChain 整合:")
    langchain_processor = SecureLangChainProcessor()
    
    try:
        safe_prompt = "請解釋機器學習的基本概念"
        processed_prompt = langchain_processor.process_prompt(safe_prompt)
        print(f"安全提示詞處理: {processed_prompt}")
    except ValueError as e:
        print(f"提示詞驗證失敗: {e}")
    
    # 3. CrewAI 整合
    print("\n3. CrewAI 整合:")
    crewai_processor = SecureCrewAIProcessor()
    
    try:
        safe_input = "分析市場趨勢"
        processed_input = await crewai_processor.process_agent_input(safe_input)
        print(f"安全代理輸入處理: {processed_input}")
    except ValueError as e:
        print(f"代理輸入驗證失敗: {e}")
    
    # 4. RAG Pipeline 整合
    print("\n4. RAG Pipeline 整合:")
    rag_pipeline = SecureRAGPipeline()
    
    try:
        safe_query = "什麼是人工智能？"
        response = await rag_pipeline.process_user_query(safe_query)
        print(f"安全查詢處理: {response}")
    except ValueError as e:
        print(f"查詢驗證失敗: {e}")
    
    # 5. 批次處理
    print("\n5. 批次處理:")
    contents = [
        "這是安全的內容",
        "這是惡意攻擊的內容",
        "這是正常的技術討論",
        "<script>alert('xss')</script>"
    ]
    
    batch_results = await rag_pipeline.batch_process_content(contents)
    for i, result in enumerate(batch_results):
        print(f"內容 {i+1}: {'通過' if result['security_validated'] else '失敗'}")
    
    # 6. 統計資訊
    print("\n6. 安全統計資訊:")
    stats = security_tool.get_stats()
    print(f"總驗證次數: {stats['total_validations']}")
    print(f"通過次數: {stats['passed_validations']}")
    print(f"失敗次數: {stats['failed_validations']}")
    print(f"成功率: {stats['success_rate']:.2%}")
    print(f"平均處理時間: {stats['average_processing_time']:.4f}秒")


if __name__ == "__main__":
    # 執行範例
    asyncio.run(main()) 