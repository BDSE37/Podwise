#!/usr/bin/env python3
"""
層級化樹狀結構 RAG Pipeline
實現查詢重寫、混合搜尋、檢索增強、重新排序、上下文壓縮、混合式RAG的完整架構
"""

import os
import logging
import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import yaml

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class QueryContext:
    """查詢上下文"""
    original_query: str
    rewritten_query: str
    intent: str
    entities: List[str]
    domain: str
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class SearchResult:
    """搜尋結果"""
    document_id: str
    content: str
    score: float
    source: str
    metadata: Dict[str, Any]

@dataclass
class RAGResponse:
    """RAG 回應"""
    content: str
    confidence: float
    sources: List[str]
    processing_time: float
    level_used: str
    metadata: Dict[str, Any]

class RAGLevel(ABC):
    """RAG 層級抽象基類"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get('name', 'Unknown')
        self.confidence_threshold = config.get('confidence_threshold', 0.7)
        self.fallback_strategy = config.get('fallback_strategy', None)
    
    @abstractmethod
    async def process(self, input_data: Any) -> Tuple[Any, float]:
        """處理輸入數據"""
        pass
    
    async def should_fallback(self, confidence: float) -> bool:
        """判斷是否需要降級"""
        return confidence < self.confidence_threshold

class Level1QueryProcessing(RAGLevel):
    """第一層：查詢重寫轉換拓展"""
    
    async def process(self, input_data: str) -> Tuple[QueryContext, float]:
        """處理查詢重寫、轉換和拓展"""
        logger.info(f"🔍 {self.name}: 處理查詢重寫轉換拓展")
        
        start_time = time.time()
        
        try:
            # 查詢重寫
            rewritten_query = await self._rewrite_query(input_data)
            
            # 意圖識別
            intent = await self._recognize_intent(input_data)
            
            # 實體識別
            entities = await self._extract_entities(input_data)
            
            # 領域分類
            domain = await self._classify_domain(input_data)
            
            # 計算信心值
            confidence = await self._calculate_confidence(
                rewritten_query, intent, entities, domain
            )
            
            processing_time = time.time() - start_time
            
            context = QueryContext(
                original_query=input_data,
                rewritten_query=rewritten_query,
                intent=intent,
                entities=entities,
                domain=domain,
                confidence=confidence,
                metadata={
                    'processing_time': processing_time,
                    'level': 'query_processing'
                }
            )
            
            logger.info(f"✅ {self.name}: 信心值 {confidence:.3f}, 處理時間 {processing_time:.3f}s")
            return context, confidence
            
        except Exception as e:
            logger.error(f"❌ {self.name}: 處理失敗 - {e}")
            return None, 0.0
    
    async def _rewrite_query(self, query: str) -> str:
        """查詢重寫"""
        # 這裡可以整合 T5 或 BART 模型進行查詢重寫
        # 目前使用簡化的同義詞擴展
        synonyms = {
            '推薦': ['建議', '介紹', '分享'],
            '播客': ['podcast', '音頻節目', '廣播'],
            '科技': ['技術', '科技', '創新']
        }
        
        rewritten = query
        for word, syns in synonyms.items():
            if word in query:
                # 隨機選擇一個同義詞替換
                import random
                rewritten = rewritten.replace(word, random.choice(syns))
        
        return rewritten
    
    async def _recognize_intent(self, query: str) -> str:
        """意圖識別"""
        intents = {
            'recommendation': ['推薦', '建議', '介紹'],
            'analysis': ['分析', '研究', '探討'],
            'comparison': ['比較', '對比', '差異'],
            'explanation': ['解釋', '說明', '介紹']
        }
        
        for intent, keywords in intents.items():
            if any(keyword in query for keyword in keywords):
                return intent
        
        return 'general'
    
    async def _extract_entities(self, query: str) -> List[str]:
        """實體識別"""
        # 簡化的實體識別
        entities = []
        if '播客' in query:
            entities.append('podcast')
        if '科技' in query:
            entities.append('technology')
        if '推薦' in query:
            entities.append('recommendation')
        
        return entities
    
    async def _classify_domain(self, query: str) -> str:
        """領域分類"""
        domains = {
            'business': ['商業', '創業', '投資', '市場'],
            'education': ['教育', '學習', '課程', '知識']
        }
        
        for domain, keywords in domains.items():
            if any(keyword in query for keyword in keywords):
                return domain
        
        return 'general'
    
    async def _calculate_confidence(self, rewritten: str, intent: str, entities: List[str], domain: str) -> float:
        """計算信心值"""
        confidence = 0.0
        
        # 重寫查詢的相似度
        if rewritten != self.config.get('original_query', ''):
            confidence += 0.3
        
        # 意圖識別的準確性
        if intent != 'general':
            confidence += 0.2
        
        # 實體識別的數量
        confidence += min(len(entities) * 0.1, 0.2)
        
        # 領域分類的準確性
        if domain != 'general':
            confidence += 0.3
        
        return min(confidence, 1.0)

class Level2HybridSearch(RAGLevel):
    """第二層：混合搜尋"""
    
    async def process(self, input_data: QueryContext) -> Tuple[List[SearchResult], float]:
        """執行混合搜尋"""
        logger.info(f"🔍 {self.name}: 執行混合搜尋")
        
        start_time = time.time()
        
        try:
            # 密集檢索
            dense_results = await self._dense_retrieval(input_data.rewritten_query)
            
            # 稀疏檢索
            sparse_results = await self._sparse_retrieval(input_data.rewritten_query)
            
            # 語義搜尋
            semantic_results = await self._semantic_search(input_data.rewritten_query)
            
            # 混合融合
            fused_results = await self._hybrid_fusion(dense_results, sparse_results, semantic_results)
            
            processing_time = time.time() - start_time
            
            # 計算信心值
            confidence = await self._calculate_search_confidence(fused_results)
            
            logger.info(f"✅ {self.name}: 檢索到 {len(fused_results)} 個結果, 信心值 {confidence:.3f}")
            return fused_results, confidence
            
        except Exception as e:
            logger.error(f"❌ {self.name}: 搜尋失敗 - {e}")
            return [], 0.0
    
    async def _dense_retrieval(self, query: str) -> List[SearchResult]:
        """密集檢索"""
        # 模擬密集檢索結果
        return [
            SearchResult(
                document_id="doc_001",
                content="這是一個關於科技播客的詳細介紹...",
                score=0.85,
                source="dense_retrieval",
                metadata={'method': 'dense', 'model': 'bge-large-zh'}
            ),
            SearchResult(
                document_id="doc_002", 
                content="最新的科技趨勢分析報告...",
                score=0.78,
                source="dense_retrieval",
                metadata={'method': 'dense', 'model': 'bge-large-zh'}
            )
        ]
    
    async def _sparse_retrieval(self, query: str) -> List[SearchResult]:
        """稀疏檢索"""
        # 模擬稀疏檢索結果
        return [
            SearchResult(
                document_id="doc_003",
                content="BM25 檢索到的相關文檔...",
                score=0.72,
                source="sparse_retrieval",
                metadata={'method': 'sparse', 'algorithm': 'bm25'}
            )
        ]
    
    async def _semantic_search(self, query: str) -> List[SearchResult]:
        """語義搜尋"""
        # 模擬語義搜尋結果
        return [
            SearchResult(
                document_id="doc_004",
                content="語義相關的播客內容...",
                score=0.80,
                source="semantic_search",
                metadata={'method': 'semantic', 'model': 'sentence-transformers'}
            )
        ]
    
    async def _hybrid_fusion(self, dense_results: List[SearchResult], 
                           sparse_results: List[SearchResult], 
                           semantic_results: List[SearchResult]) -> List[SearchResult]:
        """混合融合"""
        all_results = dense_results + sparse_results + semantic_results
        
        # 按分數排序
        all_results.sort(key=lambda x: x.score, reverse=True)
        
        # 去重（基於 document_id）
        seen_ids = set()
        unique_results = []
        for result in all_results:
            if result.document_id not in seen_ids:
                seen_ids.add(result.document_id)
                unique_results.append(result)
        
        return unique_results[:10]  # 返回前10個結果
    
    async def _calculate_search_confidence(self, results: List[SearchResult]) -> float:
        """計算搜尋信心值"""
        if not results:
            return 0.0
        
        # 基於結果數量和平均分數計算信心值
        avg_score = sum(r.score for r in results) / len(results)
        result_count_factor = min(len(results) / 5, 1.0)  # 最多5個結果為滿分
        
        confidence = (avg_score * 0.7 + result_count_factor * 0.3)
        return min(confidence, 1.0)

class Level3RetrievalAugmentation(RAGLevel):
    """第三層：檢索增強"""
    
    async def process(self, input_data: List[SearchResult]) -> Tuple[List[SearchResult], float]:
        """執行檢索增強"""
        logger.info(f"🔍 {self.name}: 執行檢索增強")
        
        start_time = time.time()
        
        try:
            augmented_results = []
            
            for result in input_data:
                # 上下文增強
                augmented_content = await self._augment_context(result)
                
                # 知識圖譜整合
                knowledge_enhanced = await self._integrate_knowledge_graph(augmented_content)
                
                # 外部數據融合
                external_enhanced = await self._fuse_external_data(knowledge_enhanced)
                
                # 創建增強後的結果
                augmented_result = SearchResult(
                    document_id=result.document_id,
                    content=external_enhanced,
                    score=result.score * 1.1,  # 增強後分數略高
                    source=result.source,
                    metadata={
                        **result.metadata,
                        'augmented': True,
                        'context_enhanced': True,
                        'knowledge_integrated': True,
                        'external_fused': True
                    }
                )
                
                augmented_results.append(augmented_result)
            
            processing_time = time.time() - start_time
            
            # 計算信心值
            confidence = await self._calculate_augmentation_confidence(augmented_results)
            
            logger.info(f"✅ {self.name}: 增強了 {len(augmented_results)} 個結果, 信心值 {confidence:.3f}")
            return augmented_results, confidence
            
        except Exception as e:
            logger.error(f"❌ {self.name}: 增強失敗 - {e}")
            return input_data, 0.0
    
    async def _augment_context(self, result: SearchResult) -> str:
        """上下文增強"""
        # 模擬上下文增強
        enhanced_content = f"[上下文增強] {result.content} [包含相關背景信息]"
        return enhanced_content
    
    async def _integrate_knowledge_graph(self, content: str) -> str:
        """知識圖譜整合"""
        # 模擬知識圖譜整合
        enhanced_content = f"[知識圖譜] {content} [整合實體關係]"
        return enhanced_content
    
    async def _fuse_external_data(self, content: str) -> str:
        """外部數據融合"""
        # 模擬外部數據融合
        enhanced_content = f"[外部數據] {content} [融合最新信息]"
        return enhanced_content
    
    async def _calculate_augmentation_confidence(self, results: List[SearchResult]) -> float:
        """計算增強信心值"""
        if not results:
            return 0.0
        
        # 基於增強標記計算信心值
        augmented_count = sum(1 for r in results if r.metadata.get('augmented', False))
        confidence = augmented_count / len(results)
        
        return confidence

class Level4Reranking(RAGLevel):
    """第四層：重新排序"""
    
    async def process(self, input_data: List[SearchResult]) -> Tuple[List[SearchResult], float]:
        """執行重新排序"""
        logger.info(f"🔍 {self.name}: 執行重新排序")
        
        start_time = time.time()
        
        try:
            # 多準則排序
            multi_criteria_ranked = await self._multi_criteria_ranking(input_data)
            
            # 個人化排序
            personalized_ranked = await self._personalization_ranking(multi_criteria_ranked)
            
            # 多樣性排序
            diversity_ranked = await self._diversity_ranking(personalized_ranked)
            
            processing_time = time.time() - start_time
            
            # 計算信心值
            confidence = await self._calculate_ranking_confidence(diversity_ranked)
            
            logger.info(f"✅ {self.name}: 重新排序完成, 信心值 {confidence:.3f}")
            return diversity_ranked, confidence
            
        except Exception as e:
            logger.error(f"❌ {self.name}: 重新排序失敗 - {e}")
            return input_data, 0.0
    
    async def _multi_criteria_ranking(self, results: List[SearchResult]) -> List[SearchResult]:
        """多準則排序"""
        # 模擬多準則排序
        for result in results:
            # 調整分數基於多個準則
            relevance_score = result.score * 0.4
            freshness_score = 0.8 * 0.2  # 假設新鮮度為0.8
            authority_score = 0.7 * 0.2  # 假設權威性為0.7
            diversity_score = 0.6 * 0.1  # 假設多樣性為0.6
            novelty_score = 0.9 * 0.1    # 假設新穎性為0.9
            
            result.score = relevance_score + freshness_score + authority_score + diversity_score + novelty_score
        
        # 重新排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    async def _personalization_ranking(self, results: List[SearchResult]) -> List[SearchResult]:
        """個人化排序"""
        # 模擬個人化排序（基於用戶偏好）
        user_preferences = {
            'technology': 1.2,
            'business': 1.1,
            'entertainment': 0.9
        }
        
        for result in results:
            # 根據內容調整分數
            if '科技' in result.content:
                result.score *= user_preferences.get('technology', 1.0)
            elif '商業' in result.content:
                result.score *= user_preferences.get('business', 1.0)
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    async def _diversity_ranking(self, results: List[SearchResult]) -> List[SearchResult]:
        """多樣性排序"""
        # 模擬多樣性排序
        diverse_results = []
        seen_topics = set()
        
        for result in results:
            # 簡單的多樣性檢查
            topic = self._extract_topic(result.content)
            if topic not in seen_topics or len(diverse_results) < 3:
                diverse_results.append(result)
                seen_topics.add(topic)
        
        return diverse_results[:5]  # 返回前5個多樣化結果
    
    def _extract_topic(self, content: str) -> str:
        """提取主題"""
        topics = ['科技', '商業', '娛樂', '教育']
        for topic in topics:
            if topic in content:
                return topic
        return 'general'
    
    async def _calculate_ranking_confidence(self, results: List[SearchResult]) -> float:
        """計算排序信心值"""
        if not results:
            return 0.0
        
        # 基於排序一致性和分數分布計算信心值
        scores = [r.score for r in results]
        avg_score = sum(scores) / len(scores)
        score_variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        
        # 分數越高，方差越小，信心值越高
        confidence = avg_score * (1 - score_variance)
        return min(max(confidence, 0.0), 1.0)

class Level5ContextCompression(RAGLevel):
    """第五層：上下文壓縮過濾"""
    
    async def process(self, input_data: List[SearchResult]) -> Tuple[List[SearchResult], float]:
        """執行上下文壓縮過濾"""
        logger.info(f"🔍 {self.name}: 執行上下文壓縮過濾")
        
        start_time = time.time()
        
        try:
            compressed_results = []
            
            for result in input_data:
                # 上下文壓縮
                compressed_content = await self._compress_context(result.content)
                
                # 信息過濾
                filtered_content = await self._filter_information(compressed_content)
                
                # 創建壓縮後的結果
                compressed_result = SearchResult(
                    document_id=result.document_id,
                    content=filtered_content,
                    score=result.score,
                    source=result.source,
                    metadata={
                        **result.metadata,
                        'compressed': True,
                        'filtered': True,
                        'compression_ratio': len(filtered_content) / len(result.content)
                    }
                )
                
                compressed_results.append(compressed_result)
            
            processing_time = time.time() - start_time
            
            # 計算信心值
            confidence = await self._calculate_compression_confidence(compressed_results)
            
            logger.info(f"✅ {self.name}: 壓縮了 {len(compressed_results)} 個結果, 信心值 {confidence:.3f}")
            return compressed_results, confidence
            
        except Exception as e:
            logger.error(f"❌ {self.name}: 壓縮失敗 - {e}")
            return input_data, 0.0
    
    async def _compress_context(self, content: str) -> str:
        """上下文壓縮"""
        # 模擬上下文壓縮（提取關鍵信息）
        import re
        
        # 移除冗餘信息
        compressed = re.sub(r'\[.*?\]', '', content)  # 移除方括號內容
        compressed = re.sub(r'\s+', ' ', compressed)  # 合併多個空格
        
        # 限制長度
        if len(compressed) > 200:
            compressed = compressed[:200] + "..."
        
        return compressed
    
    async def _filter_information(self, content: str) -> str:
        """信息過濾"""
        # 模擬信息過濾
        # 移除低質量內容
        filtered = content
        
        # 移除常見的無用詞
        stop_words = ['這個', '那個', '一些', '很多', '非常']
        for word in stop_words:
            filtered = filtered.replace(word, '')
        
        return filtered
    
    async def _calculate_compression_confidence(self, results: List[SearchResult]) -> float:
        """計算壓縮信心值"""
        if not results:
            return 0.0
        
        # 基於壓縮比例和信息保留度計算信心值
        total_compression_ratio = 0.0
        compressed_count = 0
        
        for result in results:
            if result.metadata.get('compressed', False):
                compression_ratio = result.metadata.get('compression_ratio', 1.0)
                total_compression_ratio += compression_ratio
                compressed_count += 1
        
        if compressed_count == 0:
            return 0.0
        
        avg_compression_ratio = total_compression_ratio / compressed_count
        
        # 理想的壓縮比例在 0.3-0.7 之間
        if 0.3 <= avg_compression_ratio <= 0.7:
            confidence = 0.9
        elif avg_compression_ratio < 0.3:
            confidence = avg_compression_ratio / 0.3 * 0.9
        else:
            confidence = (1.0 - avg_compression_ratio) / 0.3 * 0.9
        
        return min(confidence, 1.0)

class Level6HybridRAG(RAGLevel):
    """第六層：混合式RAG"""
    
    async def process(self, input_data: List[SearchResult]) -> Tuple[RAGResponse, float]:
        """執行混合式RAG生成"""
        logger.info(f"🔍 {self.name}: 執行混合式RAG生成")
        
        start_time = time.time()
        
        try:
            # 多模型生成
            multi_model_response = await self._multi_model_generation(input_data)
            
            # 自適應生成
            adaptive_response = await self._adaptive_generation(multi_model_response, input_data)
            
            # 質量控制
            quality_controlled_response = await self._quality_control(adaptive_response)
            
            processing_time = time.time() - start_time
            
            # 創建最終回應
            rag_response = RAGResponse(
                content=quality_controlled_response,
                confidence=0.9,  # 最終層級通常有較高信心值
                sources=[r.document_id for r in input_data[:3]],  # 前3個來源
                processing_time=processing_time,
                level_used='hybrid_rag',
                metadata={
                    'models_used': ['qwen2.5-7b', 'deepseek-coder-6.7b'],
                    'quality_controlled': True,
                    'adaptive_generation': True
                }
            )
            
            logger.info(f"✅ {self.name}: 生成完成, 處理時間 {processing_time:.3f}s")
            return rag_response, 0.9
            
        except Exception as e:
            logger.error(f"❌ {self.name}: 生成失敗 - {e}")
            return None, 0.0
    
    async def _multi_model_generation(self, results: List[SearchResult]) -> str:
        """多模型生成"""
        # 模擬多模型生成
        context = "\n".join([r.content for r in results[:3]])
        
        # 使用不同模型生成
        qwen_response = f"[Qwen2.5-7B] 基於檢索結果，我推薦以下播客節目：{context[:100]}..."
        deepseek_response = f"[DeepSeek-Coder] 根據分析，這些是相關的科技播客：{context[:100]}..."
        
        # 融合回應
        combined_response = f"{qwen_response}\n\n{deepseek_response}"
        return combined_response
    
    async def _adaptive_generation(self, base_response: str, results: List[SearchResult]) -> str:
        """自適應生成"""
        # 根據檢索結果調整生成策略
        if len(results) > 5:
            # 豐富的檢索結果，生成詳細回應
            adaptive_response = f"[詳細模式] {base_response} [包含深度分析]"
        else:
            # 有限的檢索結果，生成簡潔回應
            adaptive_response = f"[簡潔模式] {base_response} [重點摘要]"
        
        return adaptive_response
    
    async def _quality_control(self, response: str) -> str:
        """質量控制"""
        # 模擬質量控制
        # 檢查事實準確性
        if '播客' in response and '推薦' in response:
            quality_response = f"[質量驗證通過] {response}"
        else:
            quality_response = f"[需要改進] {response}"
        
        return quality_response

class HierarchicalRAGPipeline:
    """層級化樹狀結構 RAG Pipeline"""
    
    def __init__(self, config_path: str = "config/hierarchical_rag_config.yaml"):
        """
        初始化層級化 RAG Pipeline
        
        Args:
            config_path: 配置文件路徑
        """
        self.config = self._load_config(config_path)
        self.levels = self._initialize_levels()
        self.fallback_service = None  # AnythingLLM 備援服務
        
        logger.info("🌳 層級化樹狀結構 RAG Pipeline 初始化完成")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """載入配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"✅ 配置載入成功: {config_path}")
            return config
        except Exception as e:
            logger.error(f"❌ 配置載入失敗: {e}")
            return {}
    
    def _initialize_levels(self) -> Dict[str, RAGLevel]:
        """初始化各層級"""
        levels = {}
        
        # 初始化各層級
        hierarchical_config = self.config.get('hierarchical_structure', {})
        
        levels['level_1'] = Level1QueryProcessing(
            hierarchical_config.get('level_1_query_processing', {})
        )
        
        levels['level_2'] = Level2HybridSearch(
            hierarchical_config.get('level_2_hybrid_search', {})
        )
        
        levels['level_3'] = Level3RetrievalAugmentation(
            hierarchical_config.get('level_3_retrieval_augmentation', {})
        )
        
        levels['level_4'] = Level4Reranking(
            hierarchical_config.get('level_4_reranking', {})
        )
        
        levels['level_5'] = Level5ContextCompression(
            hierarchical_config.get('level_5_context_compression', {})
        )
        
        levels['level_6'] = Level6HybridRAG(
            hierarchical_config.get('level_6_hybrid_rag', {})
        )
        
        logger.info(f"✅ 初始化了 {len(levels)} 個層級")
        return levels
    
    async def process_query(self, query: str) -> RAGResponse:
        """
        處理查詢（層級化處理）
        
        Args:
            query: 使用者查詢
            
        Returns:
            RAGResponse: 最終回應
        """
        logger.info(f"🚀 開始層級化處理查詢: {query[:50]}...")
        
        start_time = time.time()
        current_input = query
        level_used = "fallback"
        
        try:
            # 第一層：查詢處理
            level_1_result, confidence_1 = await self.levels['level_1'].process(current_input)
            if confidence_1 >= self.levels['level_1'].confidence_threshold:
                current_input = level_1_result
                level_used = "level_1"
                logger.info(f"✅ 第一層處理成功，信心值: {confidence_1:.3f}")
            else:
                logger.warning(f"⚠️ 第一層信心值不足 ({confidence_1:.3f})，嘗試第二層")
            
            # 第二層：混合搜尋
            level_2_result, confidence_2 = await self.levels['level_2'].process(current_input)
            if confidence_2 >= self.levels['level_2'].confidence_threshold:
                current_input = level_2_result
                level_used = "level_2"
                logger.info(f"✅ 第二層處理成功，信心值: {confidence_2:.3f}")
            else:
                logger.warning(f"⚠️ 第二層信心值不足 ({confidence_2:.3f})，嘗試第三層")
            
            # 第三層：檢索增強
            level_3_result, confidence_3 = await self.levels['level_3'].process(current_input)
            if confidence_3 >= self.levels['level_3'].confidence_threshold:
                current_input = level_3_result
                level_used = "level_3"
                logger.info(f"✅ 第三層處理成功，信心值: {confidence_3:.3f}")
            else:
                logger.warning(f"⚠️ 第三層信心值不足 ({confidence_3:.3f})，嘗試第四層")
            
            # 第四層：重新排序
            level_4_result, confidence_4 = await self.levels['level_4'].process(current_input)
            if confidence_4 >= self.levels['level_4'].confidence_threshold:
                current_input = level_4_result
                level_used = "level_4"
                logger.info(f"✅ 第四層處理成功，信心值: {confidence_4:.3f}")
            else:
                logger.warning(f"⚠️ 第四層信心值不足 ({confidence_4:.3f})，嘗試第五層")
            
            # 第五層：上下文壓縮
            level_5_result, confidence_5 = await self.levels['level_5'].process(current_input)
            if confidence_5 >= self.levels['level_5'].confidence_threshold:
                current_input = level_5_result
                level_used = "level_5"
                logger.info(f"✅ 第五層處理成功，信心值: {confidence_5:.3f}")
            else:
                logger.warning(f"⚠️ 第五層信心值不足 ({confidence_5:.3f})，嘗試第六層")
            
            # 第六層：混合式RAG
            level_6_result, confidence_6 = await self.levels['level_6'].process(current_input)
            if confidence_6 >= self.levels['level_6'].confidence_threshold:
                level_used = "level_6"
                logger.info(f"✅ 第六層處理成功，信心值: {confidence_6:.3f}")
                
                # 更新最終回應的層級信息
                level_6_result.level_used = level_used
                return level_6_result
            else:
                logger.warning(f"⚠️ 第六層信心值不足 ({confidence_6:.3f})，使用備援服務")
        
        except Exception as e:
            logger.error(f"❌ 層級化處理失敗: {e}")
        
        # 備援服務
        logger.info("🔄 使用備援服務 (AnythingLLM)")
        fallback_response = await self._fallback_service(query)
        
        total_time = time.time() - start_time
        
        return RAGResponse(
            content=fallback_response,
            confidence=0.8,  # 備援服務的預設信心值
            sources=[],
            processing_time=total_time,
            level_used="fallback",
            metadata={'fallback_used': True, 'error': 'All levels failed'}
        )
    
    async def _fallback_service(self, query: str) -> str:
        """備援服務"""
        # 模擬 AnythingLLM 備援服務
        return f"[備援服務] 基於您的查詢「{query}」，我建議您查看相關的播客節目。由於系統正在優化中，請稍後再試。"

async def main():
    """主函數"""
    # 建立層級化 RAG Pipeline
    pipeline = HierarchicalRAGPipeline()
    
    # 測試查詢
    test_queries = [
        "請推薦一些科技類的播客節目",
        "分析最近播客產業的發展趨勢",
        "比較不同播客平台的特色"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"測試查詢: {query}")
        print(f"{'='*60}")
        
        response = await pipeline.process_query(query)
        
        print(f"回應內容: {response.content}")
        print(f"信心值: {response.confidence}")
        print(f"使用層級: {response.level_used}")
        print(f"處理時間: {response.processing_time:.3f}s")
        print(f"來源: {response.sources}")

if __name__ == "__main__":
    asyncio.run(main()) 