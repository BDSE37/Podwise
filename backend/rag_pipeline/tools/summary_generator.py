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
            logger.info(f"SummaryGenerator 初始化完成，模型: {self.model}")
        else:
            logger.warning("OpenAI API 金鑰未設置，將使用備援摘要方法")
        
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
            
            # 使用新版本的 OpenAI API
            client = openai.AsyncOpenAI(api_key=self.api_key)
            
            response = await client.chat.completions.create(
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
        備援摘要生成方法 - 智能跳過工商廣告，提取節目內容，確保語意通順
        
        Args:
            text: 輸入文本
            max_words: 最大字數
            
        Returns:
            str: 生成的摘要
        """
        try:
            # 跳過工商廣告內容
            cleaned_text = self._remove_advertisement_content(text)
            
            # 智能句子提取
            meaningful_sentences = self._extract_meaningful_sentences(cleaned_text)
            
            # 選擇語意通順的句子組合
            summary = self._create_coherent_summary(meaningful_sentences, max_words)
            
            # 如果沒有找到合適的句子，嘗試從中間部分提取
            if not summary or len(summary) < 50:
                middle_text = self._extract_middle_content(text)
                middle_sentences = self._extract_meaningful_sentences(middle_text)
                summary = self._create_coherent_summary(middle_sentences, max_words)
            
            # 最後備援
            if not summary or len(summary) < 30:
                summary = self._extract_fallback_summary(text, max_words)
            
            # 最終標點符號處理
            summary = self._finalize_punctuation(summary)
            
            # 確保摘要不超過字數限制
            if len(summary) > max_words:
                summary = summary[:max_words] + "..."
            
            return summary
            
        except Exception as e:
            logger.error(f"備援摘要生成失敗: {e}")
            # 最後的備援：直接取前150個字元
            return text[:max_words] + "..."
    
    def _remove_advertisement_content(self, text: str) -> str:
        """
        移除工商廣告內容
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理後的文本
        """
        # 工商廣告關鍵詞
        ad_keywords = [
            "贊助", "廣告", "合作", "乳液糖", "太陽餅", "禮盒", "廠商", "供不應求",
            "包裝", "送給", "親朋好友", "企業送禮", "明星商品", "冠軍", "傳統與創新",
            "嚴選", "高品質食材", "現金榴彈黃酥", "餅魂", "精神與傳承"
        ]
        
        # 分割句子
        sentences = re.split(r'[。！？]', text)
        cleaned_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 檢查是否包含廣告關鍵詞
            is_ad = any(keyword in sentence for keyword in ad_keywords)
            
            # 檢查是否為開頭的歡迎詞（通常包含工商）
            is_welcome_ad = (
                "歡迎收聽" in sentence and 
                any(word in sentence for word in ["贊助", "合作", "廣告"])
            )
            
            # 跳過廣告內容
            if not is_ad and not is_welcome_ad:
                cleaned_sentences.append(sentence)
        
        return "。".join(cleaned_sentences) + "。"
    
    def _extract_meaningful_sentences(self, text: str) -> List[str]:
        """
        從文本中提取有意義的句子，跳過工商廣告內容，優先選擇口語化表達
        
        Args:
            text: 輸入文本
            
        Returns:
            List[str]: 有意義的句子列表
        """
        try:
            # 分割句子
            sentences = re.split(r'[。！？]', text)
            meaningful_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence or len(sentence) < 10:
                    continue
                
                # 跳過工商廣告內容
                if self._is_advertisement_content(sentence):
                    continue
                
                # 計算句子相關性分數（優先口語化表達）
                score = self._calculate_sentence_relevance(sentence)
                
                # 只保留相關性較高的句子
                if score > 0.3:
                    meaningful_sentences.append((sentence, score))
            
            # 按相關性分數排序
            meaningful_sentences.sort(key=lambda x: x[1], reverse=True)
            
            # 返回前10個最相關的句子
            return [sentence for sentence, score in meaningful_sentences[:10]]
            
        except Exception as e:
            logger.error(f"關鍵詞提取失敗: {e}")
            return []
    
    def _is_advertisement_content(self, sentence: str) -> bool:
        """
        檢查句子是否為工商廣告內容
        
        Args:
            sentence: 句子
            
        Returns:
            bool: 是否為廣告內容
        """
        # 工商廣告關鍵詞
        ad_keywords = [
            '贊助', '廣告', '合作', '歡迎收聽', '本集節目由', '感謝', '提供',
            '優惠', '折扣', '限時', '特價', '購買', '訂購', '客服', '電話',
            '網站', 'APP', '下載', '註冊', '登入', '會員', 'VIP', '專屬'
        ]
        
        # 檢查是否包含廣告關鍵詞
        for keyword in ad_keywords:
            if keyword in sentence:
                return True
        
        # 檢查是否為歡迎詞
        welcome_patterns = [
            r'歡迎收聽.*',
            r'大家好.*',
            r'我是.*',
            r'本集.*'
        ]
        
        for pattern in welcome_patterns:
            if re.match(pattern, sentence):
                return True
        
        return False
    
    def _calculate_sentence_relevance(self, sentence: str) -> float:
        """
        計算句子的相關性分數，優先口語化表達
        
        Args:
            sentence: 句子
            
        Returns:
            float: 相關性分數 (0-1)
        """
        # 口語化表達關鍵詞（加分項）
        colloquial_keywords = [
            '我覺得', '我認為', '我覺得', '我觀察到', '我發現', '我注意到',
            '其實', '說真的', '坦白說', '老實說', '說實話', '說穿了',
            '基本上', '原則上', '理論上', '實際上', '事實上', '說白了',
            '這個', '那個', '這些', '那些', '這樣', '那樣', '這麼', '那麼',
            '蠻', '挺', '還蠻', '還挺', '蠻好的', '挺不錯的', '蠻有意思的'
        ]
        
        # 內容相關關鍵詞
        content_keywords = [
            '分析', '討論', '觀點', '提到', '說到', '觀察', '發現', '研究',
            '數據', '趨勢', '市場', '股票', '投資', '經濟', '政策', '影響',
            '原因', '結果', '比較', '對比', '預測', '展望', '分享', '經驗'
        ]
        
        # 計算口語化分數
        colloquial_score = 0
        for keyword in colloquial_keywords:
            if keyword in sentence:
                colloquial_score += 0.1
        
        # 計算內容相關分數
        content_score = 0
        for keyword in content_keywords:
            if keyword in sentence:
                content_score += 0.05
        
        # 句子長度分數
        length_score = min(len(sentence) / 100, 1.0)
        
        # 綜合分數（口語化表達優先）
        total_score = (colloquial_score * 0.6 + content_score * 0.3 + length_score * 0.1)
        
        return min(total_score, 1.0)
    
    def _create_coherent_summary(self, sentences: List[str], max_words: int) -> str:
        """
        創建語意通順的口語化摘要
        
        Args:
            sentences: 有意義的句子列表
            max_words: 最大字數
            
        Returns:
            str: 語意通順的摘要
        """
        if not sentences:
            return ""
        
        # 選擇前2-3個最相關的句子
        selected_sentences = sentences[:3]
        
        # 檢查句子之間的語意連接
        coherent_summary = []
        current_length = 0
        
        for i, sentence in enumerate(selected_sentences):
            # 檢查是否會超過字數限制
            if current_length + len(sentence) > max_words:
                break
            
            # 檢查語意通順性
            if self._is_coherent_sentence(sentence, coherent_summary):
                # 處理標點符號，保持口語化
                processed_sentence = self._process_punctuation_colloquial(sentence)
                coherent_summary.append(processed_sentence)
                current_length += len(processed_sentence)
            else:
                # 嘗試簡化句子
                simplified = self._simplify_sentence_colloquial(sentence)
                if simplified and current_length + len(simplified) <= max_words:
                    processed_simplified = self._process_punctuation_colloquial(simplified)
                    coherent_summary.append(processed_simplified)
                    current_length += len(processed_simplified)
        
        if coherent_summary:
            # 智能連接句子，保持口語化
            summary = self._connect_sentences_colloquially(coherent_summary)
            return summary
        else:
            return ""
    
    def _is_coherent_sentence(self, sentence: str, previous_sentences: List[str]) -> bool:
        """
        檢查句子是否語意通順
        
        Args:
            sentence: 當前句子
            previous_sentences: 前面的句子
            
        Returns:
            bool: 是否語意通順
        """
        # 檢查句子是否完整
        if len(sentence) < 10:
            return False
        
        # 檢查是否包含完整的語意結構
        has_subject = any(word in sentence for word in ["我", "他", "她", "它", "我們", "他們", "這個", "那個", "這些", "那些"])
        has_verb = any(word in sentence for word in ["是", "有", "說", "認為", "覺得", "分析", "討論", "提到", "分享", "觀察"])
        
        # 檢查是否避免重複內容
        if previous_sentences:
            for prev_sentence in previous_sentences[-2:]:  # 檢查前兩句
                if self._calculate_similarity(sentence, prev_sentence) > 0.7:
                    return False
        
        return has_subject or has_verb
    
    def _simplify_sentence(self, sentence: str) -> str:
        """
        簡化句子，提高可讀性
        
        Args:
            sentence: 原始句子
            
        Returns:
            str: 簡化後的句子
        """
        # 移除過長的修飾語
        if len(sentence) > 50:
            # 保留主要內容，移除過長的描述
            parts = sentence.split("，")
            if len(parts) > 2:
                return "，".join(parts[:2]) + "。"
        
        return sentence
    
    def _calculate_similarity(self, sentence1: str, sentence2: str) -> float:
        """
        計算兩個句子的相似度
        
        Args:
            sentence1: 句子1
            sentence2: 句子2
            
        Returns:
            float: 相似度 (0-1)
        """
        # 簡單的詞彙重疊計算
        words1 = set(re.findall(r'[\u4e00-\u9fff]+', sentence1))
        words2 = set(re.findall(r'[\u4e00-\u9fff]+', sentence2))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _extract_middle_content(self, text: str) -> str:
        """
        提取文本中間部分（跳過開頭廣告）
        
        Args:
            text: 原始文本
            
        Returns:
            str: 中間部分的文本
        """
        # 從1/3處開始，取中間部分
        start = len(text) // 3
        end = start + len(text) // 2
        
        return text[start:end]
    
    def _extract_fallback_summary(self, text: str, max_words: int) -> str:
        """
        最後的備援摘要提取
        
        Args:
            text: 原始文本
            max_words: 最大字數
            
        Returns:
            str: 備援摘要
        """
        # 尋找包含關鍵詞的句子
        key_sentences = []
        sentences = re.split(r'[。！？]', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 15 or len(sentence) > 100:
                continue
            
            # 檢查是否包含重要內容
            if any(word in sentence for word in ["分析", "討論", "觀點", "認為", "覺得", "提到", "說到"]):
                key_sentences.append(sentence)
        
        if key_sentences:
            # 選擇最長的句子
            best_sentence = max(key_sentences, key=len)
            if len(best_sentence) <= max_words:
                return best_sentence + "。"
            else:
                return best_sentence[:max_words] + "..."
        
        # 如果沒有找到關鍵句子，取中間部分
        middle_start = len(text) // 4
        middle_text = text[middle_start:middle_start + max_words]
        
        # 找到句子的結束位置
        for i in range(len(middle_text) - 1, 0, -1):
            if middle_text[i] in "。！？":
                return middle_text[:i+1]
        
        return middle_text + "..."
    
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
    
    def _process_punctuation(self, sentence: str) -> str:
        """
        處理句子的標點符號，讓語意更清晰
        
        Args:
            sentence: 原始句子
            
        Returns:
            str: 處理後的句子
        """
        if not sentence:
            return sentence
        
        # 移除多餘的標點符號
        sentence = re.sub(r'[。！？，、；：""''（）【】]+', '', sentence)
        
        # 在適當位置加入逗號
        sentence = self._add_commas_intelligently(sentence)
        
        # 確保句子以句號結尾
        if not sentence.endswith('。'):
            sentence += '。'
        
        return sentence
    
    def _add_commas_intelligently(self, sentence: str) -> str:
        """
        智能加入逗號，讓語意更清晰
        
        Args:
            sentence: 原始句子
            
        Returns:
            str: 加入逗號後的句子
        """
        if len(sentence) < 20:
            return sentence
        
        # 在轉折詞前後加入逗號
        transition_words = [
            '但是', '然而', '不過', '可是', '只是', '雖然', '儘管',
            '因為', '所以', '因此', '於是', '然後', '接著', '最後', '總之',
            '例如', '比如', '像是', '就是', '其實', '事實上', '當然'
        ]
        
        for word in transition_words:
            if word in sentence:
                # 在轉折詞前加入逗號
                sentence = sentence.replace(word, f'，{word}')
                # 在轉折詞後加入逗號（如果不是句尾）
                if not sentence.endswith(word + '，'):
                    sentence = sentence.replace(word + '，', word + '，', 1)
        
        # 在長句子的適當位置加入逗號
        if len(sentence) > 30:
            # 在動詞後加入逗號
            verbs = ['說', '認為', '覺得', '分析', '討論', '提到', '分享', '觀察']
            for verb in verbs:
                if verb in sentence:
                    parts = sentence.split(verb)
                    if len(parts) > 1 and len(parts[1]) > 10:
                        sentence = parts[0] + verb + '，' + parts[1]
                        break
        
        # 避免過多的逗號
        sentence = re.sub(r'，+', '，', sentence)
        
        return sentence
    
    def _connect_sentences_intelligently(self, sentences: List[str]) -> str:
        """
        智能連接句子，讓摘要更流暢
        
        Args:
            sentences: 句子列表
            
        Returns:
            str: 連接後的摘要
        """
        if not sentences:
            return ""
        
        if len(sentences) == 1:
            return sentences[0]
        
        # 檢查句子之間的語意關係
        connected_summary = []
        
        for i, sentence in enumerate(sentences):
            current_sentence = sentence
            
            # 如果不是第一句，檢查是否需要連接詞
            if i > 0:
                prev_sentence = sentences[i-1]
                
                # 檢查是否需要加入連接詞
                if self._needs_connector(prev_sentence, current_sentence):
                    connector = self._get_appropriate_connector(prev_sentence, current_sentence)
                    current_sentence = connector + current_sentence
            
            connected_summary.append(current_sentence)
        
        return "".join(connected_summary)
    
    def _needs_connector(self, prev_sentence: str, current_sentence: str) -> bool:
        """
        檢查是否需要連接詞
        
        Args:
            prev_sentence: 前一句
            current_sentence: 當前句
            
        Returns:
            bool: 是否需要連接詞
        """
        # 如果前一句以句號結尾，通常需要連接詞
        if prev_sentence.endswith('。'):
            return True
        
        # 檢查語意關係
        prev_keywords = ['但是', '然而', '不過', '可是', '只是']
        current_keywords = ['但是', '然而', '不過', '可是', '只是', '因為', '所以', '因此']
        
        # 如果當前句有轉折詞，通常不需要額外連接詞
        if any(word in current_sentence for word in current_keywords):
            return False
        
        return True
    
    def _get_appropriate_connector(self, prev_sentence: str, current_sentence: str) -> str:
        """
        獲取適當的連接詞
        
        Args:
            prev_sentence: 前一句
            current_sentence: 當前句
            
        Returns:
            str: 適當的連接詞
        """
        # 檢查語意關係，選擇適當的連接詞
        if any(word in current_sentence for word in ['但是', '然而', '不過', '可是', '只是']):
            return ""  # 已有轉折詞
        
        if any(word in current_sentence for word in ['因為', '所以', '因此']):
            return ""  # 已有因果詞
        
        # 根據內容選擇連接詞
        if any(word in current_sentence for word in ['分析', '討論', '提到', '說到']):
            return "另外，"
        
        if any(word in current_sentence for word in ['認為', '覺得', '觀察']):
            return "同時，"
        
        # 預設連接詞
        return "此外，"

    def _finalize_punctuation(self, summary: str) -> str:
        """
        最終標點符號處理，確保摘要語意清晰
        
        Args:
            summary: 原始摘要
            
        Returns:
            str: 處理後的摘要
        """
        if not summary:
            return summary
        
        # 分段處理標點符號
        summary = self._process_punctuation_by_segments(summary)
        
        # 智能標點符號插入
        summary = self._insert_punctuation_intelligently(summary)
        
        # 清理和優化
        summary = self._cleanup_punctuation(summary)
        
        return summary
    
    def _process_punctuation_by_segments(self, text: str) -> str:
        """
        分段處理標點符號，參考 PunctuationModel 的方法
        
        Args:
            text: 原始文本
            
        Returns:
            str: 處理後的文本
        """
        if not text:
            return text
        
        # 移除現有的標點符號
        text = re.sub(r'[。！？，、；：""''（）【】]+', '', text)
        
        # 分段處理：按語意單位分割
        segments = self._split_by_semantic_units(text)
        
        processed_segments = []
        for segment in segments:
            if len(segment) < 5:
                processed_segments.append(segment)
                continue
            
            # 處理每個語意段
            processed_segment = self._process_single_segment(segment)
            processed_segments.append(processed_segment)
        
        return "".join(processed_segments)
    
    def _split_by_semantic_units(self, text: str) -> List[str]:
        """
        按語意單位分割文本
        
        Args:
            text: 原始文本
            
        Returns:
            List[str]: 語意段列表
        """
        # 語意分割關鍵詞
        split_keywords = [
            '但是', '然而', '不過', '可是', '只是', '雖然', '儘管',
            '因為', '所以', '因此', '於是', '然後', '接著', '最後', '總之',
            '例如', '比如', '像是', '就是', '其實', '事實上', '當然',
            '另外', '同時', '此外', '而且', '並且', '或者', '還是'
        ]
        
        segments = [text]
        
        for keyword in split_keywords:
            new_segments = []
            for segment in segments:
                if keyword in segment:
                    parts = segment.split(keyword)
                    for i, part in enumerate(parts):
                        if i == 0:
                            new_segments.append(part)
                        else:
                            new_segments.append(keyword + part)
                else:
                    new_segments.append(segment)
            segments = new_segments
        
        # 過濾空段
        return [seg for seg in segments if seg.strip()]
    
    def _process_single_segment(self, segment: str) -> str:
        """
        處理單個語意段
        
        Args:
            segment: 語意段
            
        Returns:
            str: 處理後的語意段
        """
        if len(segment) < 10:
            return segment
        
        # 在動詞後加入逗號
        verbs = ['說', '認為', '覺得', '分析', '討論', '提到', '分享', '觀察', '發現', '看到', '聽到']
        for verb in verbs:
            if verb in segment:
                parts = segment.split(verb)
                if len(parts) > 1 and len(parts[1]) > 8:
                    segment = parts[0] + verb + '，' + parts[1]
                    break
        
        # 在形容詞後加入逗號
        adjectives = ['非常', '特別', '真的', '確實', '明顯', '清楚', '重要', '關鍵']
        for adj in adjectives:
            if adj in segment:
                parts = segment.split(adj)
                if len(parts) > 1 and len(parts[1]) > 5:
                    segment = parts[0] + adj + '，' + parts[1]
                    break
        
        return segment
    
    def _insert_punctuation_intelligently(self, text: str) -> str:
        """
        智能插入標點符號，參考 PunctuationModel 的方法
        
        Args:
            text: 原始文本
            
        Returns:
            str: 處理後的文本
        """
        if not text:
            return text
        
        # 在轉折詞前加入逗號
        transition_words = [
            '但是', '然而', '不過', '可是', '只是', '雖然', '儘管',
            '因為', '所以', '因此', '於是', '然後', '接著', '最後', '總之'
        ]
        
        for word in transition_words:
            if word in text:
                text = text.replace(word, f'，{word}')
        
        # 在連接詞前加入逗號
        connector_words = [
            '另外', '同時', '此外', '而且', '並且', '或者', '還是'
        ]
        
        for word in connector_words:
            if word in text:
                text = text.replace(word, f'，{word}')
        
        # 在時間詞前加入逗號
        time_words = [
            '最近', '現在', '目前', '之前', '之後', '當時', '那時'
        ]
        
        for word in time_words:
            if word in text:
                text = text.replace(word, f'，{word}')
        
        return text
    
    def _cleanup_punctuation(self, text: str) -> str:
        """
        清理和優化標點符號
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理後的文本
        """
        if not text:
            return text
        
        # 避免過多的逗號
        text = re.sub(r'，+', '，', text)
        
        # 避免句首逗號
        text = re.sub(r'^，', '', text)
        
        # 確保句子以句號結尾
        if not text.endswith('。'):
            text += '。'
        
        # 清理多餘的句號
        text = re.sub(r'。+', '。', text)
        
        return text

    def _process_punctuation_colloquial(self, sentence: str) -> str:
        """
        處理句子的標點符號，保持口語化風格
        
        Args:
            sentence: 原始句子
            
        Returns:
            str: 處理後的句子
        """
        if not sentence:
            return sentence
        
        # 移除多餘的標點符號
        sentence = re.sub(r'[。！？，、；：""''（）【】]+', '', sentence)
        
        # 在口語化表達後加入逗號
        sentence = self._add_commas_colloquial(sentence)
        
        # 確保句子以句號結尾
        if not sentence.endswith('。'):
            sentence += '。'
        
        return sentence
    
    def _add_commas_colloquial(self, sentence: str) -> str:
        """
        在口語化表達中智能加入逗號
        
        Args:
            sentence: 原始句子
            
        Returns:
            str: 加入逗號後的句子
        """
        if len(sentence) < 15:
            return sentence
        
        # 口語化表達詞彙
        colloquial_words = [
            '我覺得', '我認為', '我觀察到', '我發現', '我注意到',
            '其實', '說真的', '坦白說', '老實說', '說實話', '說穿了',
            '基本上', '原則上', '理論上', '實際上', '事實上', '說白了',
            '這個', '那個', '這些', '那些', '這樣', '那樣', '這麼', '那麼',
            '蠻', '挺', '還蠻', '還挺', '蠻好的', '挺不錯的', '蠻有意思的'
        ]
        
        # 在口語化詞彙後加入逗號
        for word in colloquial_words:
            if word in sentence:
                parts = sentence.split(word)
                if len(parts) > 1 and len(parts[1]) > 5:
                    sentence = parts[0] + word + '，' + parts[1]
                    break
        
        # 在轉折詞前後加入逗號
        transition_words = [
            '但是', '然而', '不過', '可是', '只是', '雖然', '儘管',
            '因為', '所以', '因此', '於是', '然後', '接著', '最後', '總之'
        ]
        
        for word in transition_words:
            if word in sentence:
                sentence = sentence.replace(word, f'，{word}')
        
        # 避免過多的逗號
        sentence = re.sub(r'，+', '，', sentence)
        
        return sentence
    
    def _simplify_sentence_colloquial(self, sentence: str) -> str:
        """
        簡化句子，保持口語化風格
        
        Args:
            sentence: 原始句子
            
        Returns:
            str: 簡化後的句子
        """
        # 移除過長的修飾語，保持口語化
        if len(sentence) > 60:
            # 保留主要內容，移除過長的描述
            parts = sentence.split("，")
            if len(parts) > 2:
                return "，".join(parts[:2]) + "。"
        
        return sentence
    
    def _connect_sentences_colloquially(self, sentences: List[str]) -> str:
        """
        口語化連接句子，讓摘要更自然
        
        Args:
            sentences: 句子列表
            
        Returns:
            str: 連接後的摘要
        """
        if not sentences:
            return ""
        
        if len(sentences) == 1:
            return sentences[0]
        
        # 檢查句子之間的語意關係
        connected_summary = []
        
        for i, sentence in enumerate(sentences):
            current_sentence = sentence
            
            # 如果不是第一句，檢查是否需要連接詞
            if i > 0:
                prev_sentence = sentences[i-1]
                
                # 檢查是否需要加入口語化連接詞
                if self._needs_colloquial_connector(prev_sentence, current_sentence):
                    connector = self._get_colloquial_connector(prev_sentence, current_sentence)
                    current_sentence = connector + current_sentence
            
            connected_summary.append(current_sentence)
        
        return "".join(connected_summary)
    
    def _needs_colloquial_connector(self, prev_sentence: str, current_sentence: str) -> bool:
        """
        檢查是否需要口語化連接詞
        
        Args:
            prev_sentence: 前一句
            current_sentence: 當前句
            
        Returns:
            bool: 是否需要連接詞
        """
        # 如果前一句以句號結尾，通常需要連接詞
        if prev_sentence.endswith('。'):
            return True
        
        # 檢查語意關係
        current_keywords = ['但是', '然而', '不過', '可是', '只是', '因為', '所以', '因此']
        
        # 如果當前句有轉折詞，通常不需要額外連接詞
        if any(word in current_sentence for word in current_keywords):
            return False
        
        return True
    
    def _get_colloquial_connector(self, prev_sentence: str, current_sentence: str) -> str:
        """
        獲取口語化的連接詞
        
        Args:
            prev_sentence: 前一句
            current_sentence: 當前句
            
        Returns:
            str: 口語化連接詞
        """
        # 檢查語意關係，選擇適當的口語化連接詞
        if any(word in current_sentence for word in ['但是', '然而', '不過', '可是', '只是']):
            return ""  # 已有轉折詞
        
        if any(word in current_sentence for word in ['因為', '所以', '因此']):
            return ""  # 已有因果詞
        
        # 根據內容選擇口語化連接詞
        if any(word in current_sentence for word in ['分析', '討論', '提到', '說到']):
            return "另外，"
        
        if any(word in current_sentence for word in ['認為', '覺得', '觀察']):
            return "同時，"
        
        # 口語化預設連接詞
        return "還有，"


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