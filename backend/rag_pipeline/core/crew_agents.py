#!/usr/bin/env python3
"""
三層代理人架構模組

此模組實現三層 CrewAI 架構，包含領導者層、類別專家層和功能專家層，
提供智能的查詢處理和決策制定功能。

架構層次：
- 第一層：領導者層 (Leader Layer) - 協調和決策
- 第二層：類別專家層 (Category Expert Layer) - 商業/教育專家
- 第三層：功能專家層 (Functional Expert Layer) - 專業功能處理

作者: Podwise Team
版本: 2.0.0
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time
from datetime import datetime
try:
    from .prompt_processor import PromptProcessor
except ImportError:
    from core.prompt_processor import PromptProcessor

logger = logging.getLogger(__name__)


# 導入統一數據模型
from .data_models import AgentResponse, UserQuery

# 導入統一基礎代理類別
from .base_agent import BaseAgent


# ==================== 第三層：功能專家層 ====================

class WebSearchAgent(BaseAgent):
    """
    Web 搜尋專家代理人
    
    此代理人負責當 RAG 檢索信心度不足時，使用 OpenAI 進行
    網路搜尋作為備援服務。
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化 Web 搜尋專家代理人"""
        super().__init__("Web Search Expert", config)
        
        # 載入角色配置
        try:
            import sys
            import os
            config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
            if config_dir not in sys.path:
                sys.path.insert(0, config_dir)
            from agent_roles_config import get_agent_roles_manager
            self.role_config = get_agent_roles_manager().get_role("web_search_expert")
        except ImportError as e:
            logger.info(f"ℹ️ 無法載入角色配置: {e}")
            self.role_config = None
        
        # 初始化 Web Search 工具
        try:
            import sys
            import os
            tools_dir = os.path.join(os.path.dirname(__file__), '..', 'tools')
            if tools_dir not in sys.path:
                sys.path.insert(0, tools_dir)
            from web_search_tool import WebSearchTool
            self.web_search_tool = WebSearchTool()
        except ImportError as e:
            logger.info(f"ℹ️ Web Search 工具不可用: {e}")
            self.web_search_tool = None
        
        # 設定信心度閾值（使用配置系統）
        self.confidence_threshold = self.role_config.confidence_threshold if self.role_config else 0.7
        
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        處理 Web 搜尋請求
        
        Args:
            input_data: 包含查詢和原始信心度的字典
                - query: 用戶查詢
                - original_confidence: 原始檢索信心度
                - category: 查詢分類
                - context: 上下文資訊
            
        Returns:
            AgentResponse: 搜尋結果
        """
        start_time = time.time()
        
        if not self.validate_input(input_data):
            return AgentResponse(
                content="輸入數據無效",
                confidence=0.0,
                reasoning="輸入數據驗證失敗",
                processing_time=time.time() - start_time
            )
        
        try:
            query = input_data.get('query', '')
            original_confidence = input_data.get('original_confidence', 0.0)
            category = input_data.get('category', '其他')
            context = input_data.get('context', '')
            
            # 檢查是否需要 Web 搜尋
            if not self._should_use_web_search(original_confidence):
                return AgentResponse(
                    content="原始檢索信心度足夠，無需 Web 搜尋",
                    confidence=original_confidence,
                    reasoning=f"原始信心度 {original_confidence:.2f} 高於閾值 {self.confidence_threshold}",
                    processing_time=time.time() - start_time
                )
            
            # 檢查 Web Search 工具是否可用
            if not self.web_search_tool or not hasattr(self.web_search_tool, 'is_configured') or not self.web_search_tool.is_configured():
                return AgentResponse(
                    content="Web 搜尋服務未配置，無法執行備援搜尋",
                    confidence=0.2,
                    reasoning="Web Search 工具不可用",
                    metadata={"web_search_available": False},
                    processing_time=time.time() - start_time
                )
            
            # 根據類別選擇搜尋策略
            search_result = await self._execute_category_search(query, category, context)
            
            processing_time = time.time() - start_time
            
            if search_result["success"]:
                return AgentResponse(
                    content=search_result["response"],
                    confidence=0.85,  # Web 搜尋通常有較高信心度
                    reasoning="使用 OpenAI Web 搜尋獲得回應",
                    metadata={
                        "web_search_used": True,
                        "search_method": search_result.get("method", "openai"),
                        "original_confidence": original_confidence,
                        "improvement": 0.85 - original_confidence
                    },
                    processing_time=processing_time
                )
            else:
                return AgentResponse(
                    content=f"Web 搜尋失敗: {search_result.get('error', 'Unknown error')}",
                    confidence=0.3,
                    reasoning="Web 搜尋執行失敗",
                    metadata={
                        "web_search_used": False,
                        "error": search_result.get("error", "Unknown error")
                    },
                    processing_time=processing_time
                )
                
        except Exception as e:
            logger.error(f"Web 搜尋專家處理失敗: {str(e)}")
            return AgentResponse(
                content="Web 搜尋過程中發生錯誤",
                confidence=0.1,
                reasoning=f"處理失敗: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    def _should_use_web_search(self, original_confidence: float) -> bool:
        """判斷是否需要使用 Web 搜尋"""
        return original_confidence < self.confidence_threshold
    
    async def _execute_category_search(self, query: str, category: str, context: str) -> Dict[str, Any]:
        """根據類別執行搜尋"""
        try:
            if category == "商業":
                return await self.web_search_tool.search_business_topic(query)
            elif category == "教育":
                return await self.web_search_tool.search_education_topic(query)
            else:
                # 其他類別使用通用搜尋
                return await self.web_search_tool.search_with_openai(query, context)
                
        except Exception as e:
            logger.error(f"類別搜尋執行失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": ""
            }
    
    def validate_input(self, input_data: Any) -> bool:
        """驗證輸入數據"""
        if not isinstance(input_data, dict):
            return False
        
        required_fields = ['query']
        return all(field in input_data for field in required_fields)

class RAGExpertAgent(BaseAgent):
    """
    RAG 檢索專家代理人
    
    此代理人負責語意檢索和向量搜尋，提供最相關的
    內容檢索功能。使用 intelligent_retrieval_expert 實作。
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化 RAG 專家代理人"""
        super().__init__("rag_expert", config)
        
        # 載入角色配置
        try:
            import sys
            import os
            config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
            if config_dir not in sys.path:
                sys.path.insert(0, config_dir)
            from agent_roles_config import get_agent_roles_manager
            self.role_config = get_agent_roles_manager().get_role("intelligent_retrieval_expert")
        except ImportError as e:
            logger.info(f"ℹ️ 無法載入角色配置: {e}")
            self.role_config = None
        
        # 初始化智能檢索專家
        try:
            from core.intelligent_retrieval_expert import get_intelligent_retrieval_expert
            self.intelligent_retrieval = get_intelligent_retrieval_expert()
        except ImportError as e:
            logger.warning(f"智能檢索專家導入失敗: {e}")
            self.intelligent_retrieval = None
    
    async def process(self, input_data: UserQuery) -> AgentResponse:
        """
        處理 RAG 檢索請求
        
        Args:
            input_data: 用戶查詢
            
        Returns:
            AgentResponse: 檢索結果
        """
        start_time = time.time()
        
        if not self.validate_input(input_data):
            return AgentResponse(
                content="輸入數據無效",
                confidence=0.0,
                reasoning="輸入數據驗證失敗",
                processing_time=time.time() - start_time
            )
        
        try:
            # 檢查智能檢索專家是否可用
            if not self.intelligent_retrieval:
                return AgentResponse(
                    content="智能檢索服務不可用",
                    confidence=0.3,
                    reasoning="智能檢索專家未初始化",
                    processing_time=time.time() - start_time,
                    metadata={"status": "SERVICE_UNAVAILABLE"}
                )
            
            # 使用智能檢索專家處理查詢
            retrieval_response = await self.intelligent_retrieval.process_query(input_data.query)
            
            # 格式化回應
            if retrieval_response.status == "SUCCESS":
                formatted_response = self.intelligent_retrieval.format_response(retrieval_response)
                
                return AgentResponse(
                    content=formatted_response,
                    confidence=retrieval_response.avg_confidence,
                    reasoning=f"使用智能檢索專家，找到 {retrieval_response.total_matches} 個相關結果",
                    processing_time=retrieval_response.processing_time,
                    metadata={
                        "status": "SUCCESS",
                        "total_matches": retrieval_response.total_matches,
                        "avg_confidence": retrieval_response.avg_confidence,
                        "results": [
                            {
                                "content": result.content,
                                "confidence": result.confidence,
                                "matched_tags": result.matched_tags
                            }
                            for result in retrieval_response.results
                        ]
                    }
                )
            
            elif retrieval_response.status == "NO_MATCH":
                return AgentResponse(
                    content="NO_MATCH",
                    confidence=0.0,
                    reasoning="信心分數低於閾值，未找到相關結果",
                    processing_time=retrieval_response.processing_time,
                    metadata={
                        "status": "NO_MATCH",
                        "avg_confidence": retrieval_response.avg_confidence
                    }
                )
            
            else:  # ERROR
                return AgentResponse(
                    content="檢索過程中發生錯誤",
                    confidence=0.0,
                    reasoning="智能檢索專家處理失敗",
                    processing_time=retrieval_response.processing_time,
                    metadata={
                        "status": "ERROR",
                        "avg_confidence": retrieval_response.avg_confidence
                    }
                )
                
        except Exception as e:
            logger.error(f"RAG 專家處理失敗: {e}")
            return AgentResponse(
                content="處理過程中發生異常",
                confidence=0.0,
                reasoning=f"異常：{str(e)}",
                processing_time=time.time() - start_time
            )
    
    async def _semantic_search(self, query: str) -> List[Dict[str, Any]]:
        """執行語意檢索"""
        # 實作語意檢索邏輯
        return [{"title": "語意檢索結果", "score": 0.9}]
    
    async def _vector_search(self, query: str) -> List[Dict[str, Any]]:
        """執行向量搜尋"""
        # 實作向量搜尋邏輯
        return [{"title": "向量搜尋結果", "score": 0.8}]
    
    def _merge_results(self, semantic: List, vector: List) -> List[Dict[str, Any]]:
        """合併搜尋結果"""
        return semantic + vector
    
    def _convert_web_result_to_podcasts(self, web_response: str) -> List[Dict[str, Any]]:
        """
        將 Web 搜尋結果轉換為 Podcast 格式
        
        Args:
            web_response: Web 搜尋回應文字
            
        Returns:
            List[Dict[str, Any]]: Podcast 格式的結果
        """
        # 這裡將 Web 搜尋結果轉換為 Podcast 格式
        # 由於 Web 搜尋返回的是文字，我們需要將其轉換為結構化的 Podcast 數據
        
        # 示例轉換邏輯（實際實作可能需要更複雜的解析）
        podcasts = []
        
        # 如果 Web 搜尋成功，創建一個通用的 Podcast 推薦
        if web_response and len(web_response.strip()) > 0:
            podcast = {
                "title": "Web 搜尋推薦",
                "description": web_response[:200] + "..." if len(web_response) > 200 else web_response,
                "rss_id": "web_search_001",
                "confidence": 0.85,  # Web 搜尋預設較高信心值
                "category": "混合",
                "tags": ["web_search", "openai"],
                "updated_at": datetime.now().isoformat()
            }
            podcasts.append(podcast)
        
        return podcasts


class SummaryExpertAgent(BaseAgent):
    """
    摘要生成專家代理人
    
    此代理人負責內容摘要生成，提供精準的內容分析
    和摘要功能。
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化摘要專家代理人"""
        super().__init__("Summary Expert", config)
        
        # 載入角色配置
        try:
            import sys
            import os
            config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
            if config_dir not in sys.path:
                sys.path.insert(0, config_dir)
            from agent_roles_config import get_agent_roles_manager
            self.role_config = get_agent_roles_manager().get_role("content_summary_expert")
        except ImportError as e:
            logger.info(f"ℹ️ 無法載入角色配置: {e}")
            self.role_config = None
    
    async def process(self, input_data: List[Dict[str, Any]]) -> AgentResponse:
        """
        處理摘要生成請求
        
        Args:
            input_data: 內容列表
            
        Returns:
            AgentResponse: 摘要結果
        """
        start_time = time.time()
        
        if not self.validate_input(input_data):
            return AgentResponse(
                content="輸入數據無效",
                confidence=0.0,
                reasoning="輸入數據驗證失敗",
                processing_time=time.time() - start_time
            )
        
        try:
            # 生成內容摘要
            summary = await self._generate_summary(input_data)
            
            processing_time = time.time() - start_time
            
            return AgentResponse(
                content=summary,
                confidence=0.9,
                reasoning="基於內容分析生成精準摘要",
                metadata={"summary_type": "content_analysis"},
                processing_time=processing_time
            )
                
        except Exception as e:
            logger.error(f"摘要專家處理失敗: {str(e)}")
            return AgentResponse(
                content="摘要生成過程中發生錯誤",
                confidence=0.3,
                reasoning=f"處理失敗: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    async def _generate_summary(self, content: List[Dict[str, Any]]) -> str:
        """生成摘要"""
        return "基於內容分析生成的 Podcast 摘要"


class TagClassificationExpertAgent(BaseAgent):
    """
    TAG 分類專家代理人
    
    此代理人負責使用 Excel 關聯詞庫對用戶輸入進行精準分類，
    提供商業/教育/其他類別的分類服務。
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化 TAG 分類專家代理人"""
        super().__init__("TAG Classification Expert", config)
        
        # 載入角色配置
        try:
            import sys
            import os
            config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
            if config_dir not in sys.path:
                sys.path.insert(0, config_dir)
            from agent_roles_config import get_agent_roles_manager
            self.role_config = get_agent_roles_manager().get_role("tag_classification_expert")
        except ImportError as e:
            logger.info(f"ℹ️ 無法載入角色配置: {e}")
            self.role_config = None
        
        # 初始化提示詞處理器
        self.prompt_processor = PromptProcessor()
    
    async def process(self, input_data: UserQuery) -> AgentResponse:
        """
        處理 TAG 分類請求
        
        Args:
            input_data: 用戶查詢
            
        Returns:
            AgentResponse: 分類結果
        """
        start_time = time.time()
        
        if not self.validate_input(input_data):
            return AgentResponse(
                content="輸入數據無效",
                confidence=0.0,
                reasoning="輸入數據驗證失敗",
                processing_time=time.time() - start_time
            )
        
        try:
            # 使用 Excel 關聯詞庫進行分類
            classification_result = await self._classify_with_excel_word_bank(input_data.query)
            
            # 格式化分類結果
            formatted_result = self._format_classification_result(classification_result)
            
            processing_time = time.time() - start_time
            
            return AgentResponse(
                content=formatted_result["content"],
                confidence=classification_result["primary_confidence"],
                reasoning=classification_result["classification_reasoning"],
                metadata={
                    "primary_category": classification_result["primary_category"],
                    "secondary_category": classification_result.get("secondary_category"),
                    "is_cross_category": classification_result["is_cross_category"],
                    "matched_keywords": classification_result["matched_keywords"],
                    "excel_word_bank_stats": classification_result["excel_word_bank_stats"]
                },
                processing_time=processing_time
            )
                
        except Exception as e:
            logger.error(f"TAG 分類專家處理失敗: {str(e)}")
            return AgentResponse(
                content="分類過程中發生錯誤",
                confidence=0.3,
                reasoning=f"處理失敗: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    async def _classify_with_excel_word_bank(self, query: str) -> Dict[str, Any]:
        """
        使用 Excel 關聯詞庫進行分類
        
        Args:
            query: 用戶查詢
            
        Returns:
            Dict[str, Any]: 分類結果
        """
        # 載入 Excel 關聯詞庫（模擬）
        word_bank = self._load_excel_word_bank()
        
        # 分析查詢中的關鍵詞
        matched_keywords = []
        business_score = 0.0
        education_score = 0.0
        other_score = 0.0
        
        query_lower = query.lower()
        
        # 商業類關鍵詞匹配
        for keyword in word_bank["business"]:
            if keyword in query_lower:
                business_score += 0.1
                matched_keywords.append({
                    "keyword": keyword,
                    "category": "商業",
                    "match_type": "精確匹配",
                    "weight": 0.8
                })
        
        # 教育類關鍵詞匹配
        for keyword in word_bank["education"]:
            if keyword in query_lower:
                education_score += 0.1
                matched_keywords.append({
                    "keyword": keyword,
                    "category": "教育",
                    "match_type": "精確匹配",
                    "weight": 0.8
                })
        
        # 其他類關鍵詞匹配
        for keyword in word_bank["other"]:
            if keyword in query_lower:
                other_score += 0.1
                matched_keywords.append({
                    "keyword": keyword,
                    "category": "其他",
                    "match_type": "精確匹配",
                    "weight": 0.8
                })
        
        # 正規化分數
        business_score = min(business_score, 1.0)
        education_score = min(education_score, 1.0)
        other_score = min(other_score, 1.0)
        
        # 決定主要類別
        scores = {
            "商業": business_score,
            "教育": education_score,
            "其他": other_score
        }
        
        primary_category = max(scores.items(), key=lambda x: x[1])[0]
        primary_confidence = scores[primary_category]
        
        # 決定次要類別
        remaining_scores = {k: v for k, v in scores.items() if k != primary_category}
        secondary_category = max(remaining_scores.items(), key=lambda x: x[1])[0] if remaining_scores else None
        secondary_confidence = remaining_scores[secondary_category] if secondary_category else 0.0
        
        # 判斷是否為跨類別
        is_cross_category = (primary_confidence > 0.6 and secondary_confidence > 0.4)
        
        # 生成分類理由
        if is_cross_category:
            reasoning = f"查詢同時包含{primary_category}({primary_confidence:.2f})和{secondary_category}({secondary_confidence:.2f})的特徵，屬於跨類別查詢"
        else:
            reasoning = f"查詢主要屬於{primary_category}類別，信心度: {primary_confidence:.2f}"
        
        return {
            "primary_category": primary_category,
            "primary_confidence": primary_confidence,
            "secondary_category": secondary_category,
            "secondary_confidence": secondary_confidence,
            "is_cross_category": is_cross_category,
            "matched_keywords": matched_keywords,
            "classification_reasoning": reasoning,
            "processing_suggestions": [
                f"建議1：針對{primary_category}類別進行深度處理",
                f"建議2：考慮{secondary_category}類別的相關內容" if secondary_category else "建議2：專注於單一類別處理"
            ],
            "excel_word_bank_stats": {
                "total_keywords_checked": len(word_bank["business"]) + len(word_bank["education"]) + len(word_bank["other"]),
                "business_matches": len([k for k in matched_keywords if k["category"] == "商業"]),
                "education_matches": len([k for k in matched_keywords if k["category"] == "教育"]),
                "other_matches": len([k for k in matched_keywords if k["category"] == "其他"])
            }
        }
    
    def _load_excel_word_bank(self) -> Dict[str, List[str]]:
        """
        載入 Excel 關聯詞庫
        
        Returns:
            Dict[str, List[str]]: 詞庫字典
        """
        # 模擬 Excel 詞庫數據
        return {
            "business": [
                "投資", "理財", "股票", "基金", "ETF", "債券", "期貨", "創業", 
                "職場", "科技", "經濟", "財務", "台積電", "美股", "台股", "獲利",
                "分析", "趨勢", "市場", "產業", "商業", "企業", "管理", "策略"
            ],
            "education": [
                "學習", "成長", "職涯", "心理", "溝通", "語言", "親子", "教育",
                "技能", "知識", "發展", "培訓", "課程", "讀書", "考試", "證照",
                "自我", "提升", "能力", "方法", "習慣", "目標", "規劃", "指導"
            ],
            "other": [
                "放鬆", "通勤", "睡前", "娛樂", "背景", "隨機", "音樂", "聊天",
                "生活", "日常", "休閒", "輕鬆", "有趣", "好玩", "消遣", "陪伴",
                "故事", "分享", "經驗", "心得", "感想", "討論", "話題", "閒聊"
            ]
        }
    
    def _format_classification_result(self, result: Dict[str, Any]) -> Dict[str, str]:
        """
        格式化分類結果
        
        Args:
            result: 分類結果
            
        Returns:
            Dict[str, str]: 格式化後的結果
        """
        content = f"📊 TAG 分類結果\n\n"
        content += f"🎯 主要類別: {result['primary_category']} (信心度: {result['primary_confidence']:.2f})\n"
        
        if result['secondary_category']:
            content += f"🎯 次要類別: {result['secondary_category']} (信心度: {result['secondary_confidence']:.2f})\n"
        
        if result['is_cross_category']:
            content += f"⚠️ 跨類別查詢: 是\n"
        
        content += f"\n🔍 匹配關鍵詞:\n"
        for keyword in result['matched_keywords'][:5]:  # 只顯示前5個
            content += f"  • {keyword['keyword']} ({keyword['category']})\n"
        
        content += f"\n📈 詞庫統計:\n"
        stats = result['excel_word_bank_stats']
        content += f"  • 商業匹配: {stats['business_matches']} 個\n"
        content += f"  • 教育匹配: {stats['education_matches']} 個\n"
        content += f"  • 其他匹配: {stats['other_matches']} 個\n"
        
        return {"content": content}





class TTSExpertAgent(BaseAgent):
    """
    TTS 專家代理人
    
    此代理人負責語音合成，提供高品質的語音
    生成功能。
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化 TTS 專家代理人"""
        super().__init__("TTS Expert", config)
        
        # 載入角色配置
        try:
            import sys
            import os
            config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
            if config_dir not in sys.path:
                sys.path.insert(0, config_dir)
            from agent_roles_config import get_agent_roles_manager
            self.role_config = get_agent_roles_manager().get_role("tts_expert")
        except ImportError as e:
            logger.info(f"ℹ️ 無法載入角色配置: {e}")
            self.role_config = None
    
    async def process(self, input_data: str) -> AgentResponse:
        """
        處理語音合成請求
        
        Args:
            input_data: 文本內容
            
        Returns:
            AgentResponse: 語音合成結果
        """
        start_time = time.time()
        
        if not self.validate_input(input_data):
            return AgentResponse(
                content="輸入數據無效",
                confidence=0.0,
                reasoning="輸入數據驗證失敗",
                processing_time=time.time() - start_time
            )
        
        try:
            # 生成語音
            audio_url = await self._generate_speech(input_data)
            
            processing_time = time.time() - start_time
            
            return AgentResponse(
                content="語音合成完成",
                confidence=0.95,
                reasoning="使用 Edge TW 語音模型生成自然語音",
                metadata={"audio_url": audio_url, "voice_model": "edge_tw"},
                processing_time=processing_time
            )
                
        except Exception as e:
            logger.error(f"TTS 專家處理失敗: {str(e)}")
            return AgentResponse(
                content="語音合成過程中發生錯誤",
                confidence=0.3,
                reasoning=f"處理失敗: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    async def _generate_speech(self, text: str) -> str:
        """生成語音"""
        return "generated_audio_url.mp3"


class UserManagerAgent(BaseAgent):
    """
    用戶管理專家代理人
    
    此代理人負責用戶 ID 管理和記錄追蹤，提供
    完整的用戶行為分析功能。
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化用戶管理專家代理人"""
        super().__init__("User Manager", config)
        
        # 載入角色配置
        try:
            import sys
            import os
            config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
            if config_dir not in sys.path:
                sys.path.insert(0, config_dir)
            from agent_roles_config import get_agent_roles_manager
            self.role_config = get_agent_roles_manager().get_role("user_experience_expert")
        except ImportError as e:
            logger.info(f"ℹ️ 無法載入角色配置: {e}")
            self.role_config = None
    
    async def process(self, input_data: UserQuery) -> AgentResponse:
        """
        處理用戶管理請求
        
        Args:
            input_data: 用戶查詢
            
        Returns:
            AgentResponse: 用戶管理結果
        """
        start_time = time.time()
        
        if not self.validate_input(input_data):
            return AgentResponse(
                content="輸入數據無效",
                confidence=0.0,
                reasoning="輸入數據驗證失敗",
                processing_time=time.time() - start_time
            )
        
        try:
            # 驗證用戶 ID
            is_valid = await self._validate_user_id(input_data.user_id)
            
            # 記錄用戶行為
            await self._log_user_behavior(input_data)
            
            processing_time = time.time() - start_time
            
            return AgentResponse(
                content=f"用戶 {input_data.user_id} 驗證{'成功' if is_valid else '失敗'}",
                confidence=0.9 if is_valid else 0.3,
                reasoning="完成用戶 ID 驗證和行為記錄",
                metadata={"user_id": input_data.user_id, "is_valid": is_valid},
                processing_time=processing_time
            )
                
        except Exception as e:
            logger.error(f"用戶管理專家處理失敗: {str(e)}")
            return AgentResponse(
                content="用戶管理過程中發生錯誤",
                confidence=0.3,
                reasoning=f"處理失敗: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    async def _validate_user_id(self, user_id: str) -> bool:
        """驗證用戶 ID"""
        return len(user_id) >= 3 and user_id.isalnum()
    
    async def _log_user_behavior(self, query: UserQuery) -> None:
        """記錄用戶行為"""
        logger.info(f"記錄用戶行為: {query.user_id} - {query.query}")


# ==================== 第二層：類別專家層 ====================

class BusinessExpertAgent(BaseAgent):
    """
    商業專家代理人
    
    此代理人專門處理商業類別的查詢，提供專業的
    商業分析和推薦功能。
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化商業專家代理人"""
        super().__init__("Business Expert", config)
        
        # 載入角色配置
        try:
            import sys
            import os
            config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
            if config_dir not in sys.path:
                sys.path.insert(0, config_dir)
            from agent_roles_config import get_agent_roles_manager
            self.role_config = get_agent_roles_manager().get_role("business_intelligence_expert")
        except ImportError as e:
            logger.info(f"ℹ️ 無法載入角色配置: {e}")
            self.role_config = None
        
        self.prompt_processor = PromptProcessor()
    
    async def process(self, input_data: UserQuery) -> AgentResponse:
        """
        處理商業類別查詢
        
        Args:
            input_data: 用戶查詢
            
        Returns:
            AgentResponse: 商業分析結果
        """
        start_time = time.time()
        
        if not self.validate_input(input_data):
            return AgentResponse(
                content="輸入數據無效",
                confidence=0.0,
                reasoning="輸入數據驗證失敗",
                processing_time=time.time() - start_time
            )
        
        try:
            # 使用 PromptProcessor 進行專家評估
            # 首先需要獲取檢索結果（這裡暫時使用模擬數據）
            search_results = await self._get_search_results(input_data.query)
            
            # 使用提示詞模板進行商業專家評估
            prompt_result = await self.prompt_processor.process_business_expert(
                search_results=search_results,
                user_question=input_data.query,
                trace_id=input_data.context  # 假設 context 包含 trace_id
            )
            
            processing_time = time.time() - start_time
            
            return AgentResponse(
                content=prompt_result.content,
                confidence=prompt_result.confidence,
                reasoning="使用商業專家提示詞模板進行評估",
                metadata=prompt_result.metadata,
                processing_time=processing_time
            )
                
        except Exception as e:
            logger.error(f"商業專家處理失敗: {str(e)}")
            return AgentResponse(
                content="商業分析過程中發生錯誤",
                confidence=0.3,
                reasoning=f"處理失敗: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    async def _get_search_results(self, query: str) -> List[Dict[str, Any]]:
        """獲取檢索結果（暫時使用模擬數據）"""
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
    
    # 保留原有的方法作為備用
    def _analyze_business_relevance(self, query: str) -> float:
        """分析商業相關性"""
        business_keywords = ["股票", "投資", "理財", "財經", "市場", "經濟"]
        query_lower = query.lower()
        
        relevance = 0.0
        for keyword in business_keywords:
            if keyword in query_lower:
                relevance += 0.2
        
        return min(relevance, 1.0)
    
    async def _generate_business_recommendations(self, query: str) -> List[Dict[str, Any]]:
        """生成商業推薦"""
        return [{"title": "商業推薦", "category": "商業", "confidence": 0.8}]


class EducationExpertAgent(BaseAgent):
    """
    教育專家代理人
    
    此代理人專門處理教育類別的查詢，提供專業的
    教育分析和推薦功能。
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化教育專家代理人"""
        super().__init__("Education Expert", config)
        
        # 載入角色配置
        try:
            import sys
            import os
            config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
            if config_dir not in sys.path:
                sys.path.insert(0, config_dir)
            from agent_roles_config import get_agent_roles_manager
            self.role_config = get_agent_roles_manager().get_role("educational_growth_strategist")
        except ImportError as e:
            logger.info(f"ℹ️ 無法載入角色配置: {e}")
            self.role_config = None
        
        self.prompt_processor = PromptProcessor()
    
    async def process(self, input_data: UserQuery) -> AgentResponse:
        """
        處理教育類別查詢
        
        Args:
            input_data: 用戶查詢
            
        Returns:
            AgentResponse: 教育分析結果
        """
        start_time = time.time()
        
        if not self.validate_input(input_data):
            return AgentResponse(
                content="輸入數據無效",
                confidence=0.0,
                reasoning="輸入數據驗證失敗",
                processing_time=time.time() - start_time
            )
        
        try:
            # 使用 PromptProcessor 進行專家評估
            # 首先需要獲取檢索結果（這裡暫時使用模擬數據）
            search_results = await self._get_search_results(input_data.query)
            
            # 使用提示詞模板進行教育專家評估
            prompt_result = await self.prompt_processor.process_education_expert(
                search_results=search_results,
                user_question=input_data.query,
                trace_id=input_data.context  # 假設 context 包含 trace_id
            )
            
            processing_time = time.time() - start_time
            
            return AgentResponse(
                content=prompt_result.content,
                confidence=prompt_result.confidence,
                reasoning="使用教育專家提示詞模板進行評估",
                metadata=prompt_result.metadata,
                processing_time=processing_time
            )
                
        except Exception as e:
            logger.error(f"教育專家處理失敗: {str(e)}")
            return AgentResponse(
                content="教育分析過程中發生錯誤",
                confidence=0.3,
                reasoning=f"處理失敗: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    async def _get_search_results(self, query: str) -> List[Dict[str, Any]]:
        """獲取檢索結果（暫時使用模擬數據）"""
        return [
            {
                "title": "好葉 EP56_學習方法大公開",
                "episode": "EP56",
                "rss_id": "better_leaf_56",
                "category": "教育",
                "similarity_score": 0.8,
                "tag_score": 0.75,
                "hybrid_score": 0.785,
                "updated_at": "2024-01-12",
                "summary": "分享高效學習方法和技巧"
            }
        ]
    
    # 保留原有的方法作為備用
    def _analyze_education_relevance(self, query: str) -> float:
        """分析教育相關性"""
        education_keywords = ["學習", "技能", "成長", "職涯", "發展", "教育"]
        query_lower = query.lower()
        
        relevance = 0.0
        for keyword in education_keywords:
            if keyword in query_lower:
                relevance += 0.2
        
        return min(relevance, 1.0)
    
    async def _generate_education_recommendations(self, query: str) -> List[Dict[str, Any]]:
        """生成教育推薦"""
        return [{"title": "教育推薦", "category": "教育", "confidence": 0.8}]


# ==================== 第一層：領導者層 ====================

class LeaderAgent(BaseAgent):
    """
    領導者代理人
    
    此代理人作為三層架構的協調者，負責整合各層專家的
    結果並做出最終決策。
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """初始化領導者代理人"""
        super().__init__("Leader", config)
        
        # 載入角色配置
        try:
            import sys
            import os
            config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
            if config_dir not in sys.path:
                sys.path.insert(0, config_dir)
            from agent_roles_config import get_agent_roles_manager
            self.role_config = get_agent_roles_manager().get_role("chief_decision_orchestrator")
        except ImportError as e:
            logger.info(f"ℹ️ 無法載入角色配置: {e}")
            self.role_config = None
        
        # 初始化下層專家（容錯模式）
        try:
            self.rag_expert = RAGExpertAgent(config.get('rag_expert', {}))
        except Exception as e:
            logger.warning(f"RAG 專家初始化失敗: {e}")
            self.rag_expert = None
            
        try:
            self.summary_expert = SummaryExpertAgent(config.get('summary_expert', {}))
        except Exception as e:
            logger.warning(f"摘要專家初始化失敗: {e}")
            self.summary_expert = None
            
        try:
            self.tag_classification_expert = TagClassificationExpertAgent(config.get('tag_classification_expert', {}))
        except Exception as e:
            logger.warning(f"TAG 分類專家初始化失敗: {e}")
            self.tag_classification_expert = None
            
        try:
            self.tts_expert = TTSExpertAgent(config.get('tts_expert', {}))
        except Exception as e:
            logger.warning(f"TTS 專家初始化失敗: {e}")
            self.tts_expert = None
            
        try:
            self.user_manager = UserManagerAgent(config.get('user_manager', {}))
        except Exception as e:
            logger.warning(f"用戶管理專家初始化失敗: {e}")
            self.user_manager = None
        
        # 類別專家（容錯模式）
        try:
            self.business_expert = BusinessExpertAgent(config.get('business_expert', {}))
        except Exception as e:
            logger.warning(f"商業專家初始化失敗: {e}")
            self.business_expert = None
            
        try:
            self.education_expert = EducationExpertAgent(config.get('education_expert', {}))
        except Exception as e:
            logger.warning(f"教育專家初始化失敗: {e}")
            self.education_expert = None
    
    async def process(self, input_data: UserQuery) -> AgentResponse:
        """
        處理查詢並協調各層專家
        
        Args:
            input_data: 用戶查詢
            
        Returns:
            AgentResponse: 最終決策結果
        """
        start_time = time.time()
        
        if not self.validate_input(input_data):
            return AgentResponse(
                content="輸入數據無效",
                confidence=0.0,
                reasoning="輸入數據驗證失敗",
                processing_time=time.time() - start_time
            )
        
        try:
            # 1. 用戶管理層
            if self.user_manager:
                user_result = await self.user_manager.process(input_data)
            else:
                user_result = AgentResponse(
                    content="用戶管理服務不可用",
                    confidence=0.5,
                    reasoning="用戶管理專家未初始化",
                    metadata={"user_management_available": False}
                )
            
            # 2. 根據類別決定處理方式
            if input_data.category == "商業":
                # 商業類別：交給商業專家處理
                if self.business_expert:
                    category_result = await self.business_expert.process(input_data)
                else:
                    category_result = AgentResponse(
                        content="商業專家服務不可用",
                        confidence=0.3,
                        reasoning="商業專家未初始化",
                        metadata={"business_expert_available": False}
                    )
                if self.rag_expert:
                    rag_result = await self.rag_expert.process(input_data)
                else:
                    rag_result = AgentResponse(
                        content="RAG 專家服務不可用",
                        confidence=0.3,
                        reasoning="RAG 專家未初始化",
                        metadata={"rag_expert_available": False}
                    )
            elif input_data.category == "教育":
                # 教育類別：交給教育專家處理
                if self.education_expert:
                    category_result = await self.education_expert.process(input_data)
                else:
                    category_result = AgentResponse(
                        content="教育專家服務不可用",
                        confidence=0.3,
                        reasoning="教育專家未初始化",
                        metadata={"education_expert_available": False}
                    )
                if self.rag_expert:
                    rag_result = await self.rag_expert.process(input_data)
                else:
                    rag_result = AgentResponse(
                        content="RAG 專家服務不可用",
                        confidence=0.3,
                        reasoning="RAG 專家未初始化",
                        metadata={"rag_expert_available": False}
                    )
            else:
                # 其他類別：直接由 Leader 處理 RAG，不交給類別專家
                category_result = AgentResponse(
                    content="其他類別查詢",
                    confidence=0.5,
                    reasoning="其他類別由 Leader 直接處理",
                    metadata={"category": "其他"}
                )
                if self.rag_expert:
                    rag_result = await self.rag_expert.process(input_data)
                else:
                    rag_result = AgentResponse(
                        content="RAG 專家服務不可用",
                        confidence=0.3,
                        reasoning="RAG 專家未初始化",
                        metadata={"rag_expert_available": False}
                    )
            
            # 3. 功能專家層（所有類別都使用）
            if self.summary_expert and rag_result.metadata.get("results"):
                summary_result = await self.summary_expert.process(rag_result.metadata.get("results", []))
            else:
                summary_result = AgentResponse(
                    content="摘要服務不可用",
                    confidence=0.3,
                    reasoning="摘要專家未初始化或無結果可摘要",
                    metadata={"summary_expert_available": False}
                )
            
            # 使用 TAG 分類專家進行分類
            if self.tag_classification_expert:
                tag_classification_result = await self.tag_classification_expert.process(input_data)
            else:
                tag_classification_result = AgentResponse(
                    content="TAG 分類服務不可用",
                    confidence=0.3,
                    reasoning="TAG 分類專家未初始化",
                    metadata={"tag_classification_expert_available": False}
                )
            
            # 4. 最終決策
            final_response = await self._make_final_decision(
                input_data, rag_result, category_result, summary_result, tag_classification_result
            )
            
            processing_time = time.time() - start_time
            
            return AgentResponse(
                content=final_response,
                confidence=min(rag_result.confidence, category_result.confidence),
                reasoning="基於三層專家協作的最終決策",
                metadata={
                    "user_result": user_result.metadata,
                    "rag_result": rag_result.metadata,
                    "category_result": category_result.metadata,
                    "summary_result": summary_result.metadata,
                    "tag_classification_result": tag_classification_result.metadata
                },
                processing_time=processing_time
            )
                
        except Exception as e:
            logger.error(f"領導者代理人處理失敗: {str(e)}")
            return AgentResponse(
                content="處理過程中發生錯誤",
                confidence=0.3,
                reasoning=f"處理失敗: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    async def _analyze_dual_category(self, input_data: UserQuery) -> AgentResponse:
        """分析雙類別情況"""
        business_result = await self.business_expert.process(input_data)
        education_result = await self.education_expert.process(input_data)
        
        # 選擇信心值較高的結果
        if business_result.confidence > education_result.confidence:
            return business_result
        else:
            return education_result
    
    async def _make_final_decision(self, query: UserQuery, rag_result: AgentResponse, 
                                 category_result: AgentResponse, summary_result: AgentResponse, 
                                 tag_classification_result: AgentResponse) -> str:
        """做出最終決策"""
        # 整合各專家的結果
        response_parts = []
        
        # 添加類別分析
        response_parts.append(f"根據您的查詢，我將其分類為 {query.category or '混合'} 類別")
        
        # 添加檢索結果
        response_parts.append(rag_result.content)
        
        # 添加摘要
        if summary_result.content:
            response_parts.append(f"內容摘要: {summary_result.content}")
        
        # 添加 TAG 分類結果
        if tag_classification_result.content:
            response_parts.append(f"TAG 分類: {tag_classification_result.content}")
        
        return "\n\n".join(response_parts)


# ==================== 代理人管理器 ====================

class AgentManager:
    """
    代理人管理器
    
    此類別負責管理所有代理人，提供統一的介面來
    處理用戶查詢和協調代理人協作。
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        初始化代理人管理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.leader_agent = LeaderAgent(config.get('leader', {}))
        
        logger.info("代理人管理器初始化完成")
    
    async def process_query(self, query: str, user_id: str, 
                          category: Optional[str] = None) -> AgentResponse:
        """
        處理用戶查詢
        
        Args:
            query: 查詢內容
            user_id: 用戶 ID
            category: 預分類類別
            
        Returns:
            AgentResponse: 處理結果
        """
        try:
            # 創建用戶查詢對象
            user_query = UserQuery(
                query=query,
                user_id=user_id,
                category=category
            )
            
            # 委託給領導者代理人處理
            return await self.leader_agent.process(user_query)
            
        except Exception as e:
            logger.error(f"查詢處理失敗: {str(e)}")
            return AgentResponse(
                content="查詢處理失敗",
                confidence=0.0,
                reasoning=f"處理失敗: {str(e)}",
                processing_time=0.0
            )
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        獲取代理人狀態
        
        Returns:
            Dict: 代理人狀態資訊
        """
        return {
            "leader_agent": {
                "name": self.leader_agent.agent_name,
                "role": self.leader_agent.role,
                "status": "active"
            },
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        } 