#!/usr/bin/env python3
"""
第一層：查詢重寫轉換拓展
"""

import logging
import time
from typing import Tuple, List
from .base_level import RAGLevel
from ..hierarchical_rag_pipeline import QueryContext

logger = logging.getLogger(__name__)

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
        # 簡單的查詢重寫邏輯
        rewritten = query
        
        # 擴展縮寫
        abbreviations = {
            'podcast': '播客節目',
            '推薦': '推薦',
            '科技': '科技類',
            '商業': '商業類',
            '教育': '教育類'
        }
        
        for abbr, full in abbreviations.items():
            if abbr in query:
                rewritten = rewritten.replace(abbr, full)
        
        return rewritten
    
    async def _recognize_intent(self, query: str) -> str:
        """意圖識別"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['推薦', '建議', '介紹']):
            return 'recommendation'
        elif any(word in query_lower for word in ['分析', '比較', '評估']):
            return 'analysis'
        elif any(word in query_lower for word in ['搜尋', '找', '查詢']):
            return 'search'
        else:
            return 'general'
    
    async def _extract_entities(self, query: str) -> List[str]:
        """實體識別"""
        entities = []
        
        # 簡單的實體識別
        entity_keywords = ['科技', '商業', '教育', '投資', '理財', '職涯', '學習']
        
        for keyword in entity_keywords:
            if keyword in query:
                entities.append(keyword)
        
        return entities
    
    async def _classify_domain(self, query: str) -> str:
        """領域分類"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['股票', '投資', '理財', '經濟', '商業']):
            return 'business'
        elif any(word in query_lower for word in ['學習', '教育', '職涯', '成長', '技能']):
            return 'education'
        elif any(word in query_lower for word in ['科技', 'AI', '人工智慧', '程式']):
            return 'technology'
        else:
            return 'general'
    
    async def _calculate_confidence(self, rewritten: str, intent: str, entities: List[str], domain: str) -> float:
        """計算信心值"""
        confidence = 0.5  # 基礎信心值
        
        # 根據重寫效果調整
        if len(rewritten) > len(entities) * 2:
            confidence += 0.2
        
        # 根據意圖明確性調整
        if intent != 'general':
            confidence += 0.1
        
        # 根據實體數量調整
        if len(entities) > 0:
            confidence += 0.1
        
        # 根據領域明確性調整
        if domain != 'general':
            confidence += 0.1
        
        return min(confidence, 1.0) 