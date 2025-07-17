#!/usr/bin/env python3
"""
Summary Generator

長文本摘要生成工具，用於將長文本濃縮為 ≤150 字的繁體中文摘要

功能：
- 智能文本分析
- 關鍵資訊萃取
- 繁體中文摘要生成
- 品質檢核

作者: Podwise Team
版本: 1.0.0
"""

import logging
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import asyncio

# LLM 相關導入
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("openai 未安裝，將使用備援摘要方法")

logger = logging.getLogger(__name__)


@dataclass
class SummaryResult:
    """摘要生成結果"""
    success: bool
    summary: str = ""
    word_count: int = 0
    quality_score: float = 0.0
    error_message: str = ""
    processing_time: float = 0.0


class SummaryGenerator:
    """摘要生成器"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: str = "gpt-4o-mini",
                 temperature: float = 0.4,
                 max_tokens: int = 200):
        """
        初始化摘要生成器
        
        Args:
            api_key: OpenAI API 金鑰
            model: 使用的模型名稱
            temperature: 生成溫度
            max_tokens: 最大 token 數
        """
        self.api_key = api_key or self._get_api_key()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if OPENAI_AVAILABLE and self.api_key:
            openai.api_key = self.api_key
        
        logger.info(f"SummaryGenerator 初始化完成，模型: {self.model}")
    
    def _get_api_key(self) -> Optional[str]:
        """獲取 API 金鑰"""
        import os
        return os.getenv("OPENAI_API_KEY")
    
    async def generate_summary(self, text: str, max_words: int = 150) -> SummaryResult:
        """
        生成文本摘要
        
        Args:
            text: 輸入文本
            max_words: 最大字數限制
            
        Returns:
            SummaryResult: 摘要結果
        """
        import time
        start_time = time.time()
        
        try:
            # 文本預處理
            cleaned_text = self._preprocess_text(text)
            
            # 生成摘要
            if OPENAI_AVAILABLE and self.api_key:
                summary = await self._generate_with_openai(cleaned_text, max_words)
            else:
                summary = self._generate_fallback(cleaned_text, max_words)
            
            if not summary:
                return SummaryResult(
                    success=False,
                    error_message="摘要生成失敗",
                    processing_time=time.time() - start_time
                )
            
            # 品質檢核
            quality_score = self._check_quality(summary, cleaned_text)
            
            # 字數統計
            word_count = len(summary)
            
            # 如果品質不合格，回傳錯誤
            if quality_score < 0.6:
                return SummaryResult(
                    success=False,
                    error_message="摘要品質不符合要求",
                    processing_time=time.time() - start_time
                )
            
            return SummaryResult(
                success=True,
                summary=summary,
                word_count=word_count,
                quality_score=quality_score,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"摘要生成失敗: {e}")
            return SummaryResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def _preprocess_text(self, text: str) -> str:
        """
        文本預處理
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理後的文本
        """
        # 移除多餘空白
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除特殊字符（保留中文、英文、數字、標點）
        text = re.sub(r'[^\u4e00-\u9fff\w\s，。！？；：""''（）【】\-]', '', text)
        
        # 限制文本長度（避免 token 過多）
        if len(text) > 4000:
            text = text[:4000] + "..."
        
        return text
    
    async def _generate_with_openai(self, text: str, max_words: int) -> Optional[str]:
        """
        使用 OpenAI 生成摘要
        
        Args:
            text: 輸入文本
            max_words: 最大字數
            
        Returns:
            Optional[str]: 生成的摘要
        """
        try:
            prompt = self._build_summary_prompt(text, max_words)
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一個專業的文本摘要專家，專門將長文本濃縮為簡潔的繁體中文摘要。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            summary = response.choices[0].message.content.strip()
            
            # 確保摘要不超過字數限制
            if len(summary) > max_words:
                summary = summary[:max_words]
            
            return summary
            
        except Exception as e:
            logger.error(f"OpenAI 摘要生成失敗: {e}")
            return None
    
    def _generate_fallback(self, text: str, max_words: int) -> str:
        """
        備援摘要生成方法
        
        Args:
            text: 輸入文本
            max_words: 最大字數
            
        Returns:
            str: 生成的摘要
        """
        try:
            # 簡單的關鍵句提取
            sentences = re.split(r'[。！？]', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            # 選擇前幾個句子作為摘要
            summary_parts = []
            current_length = 0
            
            for sentence in sentences:
                if current_length + len(sentence) <= max_words:
                    summary_parts.append(sentence)
                    current_length += len(sentence)
                else:
                    break
            
            summary = "。".join(summary_parts) + "。"
            
            # 如果還是太長，截斷
            if len(summary) > max_words:
                summary = summary[:max_words] + "..."
            
            return summary
            
        except Exception as e:
            logger.error(f"備援摘要生成失敗: {e}")
            return ""
    
    def _build_summary_prompt(self, text: str, max_words: int) -> str:
        """
        構建摘要提示詞
        
        Args:
            text: 輸入文本
            max_words: 最大字數
            
        Returns:
            str: 提示詞
        """
        return f"""
請將以下文本濃縮為不超過 {max_words} 字的繁體中文摘要：

要求：
1. 摘要必須使用繁體中文
2. 字數不超過 {max_words} 字
3. 保留關鍵資訊和主要觀點
4. 語句通順，邏輯清晰
5. 觀點中立，不添加個人評論

文本內容：
{text}

請直接輸出摘要，不要添加任何額外的標題或說明。
"""
    
    def _check_quality(self, summary: str, original_text: str) -> float:
        """
        檢查摘要品質
        
        Args:
            summary: 摘要文本
            original_text: 原始文本
            
        Returns:
            float: 品質分數 (0-1)
        """
        try:
            score = 0.0
            
            # 檢查字數是否符合要求
            if len(summary) <= 150:
                score += 0.3
            elif len(summary) <= 200:
                score += 0.2
            else:
                score += 0.1
            
            # 檢查是否包含繁體中文
            if re.search(r'[\u4e00-\u9fff]', summary):
                score += 0.2
            
            # 檢查語句完整性
            if summary.endswith(('。', '！', '？', '...')):
                score += 0.2
            
            # 檢查關鍵詞覆蓋度
            original_keywords = self._extract_keywords(original_text)
            summary_keywords = self._extract_keywords(summary)
            
            if original_keywords and summary_keywords:
                overlap = len(set(original_keywords) & set(summary_keywords))
                coverage = overlap / len(original_keywords)
                score += 0.3 * min(coverage, 1.0)
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"品質檢查失敗: {e}")
            return 0.5
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取關鍵詞
        
        Args:
            text: 輸入文本
            
        Returns:
            List[str]: 關鍵詞列表
        """
        try:
            # 簡單的關鍵詞提取（基於詞頻）
            words = re.findall(r'[\u4e00-\u9fff]+', text)
            
            # 過濾短詞
            keywords = [word for word in words if len(word) >= 2]
            
            # 取前 10 個最常見的詞
            from collections import Counter
            word_counts = Counter(keywords)
            return [word for word, count in word_counts.most_common(10)]
            
        except Exception as e:
            logger.error(f"關鍵詞提取失敗: {e}")
            return []


# 全域實例
summary_generator = SummaryGenerator()


def get_summary_generator() -> SummaryGenerator:
    """獲取摘要生成器實例"""
    return summary_generator


async def test_summary_generator():
    """測試摘要生成器"""
    generator = get_summary_generator()
    
    # 測試文本
    test_text = """
    在今天的商業環境中，企業面臨著前所未有的挑戰和機遇。數位轉型已經成為企業生存和發展的關鍵因素。
    隨著人工智慧、大數據和雲端計算技術的快速發展，傳統的商業模式正在被顛覆，新的商業機會不斷湧現。
    
    企業需要重新思考自己的價值主張，建立以客戶為中心的服務模式，並利用新技術提升營運效率。
    同時，企業也需要關注永續發展，在追求經濟效益的同時，承擔社會責任，保護環境。
    
    成功的企業往往具有以下特徵：清晰的戰略願景、強大的執行能力、創新的文化氛圍，以及對市場變化的敏銳洞察力。
    領導者需要具備前瞻性思維，能夠在複雜的環境中做出正確的決策，並帶領團隊實現目標。
    """
    
    print("測試摘要生成")
    print("=" * 50)
    print(f"原始文本長度: {len(test_text)} 字元")
    print(f"原始文本預覽: {test_text[:100]}...")
    print()
    
    result = await generator.generate_summary(test_text, max_words=150)
    
    print(f"摘要生成成功: {result.success}")
    print(f"處理時間: {result.processing_time:.3f} 秒")
    print(f"摘要字數: {result.word_count}")
    print(f"品質分數: {result.quality_score:.2f}")
    
    if result.success:
        print(f"摘要內容: {result.summary}")
    else:
        print(f"錯誤訊息: {result.error_message}")


if __name__ == "__main__":
    asyncio.run(test_summary_generator()) 