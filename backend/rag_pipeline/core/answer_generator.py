#!/usr/bin/env python3
"""
Podwise RAG Pipeline 回答生成器

實現分層的回答生成邏輯：
1. CrewAI + LangChain + LLM 檢索 Milvus 根據系統提示詞生成回答
2. default_qa_processor.py 根據預設 Q&A 模糊比對文本相似度高就按照這一份回答
3. web_search_tool.py OpenAI 去搜尋生成回覆

主要生成邏輯依照 agent_roles_config.py

作者: Podwise Team
版本: 1.0.0
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re

# 導入摘要相關工具
try:
    from tools.summary_generator import get_summary_generator
    from tools.cross_db_text_fetcher import get_cross_db_text_fetcher
    SUMMARY_TOOLS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"摘要工具導入失敗: {e}")
    SUMMARY_TOOLS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class PodcastRecommendation:
    """Podcast 推薦資料結構"""
    title: str
    episode: str
    podcast_name: str
    description: str
    confidence: float
    category: str
    source: str
    rss_id: Optional[str] = None
    audio_url: Optional[str] = None
    image_url: Optional[str] = None


@dataclass
class AnswerGenerationResult:
    """回答生成結果"""
    content: str
    confidence: float
    sources: List[str]
    processing_time: float
    level_used: str
    recommendations: List[PodcastRecommendation]
    metadata: Dict[str, Any]


class AnswerGenerator:
    """回答生成器"""
    
    def __init__(self, 
                 llm_manager=None,
                 default_qa_processor=None,
                 web_search_tool=None,
                 prompt_templates=None,
                 agent_roles_manager=None):
        """
        初始化回答生成器
        
        Args:
            llm_manager: LLM 管理器
            default_qa_processor: 預設問答處理器
            web_search_tool: Web 搜尋工具
            prompt_templates: 提示詞模板
            agent_roles_manager: 代理角色管理器
        """
        self.llm_manager = llm_manager
        self.default_qa_processor = default_qa_processor
        self.web_search_tool = web_search_tool
        self.prompt_templates = prompt_templates
        self.agent_roles_manager = agent_roles_manager
        
        logger.info("✅ 回答生成器初始化完成")
    
    async def generate_answer(self, 
                            query: str,
                            user_id: str,
                            search_results: List[Any] = None,
                            category: str = "其他",
                            user_context: Dict[str, Any] = None) -> AnswerGenerationResult:
        """
        生成回答 - 按照分層邏輯處理
        
        Args:
            query: 用戶查詢
            user_id: 用戶 ID
            search_results: 搜尋結果
            category: 分類
            user_context: 用戶上下文
            
        Returns:
            AnswerGenerationResult: 回答生成結果
        """
        start_time = datetime.now()
        
        try:
            # 步驟 0: 檢查是否為摘要查詢
            if SUMMARY_TOOLS_AVAILABLE and self._is_summary_query(query):
                logger.info("檢測到摘要查詢，使用摘要生成器")
                summary_result = await self._generate_summary_response(query, user_context)
                if summary_result:
                    return summary_result
            
            # 步驟 1: CrewAI + LangChain + LLM 檢索 Milvus 根據系統提示詞生成回答
            logger.info("步驟 1: 使用 CrewAI + LangChain + LLM 生成回答")
            llm_result = await self._generate_with_llm_and_prompts(query, search_results or [], category, user_context or {})
            
            if llm_result and llm_result.confidence >= 0.7:
                logger.info(f"LLM 生成成功，信心度: {llm_result.confidence}")
                return llm_result
            
            # 步驟 2: 檢查預設問答處理器
            logger.info("步驟 2: 檢查預設問答處理器")
            if self.default_qa_processor:
                qa_result = await self._generate_with_default_qa(query, user_context)
                if qa_result and qa_result.confidence >= 0.6:
                    logger.info(f"預設問答匹配成功，信心度: {qa_result.confidence}")
                    return qa_result
            
            # 步驟 3: 使用 Web 搜尋
            logger.info("步驟 3: 使用 Web 搜尋")
            web_result = await self._generate_with_web_search(query, category, user_context)
            if web_result and web_result.confidence >= 0.5:
                logger.info(f"Web 搜尋成功，信心度: {web_result.confidence}")
                return web_result
            
            # 步驟 4: 預設回應
            logger.info("步驟 4: 使用預設回應")
            return await self._generate_default_response(query, user_context)
            
        except Exception as e:
            logger.error(f"回答生成失敗: {e}")
            return AnswerGenerationResult(
                content="抱歉，處理您的查詢時發生錯誤。",
                confidence=0.0,
                sources=["error"],
                processing_time=(datetime.now() - start_time).total_seconds(),
                level_used="error",
                recommendations=[],
                metadata={"error": str(e)}
            )
    
    async def _generate_with_llm_and_prompts(self, 
                                           query: str,
                                           search_results: List[Any],
                                           category: str,
                                           user_context: Dict[str, Any]) -> Optional[AnswerGenerationResult]:
        """使用 LLM 和提示詞模板生成回答"""
        try:
            if not self.llm_manager or not self.prompt_templates:
                return None
            
            # 獲取回答生成提示詞模板
            try:
                from config.prompt_templates import get_prompt_template, format_prompt
                answer_template = get_prompt_template("answer_generation")
            except ImportError:
                logger.warning("無法導入提示詞模板")
                return None
            
            # 格式化搜尋結果
            formatted_results = self._format_search_results_for_prompt(search_results)
            
            # 格式化提示詞
            formatted_prompt = format_prompt(
                answer_template,
                leader_decision=formatted_results,
                user_question=query,
                user_context=user_context or {}
            )
            
            # 使用 LLM 生成回答
            if hasattr(self.llm_manager, 'generate_text'):
                from llm.core.base_llm import GenerationRequest
                request = GenerationRequest(prompt=formatted_prompt)
                response = await self.llm_manager.generate_text(request)
                content = response.text if response else ""
            else:
                content = ""
            
            if content:
                # 解析推薦節目
                recommendations = self._extract_recommendations_from_content(content, search_results)
                
                return AnswerGenerationResult(
                    content=content,
                    confidence=0.8,
                    sources=["llm_prompt"],
                    processing_time=0.0,
                    level_used="llm_prompt",
                    recommendations=recommendations,
                    metadata={"prompt_used": "answer_generation"}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"LLM 提示詞生成失敗: {e}")
            return None
    
    async def _generate_with_default_qa(self, 
                                      query: str,
                                      user_context: Dict[str, Any]) -> Optional[AnswerGenerationResult]:
        """使用預設問答處理器生成回答"""
        try:
            if not self.default_qa_processor:
                return None
            
            # 尋找最佳匹配
            match_result = self.default_qa_processor.find_best_match(query, 0.6)
            if not match_result:
                return None
            
            qa, confidence = match_result
            
            # 使用提示詞模板格式化回應
            try:
                from config.prompt_templates import get_prompt_template, format_prompt
                faq_template = get_prompt_template("faq_fallback")
                content = format_prompt(
                    faq_template,
                    user_question=query,
                    matched_faq=qa.question,
                    suggested_categories=["商業", "教育", "其他"]
                )
            except ImportError:
                content = qa.answer
            
            return AnswerGenerationResult(
                content=content,
                confidence=confidence,
                sources=["default_qa"],
                processing_time=0.0,
                level_used="default_qa",
                recommendations=[],
                metadata={"category": qa.category, "tags": qa.tags}
            )
            
        except Exception as e:
            logger.error(f"預設問答生成失敗: {e}")
            return None
    
    async def _generate_with_web_search(self, 
                                      query: str,
                                      category: str,
                                      user_context: Dict[str, Any]) -> Optional[AnswerGenerationResult]:
        """使用 Web 搜尋生成回答"""
        try:
            if not self.web_search_tool:
                return None
            
            from tools.web_search_tool import SearchRequest
            search_request = SearchRequest(
                query=f"{query} podcast 推薦",
                max_results=3,
                language="zh-TW"
            )
            
            web_results = await self.web_search_tool.search(search_request)
            
            if hasattr(web_results, 'results') and web_results.results:
                content = self._format_web_results_for_answer(web_results.results, query)
                confidence = getattr(web_results, 'confidence', 0.6)
                
                return AnswerGenerationResult(
                    content=content,
                    confidence=confidence,
                    sources=["web_search"],
                    processing_time=0.0,
                    level_used="web_search",
                    recommendations=[],
                    metadata={"results_count": len(web_results.results)}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Web 搜尋生成失敗: {e}")
            return None
    
    async def _generate_default_response(self, 
                                       query: str,
                                       user_context: Dict[str, Any]) -> AnswerGenerationResult:
        """生成預設回應"""
        try:
            # 使用預設回應提示詞
            try:
                from config.prompt_templates import get_prompt_template, format_prompt
                default_template = get_prompt_template("default_fallback")
                content = format_prompt(default_template, user_question=query)
            except ImportError:
                content = "抱歉，我無法找到相關的資訊。請嘗試重新描述您的需求。"
            
            return AnswerGenerationResult(
                content=content,
                confidence=0.0,
                sources=["default"],
                processing_time=0.0,
                level_used="default",
                recommendations=[],
                metadata={"fallback": True}
            )
            
        except Exception as e:
            logger.error(f"預設回應生成失敗: {e}")
            return AnswerGenerationResult(
                content="抱歉，處理您的查詢時發生錯誤。",
                confidence=0.0,
                sources=["error"],
                processing_time=0.0,
                level_used="error",
                recommendations=[],
                metadata={"error": str(e)}
            )
    
    def _format_search_results_for_prompt(self, search_results: List[Any]) -> str:
        """格式化搜尋結果用於提示詞"""
        if not search_results:
            return "無相關搜尋結果"
        
        formatted_results = []
        for i, result in enumerate(search_results[:3], 1):
            if hasattr(result, 'content'):
                content = result.content
                if hasattr(result, 'episode_title') and result.episode_title:
                    content = f"{result.episode_title}: {content}"
                formatted_results.append(f"{i}. {content}")
        
        return "\n".join(formatted_results)
    
    def _extract_recommendations_from_content(self, content: str, search_results: List[Any]) -> List[PodcastRecommendation]:
        """從內容中提取推薦節目"""
        recommendations = []
        
        # 從搜尋結果中提取
        if search_results:
            for result in search_results[:3]:
                if hasattr(result, 'content'):
                    recommendation = PodcastRecommendation(
                        title=getattr(result, 'episode_title', '未知標題'),
                        episode=getattr(result, 'episode', ''),
                        podcast_name=getattr(result, 'podcast_name', '未知頻道'),
                        description=result.content[:100] + "..." if len(result.content) > 100 else result.content,
                        confidence=getattr(result, 'confidence', 0.7),
                        category=getattr(result, 'category', '其他'),
                        source="vector_search",
                        rss_id=getattr(result, 'rss_id', None),
                        audio_url=getattr(result, 'audio_url', None),
                        image_url=getattr(result, 'image_url', None)
                    )
                    recommendations.append(recommendation)
        
        return recommendations
    
    def _format_web_results_for_answer(self, web_results: List[Any], query: str) -> str:
        """格式化 Web 搜尋結果為回答"""
        if not web_results:
            return "抱歉，我無法找到相關的資訊。"
        
        # 根據查詢類型生成不同格式的回答
        if "推薦" in query or "podcast" in query.lower():
            # 推薦格式
            content = f"根據您的查詢「{query}」，我為您找到以下相關資訊：\n\n"
            
            for i, result in enumerate(web_results[:3], 1):
                title = getattr(result, 'title', '未知標題')
                snippet = getattr(result, 'snippet', '')
                
                content += f"{i}. {title}\n"
                if snippet:
                    content += f"   {snippet[:80]}...\n"
                content += "\n"
            
            content += "💡 建議您可以進一步描述您的具體需求，我可以為您提供更精準的推薦！"
        else:
            # 一般資訊格式
            content = "我為您找到以下相關資訊：\n\n"
            
            for i, result in enumerate(web_results[:2], 1):
                title = getattr(result, 'title', '未知標題')
                snippet = getattr(result, 'snippet', '')
                
                content += f"{i}. {title}\n"
                if snippet:
                    content += f"   {snippet}\n\n"
        
        return content
    
    def ensure_different_channels(self, recommendations: List[PodcastRecommendation]) -> List[PodcastRecommendation]:
        """確保推薦的節目來自不同頻道"""
        if not recommendations:
            return recommendations
        
        # 按信心度排序
        sorted_recommendations = sorted(recommendations, key=lambda x: x.confidence, reverse=True)
        
        # 確保不同頻道
        unique_channels = set()
        final_recommendations = []
        
        for rec in sorted_recommendations:
            if rec.podcast_name not in unique_channels:
                unique_channels.add(rec.podcast_name)
                final_recommendations.append(rec)
                
                # 最多推薦 3 個不同頻道的節目
                if len(final_recommendations) >= 3:
                    break
        
        return final_recommendations
    
    def format_recommendations_for_display(self, recommendations: List[PodcastRecommendation]) -> str:
        """格式化推薦節目用於顯示"""
        if not recommendations:
            return ""
        
        # 確保不同頻道
        unique_recommendations = self.ensure_different_channels(recommendations)
        
        content = ""
        for i, rec in enumerate(unique_recommendations, 1):
            content += f"{i}. 《{rec.podcast_name}》：{rec.title}\n"
            if rec.description:
                content += f"   {rec.description}\n"
            content += f"   ⭐ 信心度：{rec.confidence:.1f}\n\n"
        
        return content
    
    def _is_summary_query(self, query: str) -> bool:
        """
        檢測是否為摘要查詢
        
        Args:
            query: 用戶查詢
            
        Returns:
            bool: 是否為摘要查詢
        """
        # 檢測摘要相關關鍵詞
        summary_keywords = ['摘要', 'summary', '總結', '概要', '重點']
        episode_patterns = [r'EP\d+', r'ep\d+', r'第\d+集', r'集數']
        
        # 檢查是否包含摘要關鍵詞
        has_summary_keyword = any(keyword in query for keyword in summary_keywords)
        
        # 檢查是否包含集數模式
        has_episode_pattern = any(re.search(pattern, query) for pattern in episode_patterns)
        
        return has_summary_keyword and has_episode_pattern
    
    async def _generate_summary_response(self, query: str, user_context: Dict[str, Any]) -> Optional[AnswerGenerationResult]:
        """
        生成摘要回應
        
        Args:
            query: 用戶查詢
            user_context: 用戶上下文
            
        Returns:
            Optional[AnswerGenerationResult]: 摘要回應結果
        """
        try:
            # 解析查詢中的 podcast 和 episode 資訊
            podcast_name, episode_tag = self._extract_podcast_episode_info(query)
            
            if not podcast_name or not episode_tag:
                logger.warning(f"無法解析 podcast 和 episode 資訊: {query}")
                return None
            
            # 獲取文本擷取器
            text_fetcher = get_cross_db_text_fetcher()
            await text_fetcher.connect_databases()
            
            # 擷取長文本
            fetch_result = await text_fetcher.fetch_text(podcast_name, episode_tag)
            
            if not fetch_result.success:
                logger.warning(f"文本擷取失敗: {fetch_result.error_message}")
                return AnswerGenerationResult(
                    content=f"抱歉，無法找到「{podcast_name} {episode_tag}」的相關內容。請確認節目名稱和集數是否正確。",
                    confidence=0.0,
                    sources=["text_fetch_error"],
                    processing_time=fetch_result.processing_time,
                    level_used="summary_error",
                    recommendations=[],
                    metadata={"error": fetch_result.error_message}
                )
            
            # 獲取摘要生成器
            summary_generator = get_summary_generator()
            
            # 生成摘要
            summary_result = await summary_generator.generate_summary(fetch_result.text, max_words=150)
            
            if not summary_result.success:
                logger.warning(f"摘要生成失敗: {summary_result.error_message}")
                return AnswerGenerationResult(
                    content=f"抱歉，生成「{podcast_name} {episode_tag}」摘要時發生錯誤。",
                    confidence=0.0,
                    sources=["summary_error"],
                    processing_time=summary_result.processing_time,
                    level_used="summary_error",
                    recommendations=[],
                    metadata={"error": summary_result.error_message}
                )
            
            # 構建回應內容
            content = f"📝 **{podcast_name} {episode_tag} 摘要**\n\n"
            content += f"{summary_result.summary}\n\n"
            content += f"💡 摘要字數：{summary_result.word_count} 字"
            
            return AnswerGenerationResult(
                content=content,
                confidence=0.9,
                sources=["mongodb_text", "summary_generator"],
                processing_time=fetch_result.processing_time + summary_result.processing_time,
                level_used="summary_generation",
                recommendations=[],
                metadata={
                    "podcast_name": podcast_name,
                    "episode_tag": episode_tag,
                    "summary_quality": summary_result.quality_score,
                    "original_text_length": len(fetch_result.text)
                }
            )
            
        except Exception as e:
            logger.error(f"摘要回應生成失敗: {e}")
            return None
    
    def _extract_podcast_episode_info(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """
        從查詢中提取 podcast 名稱和 episode 標籤
        
        Args:
            query: 用戶查詢
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (podcast_name, episode_tag)
        """
        try:
            # 移除摘要相關關鍵詞
            cleaned_query = query
            summary_keywords = ['摘要', 'summary', '總結', '概要', '重點', '我想知道']
            for keyword in summary_keywords:
                cleaned_query = cleaned_query.replace(keyword, '').strip()
            
            # 尋找 EP 模式 - 更寬鬆的匹配
            ep_patterns = [
                r'([^E]*?)(EP\d+)',  # 標準 EP 模式
                r'([^e]*?)(ep\d+)',  # 小寫 ep 模式
                r'([^集]*?)(EP\d+)',  # 包含「集」字的模式
                r'([^集]*?)(ep\d+)',  # 包含「集」字的小寫模式
            ]
            
            for pattern in ep_patterns:
                match = re.search(pattern, cleaned_query, re.IGNORECASE)
                if match:
                    podcast_name = match.group(1).strip()
                    episode_tag = match.group(2).upper()  # 統一為大寫
                    
                    # 清理 podcast_name，移除多餘的詞彙
                    podcast_name = re.sub(r'[集摘要總結概要重點]', '', podcast_name).strip()
                    
                    if podcast_name and episode_tag:
                        logger.info(f"解析結果: podcast_name='{podcast_name}', episode_tag='{episode_tag}'")
                        return podcast_name, episode_tag
            
            # 尋找其他集數模式
            episode_patterns = [
                r'([^第]*?)(第\d+集)',
                r'([^集]*?)(\d+集)',
            ]
            
            for pattern in episode_patterns:
                match = re.search(pattern, cleaned_query)
                if match:
                    podcast_name = match.group(1).strip()
                    episode_tag = match.group(2)
                    
                    # 清理 podcast_name
                    podcast_name = re.sub(r'[摘要總結概要重點]', '', podcast_name).strip()
                    
                    if podcast_name and episode_tag:
                        logger.info(f"解析結果: podcast_name='{podcast_name}', episode_tag='{episode_tag}'")
                        return podcast_name, episode_tag
            
            logger.warning(f"無法解析 podcast 和 episode 資訊: {query}")
            return None, None
            
        except Exception as e:
            logger.error(f"提取 podcast 和 episode 資訊失敗: {e}")
            return None, None


def create_answer_generator(llm_manager=None,
                           default_qa_processor=None,
                           web_search_tool=None,
                           prompt_templates=None,
                           agent_roles_manager=None) -> AnswerGenerator:
    """創建回答生成器實例"""
    return AnswerGenerator(
        llm_manager=llm_manager,
        default_qa_processor=default_qa_processor,
        web_search_tool=web_search_tool,
        prompt_templates=prompt_templates,
        agent_roles_manager=agent_roles_manager
    ) 