"""
文本切分處理器
負責將長文本切分成適當大小的 chunks
"""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """文本塊資料類別"""
    chunk_id: str
    chunk_index: int
    chunk_text: str
    chunk_length: int
    source_document_id: str


class TextChunker:
    """文本切分處理器"""
    
    def __init__(self, max_chunk_size: int = 1024, overlap_size: int = 100):
        """
        初始化文本切分器
        
        Args:
            max_chunk_size: 最大分塊大小
            overlap_size: 重疊大小
        """
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        
    def split_text_into_chunks(self, text: str, document_id: str) -> List[TextChunk]:
        """
        將文本分割成塊 (以空白或換行切分)
        
        Args:
            text: 要切分的文本
            document_id: 來源文檔 ID
            
        Returns:
            文本塊列表
        """
        if not text:
            return []
            
        # 先按換行符分割
        lines = text.split('\n')
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 如果當前行加上現有chunk超過最大長度，且當前chunk不為空，則保存當前chunk
            if len(current_chunk) + len(line) > self.max_chunk_size and current_chunk:
                # 建立 TextChunk 物件
                chunk = TextChunk(
                    chunk_id=f"{document_id}_{chunk_index}",
                    chunk_index=chunk_index,
                    chunk_text=current_chunk.strip(),
                    chunk_length=len(current_chunk.strip()),
                    source_document_id=document_id
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # 開始新的 chunk，保留部分重疊內容
                if self.overlap_size > 0 and len(current_chunk) > self.overlap_size:
                    current_chunk = current_chunk[-self.overlap_size:] + " " + line
                else:
                    current_chunk = line
            else:
                if current_chunk:
                    current_chunk += " " + line
                else:
                    current_chunk = line
                    
        # 處理最後一個chunk
        if current_chunk:
            chunk = TextChunk(
                chunk_id=f"{document_id}_{chunk_index}",
                chunk_index=chunk_index,
                chunk_text=current_chunk.strip(),
                chunk_length=len(current_chunk.strip()),
                source_document_id=document_id
            )
            chunks.append(chunk)
            
        logger.info(f"文本切斷成 {len(chunks)} 個 chunks")
        return chunks
    
    def split_text_by_sentences(self, text: str, document_id: str) -> List[TextChunk]:
        """
        按句子切分文本
        
        Args:
            text: 要切分的文本
            document_id: 來源文檔 ID
            
        Returns:
            文本塊列表
        """
        if not text:
            return []
            
        # 簡單的句子分割（按句號、問號、驚嘆號）
        import re
        sentences = re.split(r'[。！？.!?]', text)
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 如果當前句子加上現有chunk超過最大長度，且當前chunk不為空，則保存當前chunk
            if len(current_chunk) + len(sentence) > self.max_chunk_size and current_chunk:
                chunk = TextChunk(
                    chunk_id=f"{document_id}_{chunk_index}",
                    chunk_index=chunk_index,
                    chunk_text=current_chunk.strip(),
                    chunk_length=len(current_chunk.strip()),
                    source_document_id=document_id
                )
                chunks.append(chunk)
                chunk_index += 1
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                    
        # 處理最後一個chunk
        if current_chunk:
            chunk = TextChunk(
                chunk_id=f"{document_id}_{chunk_index}",
                chunk_index=chunk_index,
                chunk_text=current_chunk.strip(),
                chunk_length=len(current_chunk.strip()),
                source_document_id=document_id
            )
            chunks.append(chunk)
            
        logger.info(f"文本按句子切斷成 {len(chunks)} 個 chunks")
        return chunks
    
    def split_text_by_paragraphs(self, text: str, document_id: str) -> List[TextChunk]:
        """
        按段落切分文本
        
        Args:
            text: 要切分的文本
            document_id: 來源文檔 ID
            
        Returns:
            文本塊列表
        """
        if not text:
            return []
            
        # 按雙換行符分割段落
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # 如果當前段落加上現有chunk超過最大長度，且當前chunk不為空，則保存當前chunk
            if len(current_chunk) + len(paragraph) > self.max_chunk_size and current_chunk:
                chunk = TextChunk(
                    chunk_id=f"{document_id}_{chunk_index}",
                    chunk_index=chunk_index,
                    chunk_text=current_chunk.strip(),
                    chunk_length=len(current_chunk.strip()),
                    source_document_id=document_id
                )
                chunks.append(chunk)
                chunk_index += 1
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                    
        # 處理最後一個chunk
        if current_chunk:
            chunk = TextChunk(
                chunk_id=f"{document_id}_{chunk_index}",
                chunk_index=chunk_index,
                chunk_text=current_chunk.strip(),
                chunk_length=len(current_chunk.strip()),
                source_document_id=document_id
            )
            chunks.append(chunk)
            
        logger.info(f"文本按段落切斷成 {len(chunks)} 個 chunks")
        return chunks
    
    def get_chunk_statistics(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """
        獲取切分統計資訊
        
        Args:
            chunks: 文本塊列表
            
        Returns:
            統計資訊字典
        """
        if not chunks:
            return {
                'total_chunks': 0,
                'avg_chunk_length': 0,
                'min_chunk_length': 0,
                'max_chunk_length': 0,
                'total_text_length': 0
            }
            
        lengths = [chunk.chunk_length for chunk in chunks]
        total_length = sum(lengths)
        
        return {
            'total_chunks': len(chunks),
            'avg_chunk_length': total_length / len(chunks),
            'min_chunk_length': min(lengths),
            'max_chunk_length': max(lengths),
            'total_text_length': total_length
        } 