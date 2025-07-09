#!/usr/bin/env python3
"""
BGE-M3 模型整合腳本
用於生成 podcast 內容的 embedding 向量
"""

import torch
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BGEM3Embedding:
    """BGE-M3 模型封裝類別"""
    
    def __init__(self, model_name: str = "BAAI/bge-m3", device: str = None):
        """
        初始化 BGE-M3 模型
        
        Args:
            model_name: 模型名稱
            device: 設備 (cpu/cuda)
        """
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        logger.info(f"載入 BGE-M3 模型: {model_name}")
        logger.info(f"使用設備: {self.device}")
        
        try:
            self.model = SentenceTransformer(model_name, device=self.device)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"模型載入成功，向量維度: {self.dimension}")
        except Exception as e:
            logger.error(f"模型載入失敗: {e}")
            raise
    
    def encode_texts(self, texts: List[str], normalize: bool = True) -> np.ndarray:
        """
        將文字編碼為向量
        
        Args:
            texts: 文字列表
            normalize: 是否正規化向量
            
        Returns:
            embedding 向量陣列
        """
        try:
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=normalize,
                convert_to_numpy=True
            )
            logger.info(f"成功編碼 {len(texts)} 個文字")
            return embeddings
        except Exception as e:
            logger.error(f"文字編碼失敗: {e}")
            raise
    
    def encode_single_text(self, text: str, normalize: bool = True) -> np.ndarray:
        """
        編碼單個文字
        
        Args:
            text: 輸入文字
            normalize: 是否正規化向量
            
        Returns:
            embedding 向量
        """
        return self.encode_texts([text], normalize)[0]
    
    def batch_encode(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        批次編碼文字
        
        Args:
            texts: 文字列表
            batch_size: 批次大小
            
        Returns:
            embedding 向量陣列
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = self.encode_texts(batch_texts)
            all_embeddings.append(batch_embeddings)
            
            logger.info(f"處理批次 {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
        
        return np.vstack(all_embeddings)

def create_podcast_embeddings(texts: List[str], model: BGEM3Embedding = None) -> Dict[str, Any]:
    """
    為 podcast 內容建立 embedding
    
    Args:
        texts: podcast 文字內容列表
        model: BGE-M3 模型實例
        
    Returns:
        包含 embedding 和元資料的字典
    """
    if model is None:
        model = BGEM3Embedding()
    
    try:
        # 批次編碼
        embeddings = model.batch_encode(texts)
        
        # 準備結果
        result = {
            "embeddings": embeddings.tolist(),
            "dimension": model.dimension,
            "model_name": model.model_name,
            "text_count": len(texts),
            "metadata": {
                "normalized": True,
                "device": model.device
            }
        }
        
        logger.info(f"成功建立 {len(texts)} 個 embedding")
        return result
        
    except Exception as e:
        logger.error(f"建立 podcast embedding 失敗: {e}")
        raise

def test_embedding():
    """測試 embedding 功能"""
    logger.info("開始測試 BGE-M3 embedding...")
    
    # 測試文字
    test_texts = [
        "人工智慧正在改變我們的工作方式",
        "機器學習是 AI 的重要分支",
        "深度學習在圖像識別方面表現優異",
        "自然語言處理讓機器能理解人類語言",
        "強化學習在遊戲和機器人領域有重要應用"
    ]
    
    try:
        # 建立模型
        model = BGEM3Embedding()
        
        # 編碼文字
        embeddings = model.encode_texts(test_texts)
        
        # 檢查結果
        logger.info(f"向量形狀: {embeddings.shape}")
        logger.info(f"向量維度: {embeddings.shape[1]}")
        
        # 計算相似度
        from sklearn.metrics.pairwise import cosine_similarity
        similarity_matrix = cosine_similarity(embeddings)
        
        logger.info("相似度矩陣:")
        for i, text in enumerate(test_texts):
            logger.info(f"  {text[:20]}...")
            for j, sim in enumerate(similarity_matrix[i]):
                logger.info(f"    -> {test_texts[j][:20]}...: {sim:.3f}")
        
        logger.info("✅ BGE-M3 embedding 測試成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ BGE-M3 embedding 測試失敗: {e}")
        return False

if __name__ == "__main__":
    # 執行測試
    test_embedding() 