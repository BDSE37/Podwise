"""
STT 文本智能切分器
專門處理語音轉文字後的無標點符號長文本
保持語意完整性，適用於 Podcast 內容處理
"""

import re
import jieba
from typing import List, Dict, Any, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class STTTextSplitter:
    """
    STT 文本智能切分器
    
    主要功能：
    - 處理無標點符號的 STT 文本
    - 基於語意停頓詞進行智能切分
    - 保持語意完整性和上下文連貫性
    - 支援中文 Podcast 內容的特殊處理
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 200,
        max_chunk_size: int = 2000
    ):
        """
        初始化 STT 文本切分器
        
        Args:
            chunk_size: 目標分塊大小
            chunk_overlap: 分塊重疊大小
            min_chunk_size: 最小分塊大小
            max_chunk_size: 最大分塊大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
        # 中文語意停頓詞（按優先級排序）
        self.semantic_pause_words = [
            # 主要語意停頓詞
            "然後", "所以", "但是", "不過", "然而", "因此", "總之", "最後",
            "首先", "其次", "第三", "另外", "此外", "而且", "同時", "接著",
            "接下來", "現在", "今天", "剛才", "剛才說到", "說到這裡",
            
            # 時間標記詞
            "昨天", "明天", "上週", "下週", "這個月", "下個月",
            
            # 主題轉換詞
            "關於", "說到", "提到", "說到這個", "說到這裡",
            "我們來談談", "我們來看看", "我們來討論",
            
            # 總結詞
            "總結來說", "簡單來說", "總而言之", "歸納一下",
            
            # 語氣詞（較低優先級）
            "嗯", "啊", "哦", "對", "是的", "沒錯"
        ]
        
        # 初始化 jieba 分詞器
        jieba.initialize()
        
        # 初始化 LangChain 分割器作為備用
        self.fallback_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
            length_function=len
        )
    
    def split_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        智能切分 STT 文本
        
        Args:
            text: 要切分的文本
            metadata: 元數據
            
        Returns:
            List[Document]: 切分後的文檔列表
        """
        try:
            # 清理文本
            cleaned_text = self._clean_text(text)
            
            # 嘗試基於語意停頓詞切分
            chunks = self._semantic_split(cleaned_text)
            
            # 如果語意切分失敗或效果不佳，使用備用切分器
            if not chunks or len(chunks) == 1:
                logger.info("語意切分效果不佳，使用備用切分器")
                chunks = self._fallback_split(cleaned_text)
            
            # 轉換為 Document 物件
            documents = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    "chunk_id": i,
                    "chunk_size": len(chunk),
                    "splitter_type": "stt_semantic",
                    "original_length": len(text)
                })
                
                documents.append(Document(
                    page_content=chunk,
                    metadata=chunk_metadata
                ))
            
            logger.info(f"成功切分文本，共生成 {len(documents)} 個分塊")
            return documents
            
        except Exception as e:
            logger.error(f"文本切分失敗: {str(e)}")
            # 使用備用切分器
            return self._fallback_split(text, metadata)
    
    def _clean_text(self, text: str) -> str:
        """
        清理文本
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理後的文本
        """
        # 移除多餘的空白字符
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除特殊字符（保留中文、英文、數字、基本標點）
        text = re.sub(r'[^\u4e00-\u9fff\w\s，。！？；：""''（）【】\-]', '', text)
        
        return text
    
    def _semantic_split(self, text: str) -> List[str]:
        """
        基於語意停頓詞進行智能切分
        
        Args:
            text: 要切分的文本
            
        Returns:
            List[str]: 切分後的文本塊列表
        """
        chunks = []
        current_chunk = ""
        
        # 使用 jieba 進行分詞
        words = list(jieba.cut(text))
        
        for i, word in enumerate(words):
            current_chunk += word
            
            # 檢查是否達到目標大小
            if len(current_chunk) >= self.chunk_size:
                # 尋找最佳的語意停頓點
                split_point = self._find_semantic_split_point(
                    current_chunk, 
                    words[max(0, i-50):i+1]  # 查看最近的詞
                )
                
                if split_point > 0:
                    # 在語意停頓點切分
                    chunk = current_chunk[:split_point].strip()
                    if len(chunk) >= self.min_chunk_size:
                        chunks.append(chunk)
                        # 保留重疊部分
                        overlap_start = max(0, split_point - self.chunk_overlap)
                        current_chunk = current_chunk[overlap_start:]
                    else:
                        # 如果切分後太小，繼續累積
                        continue
                else:
                    # 如果找不到語意停頓點，強制切分
                    if len(current_chunk) >= self.max_chunk_size:
                        chunks.append(current_chunk.strip())
                        current_chunk = ""
        
        # 處理剩餘的文本
        if current_chunk.strip() and len(current_chunk.strip()) >= self.min_chunk_size:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _find_semantic_split_point(self, text: str, recent_words: List[str]) -> int:
        """
        尋找最佳的語意停頓點
        
        Args:
            text: 當前文本塊
            recent_words: 最近的詞列表
            
        Returns:
            int: 切分點位置，-1 表示未找到
        """
        # 從後往前尋找語意停頓詞
        for pause_word in self.semantic_pause_words:
            if pause_word in text:
                # 找到停頓詞的位置
                positions = [m.start() for m in re.finditer(re.escape(pause_word), text)]
                
                # 選擇最接近目標大小的位置
                target_position = len(text) - self.chunk_overlap
                best_position = -1
                min_distance = float('inf')
                
                for pos in positions:
                    distance = abs(pos - target_position)
                    if distance < min_distance and pos > len(text) * 0.3:  # 避免在開頭切分
                        min_distance = distance
                        best_position = pos
                
                if best_position > 0:
                    return best_position + len(pause_word)
        
        return -1
    
    def _fallback_split(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        備用切分方法
        
        Args:
            text: 要切分的文本
            metadata: 元數據
            
        Returns:
            List[Document]: 切分後的文檔列表
        """
        try:
            documents = self.fallback_splitter.split_text(text)
            
            # 更新元數據
            for i, doc in enumerate(documents):
                if metadata:
                    doc.metadata.update(metadata)
                doc.metadata.update({
                    "chunk_id": i,
                    "chunk_size": len(doc.page_content),
                    "splitter_type": "fallback",
                    "original_length": len(text)
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"備用切分失敗: {str(e)}")
            # 最後的備用方案：簡單按字符切分
            return self._simple_split(text, metadata)
    
    def _simple_split(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        簡單字符切分（最後備用方案）
        
        Args:
            text: 要切分的文本
            metadata: 元數據
            
        Returns:
            List[Document]: 切分後的文檔列表
        """
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk = text[i:i + self.chunk_size]
            if chunk.strip():
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    "chunk_id": len(chunks),
                    "chunk_size": len(chunk),
                    "splitter_type": "simple",
                    "original_length": len(text)
                })
                
                chunks.append(Document(
                    page_content=chunk.strip(),
                    metadata=chunk_metadata
                ))
        
        return chunks
    
    def evaluate_split_quality(self, chunks: List[Document]) -> Dict[str, Any]:
        """
        評估切分品質
        
        Args:
            chunks: 切分後的文檔列表
            
        Returns:
            Dict[str, Any]: 品質評估結果
        """
        if not chunks:
            return {"error": "沒有文檔可評估"}
        
        # 計算統計資訊
        chunk_sizes = [len(chunk.page_content) for chunk in chunks]
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        
        # 計算變異係數（衡量大小一致性）
        variance = sum((size - avg_size) ** 2 for size in chunk_sizes) / len(chunk_sizes)
        std_dev = variance ** 0.5
        cv = std_dev / avg_size if avg_size > 0 else 0
        
        # 檢查語意完整性
        semantic_score = self._calculate_semantic_score(chunks)
        
        return {
            "total_chunks": len(chunks),
            "average_chunk_size": avg_size,
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
            "size_variation_coefficient": cv,
            "semantic_score": semantic_score,
            "quality_rating": self._get_quality_rating(cv, semantic_score)
        }
    
    def _calculate_semantic_score(self, chunks: List[Document]) -> float:
        """
        計算語意完整性分數
        
        Args:
            chunks: 文檔列表
            
        Returns:
            float: 語意分數 (0-1)
        """
        score = 0.0
        total_chunks = len(chunks)
        
        for chunk in chunks:
            content = chunk.page_content
            
            # 檢查是否包含語意停頓詞
            pause_word_count = sum(1 for word in self.semantic_pause_words if word in content)
            
            # 檢查句子完整性（簡單啟發式）
            sentence_endings = len(re.findall(r'[。！？]', content))
            
            # 計算分數
            chunk_score = min(1.0, (pause_word_count * 0.3 + sentence_endings * 0.2) / 2)
            score += chunk_score
        
        return score / total_chunks if total_chunks > 0 else 0.0
    
    def _get_quality_rating(self, cv: float, semantic_score: float) -> str:
        """
        獲取品質評級
        
        Args:
            cv: 變異係數
            semantic_score: 語意分數
            
        Returns:
            str: 品質評級
        """
        if cv < 0.3 and semantic_score > 0.7:
            return "優秀"
        elif cv < 0.5 and semantic_score > 0.5:
            return "良好"
        elif cv < 0.7 and semantic_score > 0.3:
            return "一般"
        else:
            return "需要改進" 