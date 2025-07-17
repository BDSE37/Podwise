#!/usr/bin/env python3
"""
提示詞處理器模組

此模組負責整合 crew_agents 和 prompt_templates，
提供統一的提示詞格式化和 LLM 調用介面。

作者: Podwise Team
版本: 1.0.0
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

import sys
import os
# 添加 rag_pipeline 根目錄到路徑
rag_pipeline_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if rag_pipeline_root not in sys.path:
    sys.path.insert(0, rag_pipeline_root)

# 修復導入路徑問題
import os
import sys

# 添加 rag_pipeline 根目錄到 Python 路徑
rag_pipeline_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if rag_pipeline_root not in sys.path:
    sys.path.insert(0, rag_pipeline_root)

# 添加 config 目錄到 Python 路徑
config_path = os.path.join(rag_pipeline_root, 'config')
if config_path not in sys.path:
    sys.path.insert(0, config_path)

try:
    from prompt_templates import get_prompt_template, format_prompt
    from integrated_config import get_config
except ImportError as e:
    print(f"導入錯誤: {e}")
    print(f"當前路徑: {os.getcwd()}")
    print(f"Python 路徑: {sys.path}")
    # 嘗試相對導入
    try:
        from ..config.prompt_templates import get_prompt_template, format_prompt
        from ..config.integrated_config import get_config
    except ImportError as e2:
        print(f"相對導入也失敗: {e2}")
        # 最後嘗試直接導入
        try:
            import config.prompt_templates as pt
            import config.integrated_config as ic
            get_prompt_template = pt.get_prompt_template
            format_prompt = pt.format_prompt
            get_config = ic.get_config
        except ImportError as e3:
            print(f"直接導入也失敗: {e3}")
            raise
# Langfuse 整合已移除，使用 Langfuse Cloud 服務

logger = logging.getLogger(__name__)


@dataclass
class PromptResult:
    """提示詞處理結果"""
    content: str
    confidence: float
    metadata: Dict[str, Any]
    processing_time: float = 0.0


class PromptProcessor:
    """
    提示詞處理器
    
    負責整合提示詞模板和 LLM 調用，為 CrewAI 代理人
    提供統一的提示詞處理介面。
    """
    
    def __init__(self):
        """初始化提示詞處理器"""
        self.config = get_config()
        # Langfuse 整合已移除，使用 Langfuse Cloud 服務
        self.monitor = None
        
    async def process_category_classification(self, user_question: str, 
                                            trace_id: Optional[str] = None) -> PromptResult:
        """
        處理問題分類
        
        Args:
            user_question: 用戶問題
            trace_id: Langfuse 追蹤 ID
            
        Returns:
            PromptResult: 分類結果
        """
        try:
            # 獲取分類提示詞模板
            classifier_prompt = get_prompt_template("category_classifier")
            formatted_prompt = format_prompt(classifier_prompt, user_question=user_question)
            
            # 調用 LLM（這裡需要實際的 LLM 調用）
            # 暫時返回模擬結果
            result = await self._call_llm(formatted_prompt, "category_classification", trace_id)
            
            # 解析分類結果
            category_result = self._parse_category_result(result)
            
            return PromptResult(
                content=json.dumps(category_result, ensure_ascii=False),
                confidence=category_result.get("categories", [{}])[0].get("confidence", 0.0),
                metadata={"template_used": "category_classifier", "result": category_result}
            )
            
        except Exception as e:
            logger.error(f"分類處理失敗: {str(e)}")
            return PromptResult(
                content="分類處理失敗",
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def process_semantic_retrieval(self, user_query: str, category_result: Dict[str, Any],
                                       trace_id: Optional[str] = None) -> PromptResult:
        """
        處理語意檢索
        
        Args:
            user_query: 用戶查詢
            category_result: 分類結果
            trace_id: Langfuse 追蹤 ID
            
        Returns:
            PromptResult: 檢索結果
        """
        try:
            # 獲取檢索提示詞模板
            retrieval_prompt = get_prompt_template("semantic_retrieval")
            formatted_prompt = format_prompt(
                retrieval_prompt,
                user_query=user_query,
                category_result=json.dumps(category_result, ensure_ascii=False, indent=2)
            )
            
            # 調用 LLM
            result = await self._call_llm(formatted_prompt, "semantic_retrieval", trace_id)
            
            # 這裡應該整合實際的語意檢索邏輯
            search_results = await self._perform_semantic_search(user_query, category_result)
            
            return PromptResult(
                content=json.dumps(search_results, ensure_ascii=False),
                confidence=self._calculate_retrieval_confidence(search_results),
                metadata={"template_used": "semantic_retrieval", "results": search_results}
            )
            
        except Exception as e:
            logger.error(f"語意檢索處理失敗: {str(e)}")
            return PromptResult(
                content="語意檢索處理失敗",
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def process_business_expert(self, search_results: List[Dict[str, Any]], 
                                    user_question: str, trace_id: Optional[str] = None) -> PromptResult:
        """
        處理商業專家評估
        
        Args:
            search_results: 檢索結果
            user_question: 用戶問題
            trace_id: Langfuse 追蹤 ID
            
        Returns:
            PromptResult: 專家評估結果
        """
        try:
            # 獲取商業專家提示詞模板
            expert_prompt = get_prompt_template("business_expert")
            formatted_prompt = format_prompt(
                expert_prompt,
                search_results=json.dumps(search_results, ensure_ascii=False, indent=2),
                user_question=user_question
            )
            
            # 調用 LLM
            result = await self._call_llm(formatted_prompt, "business_expert", trace_id)
            
            # 解析專家評估結果
            expert_result = self._parse_expert_result(result, "商業")
            
            return PromptResult(
                content=json.dumps(expert_result, ensure_ascii=False),
                confidence=expert_result.get("recommendations", [{}])[0].get("confidence", 0.0),
                metadata={"template_used": "business_expert", "result": expert_result}
            )
            
        except Exception as e:
            logger.error(f"商業專家處理失敗: {str(e)}")
            return PromptResult(
                content="商業專家處理失敗",
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def process_education_expert(self, search_results: List[Dict[str, Any]], 
                                     user_question: str, trace_id: Optional[str] = None) -> PromptResult:
        """
        處理教育專家評估
        
        Args:
            search_results: 檢索結果
            user_question: 用戶問題
            trace_id: Langfuse 追蹤 ID
            
        Returns:
            PromptResult: 專家評估結果
        """
        try:
            # 獲取教育專家提示詞模板
            expert_prompt = get_prompt_template("education_expert")
            formatted_prompt = format_prompt(
                expert_prompt,
                search_results=json.dumps(search_results, ensure_ascii=False, indent=2),
                user_question=user_question
            )
            
            # 調用 LLM
            result = await self._call_llm(formatted_prompt, "education_expert", trace_id)
            
            # 解析專家評估結果
            expert_result = self._parse_expert_result(result, "教育")
            
            return PromptResult(
                content=json.dumps(expert_result, ensure_ascii=False),
                confidence=expert_result.get("recommendations", [{}])[0].get("confidence", 0.0),
                metadata={"template_used": "education_expert", "result": expert_result}
            )
            
        except Exception as e:
            logger.error(f"教育專家處理失敗: {str(e)}")
            return PromptResult(
                content="教育專家處理失敗",
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def process_leader_decision(self, expert_results: Dict[str, Any], 
                                    user_question: str, trace_id: Optional[str] = None) -> PromptResult:
        """
        處理領導者決策
        
        Args:
            expert_results: 專家評估結果
            user_question: 用戶問題
            trace_id: Langfuse 追蹤 ID
            
        Returns:
            PromptResult: 決策結果
        """
        try:
            # 獲取領導者決策提示詞模板
            leader_prompt = get_prompt_template("leader_decision")
            formatted_prompt = format_prompt(
                leader_prompt,
                expert_results=json.dumps(expert_results, ensure_ascii=False, indent=2),
                user_question=user_question
            )
            
            # 調用 LLM
            result = await self._call_llm(formatted_prompt, "leader_decision", trace_id)
            
            return PromptResult(
                content=result,
                confidence=0.9,  # 領導者決策通常有較高信心度
                metadata={"template_used": "leader_decision", "decision": result}
            )
            
        except Exception as e:
            logger.error(f"領導者決策處理失敗: {str(e)}")
            return PromptResult(
                content="領導者決策處理失敗",
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def process_answer_generation(self, user_question: str, 
                                      final_recommendations: List[Dict[str, Any]],
                                      explanation: str, trace_id: Optional[str] = None) -> PromptResult:
        """
        處理回答生成
        
        Args:
            user_question: 用戶問題
            final_recommendations: 最終推薦
            explanation: 解釋說明
            trace_id: Langfuse 追蹤 ID
            
        Returns:
            PromptResult: 生成的回答
        """
        try:
            # 獲取回答生成提示詞模板
            answer_prompt = get_prompt_template("answer_generation")
            formatted_prompt = format_prompt(
                answer_prompt,
                user_question=user_question,
                final_recommendations=json.dumps(final_recommendations, ensure_ascii=False, indent=2),
                explanation=explanation
            )
            
            # 調用 LLM
            result = await self._call_llm(formatted_prompt, "answer_generation", trace_id)
            
            return PromptResult(
                content=result,
                confidence=0.85,
                metadata={"template_used": "answer_generation", "answer": result}
            )
            
        except Exception as e:
            logger.error(f"回答生成處理失敗: {str(e)}")
            return PromptResult(
                content="回答生成處理失敗",
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def _call_llm(self, prompt: str, task_type: str, 
                       trace_id: Optional[str] = None) -> str:
        """
        調用 LLM
        
        Args:
            prompt: 格式化後的提示詞
            task_type: 任務類型
            trace_id: Langfuse 追蹤 ID
            
        Returns:
            str: LLM 回應
        """
        # 這裡需要實際的 LLM 調用邏輯
        # 暫時返回模擬結果
        
        # Langfuse 整合已移除，使用 Langfuse Cloud 服務
        # 記錄到 Langfuse Cloud (如果需要)
        pass
        
        # 模擬不同任務類型的回應
        if task_type == "category_classification":
            return json.dumps({
                "categories": [
                    {"category": "商業", "confidence": 0.85, "keywords": ["投資", "理財"]},
                    {"category": "教育", "confidence": 0.45, "keywords": ["學習"]}
                ],
                "primary_category": "商業",
                "is_multi_category": False
            }, ensure_ascii=False)
        
        return "模擬 LLM 回應"
    
    async def _perform_semantic_search(self, query: str, 
                                     category_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        執行語意檢索
        
        Args:
            query: 查詢內容
            category_result: 分類結果
            
        Returns:
            List[Dict[str, Any]]: 檢索結果
        """
        # 這裡需要實際的語意檢索邏輯
        # 暫時返回模擬結果
        return [
            {
                "title": "股癌 EP123_投資新手必聽",
                "episode": "EP123",
                "rss_id": "stock_cancer_123",
                "category": "商業",
                "similarity_score": 0.85,
                "tag_score": 0.7,
                "hybrid_score": 0.805,
                "updated_at": "2024-01-15",
                "summary": "專門為投資新手設計的理財觀念分享"
            }
        ]
    
    def _parse_category_result(self, llm_response: str) -> Dict[str, Any]:
        """解析分類結果"""
        try:
            return json.loads(llm_response)
        except:
            return {
                "categories": [{"category": "其他", "confidence": 0.5}],
                "primary_category": "其他",
                "is_multi_category": False
            }
    
    def _parse_expert_result(self, llm_response: str, category: str) -> Dict[str, Any]:
        """解析專家評估結果"""
        try:
            return json.loads(llm_response)
        except:
            return {
                "category": category,
                "recommendations": [],
                "status": "error",
                "high_confidence_count": 0
            }
    
    def _calculate_retrieval_confidence(self, results: List[Dict[str, Any]]) -> float:
        """計算檢索信心度"""
        if not results:
            return 0.0
        
        scores = [r.get("hybrid_score", 0.0) for r in results]
        return sum(scores) / len(scores) if scores else 0.0 