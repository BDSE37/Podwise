#!/usr/bin/env python3
"""
Word2Vec 模型訓練工具

此腳本用於訓練 Word2Vec 模型，基於 Podcast 內容進行語義學習，
為智能 TAG 提取提供語義相似度計算能力。

主要功能：
- 載入 Podcast 文本數據
- 文本預處理
- Word2Vec 模型訓練
- 模型評估與保存

作者: Podwise Team
版本: 1.0.0
"""

import logging
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime

# 機器學習相關導入
try:
    import jieba
    from gensim.models import Word2Vec
    from gensim.models.word2vec import LineSentence
    from sklearn.metrics.pairwise import cosine_similarity
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.error("機器學習套件未安裝，無法訓練 Word2Vec 模型")

logger = logging.getLogger(__name__)


class Word2VecTrainer:
    """Word2Vec 模型訓練器"""
    
    def __init__(self, 
                 data_dir: str = "../../../data/raw",
                 model_save_path: str = "models/word2vec_podcast.model",
                 min_count: int = 2,
                 vector_size: int = 100,
                 window: int = 5,
                 workers: int = 4):
        """
        初始化訓練器
        
        Args:
            data_dir: 數據目錄路徑
            model_save_path: 模型保存路徑
            min_count: 最小詞頻
            vector_size: 向量維度
            window: 窗口大小
            workers: 工作進程數
        """
        self.data_dir = Path(data_dir)
        self.model_save_path = Path(model_save_path)
        self.min_count = min_count
        self.vector_size = vector_size
        self.window = window
        self.workers = workers
        
        # 確保模型保存目錄存在
        self.model_save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化 jieba
        if ML_AVAILABLE:
            jieba.initialize()
    
    def load_podcast_data(self) -> List[str]:
        """
        載入 Podcast 數據
        
        Returns:
            List[str]: 文本列表
        """
        texts = []
        
        # 支援的檔案格式
        supported_formats = ['.json', '.txt', '.csv']
        
        for file_path in self.data_dir.rglob('*'):
            if file_path.suffix.lower() in supported_formats:
                try:
                    if file_path.suffix.lower() == '.json':
                        texts.extend(self._load_json_data(file_path))
                    elif file_path.suffix.lower() == '.txt':
                        texts.extend(self._load_txt_data(file_path))
                    elif file_path.suffix.lower() == '.csv':
                        texts.extend(self._load_csv_data(file_path))
                    
                    logger.info(f"載入檔案: {file_path}")
                    
                except Exception as e:
                    logger.error(f"載入檔案失敗 {file_path}: {str(e)}")
        
        logger.info(f"總共載入 {len(texts)} 個文本")
        return texts
    
    def _load_json_data(self, file_path: Path) -> List[str]:
        """載入 JSON 數據"""
        texts = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        # 提取可能的文本欄位
                        text_fields = ['content', 'text', 'description', 'title', 'summary', 'transcript']
                        for field in text_fields:
                            if field in item and item[field]:
                                texts.append(str(item[field]))
            elif isinstance(data, dict):
                # 如果是字典，遞歸處理
                texts.extend(self._extract_text_from_dict(data))
        
        return texts
    
    def _load_txt_data(self, file_path: Path) -> List[str]:
        """載入 TXT 數據"""
        texts = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    texts.append(line)
        
        return texts
    
    def _load_csv_data(self, file_path: Path) -> List[str]:
        """載入 CSV 數據"""
        texts = []
        
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            
            # 提取可能的文本欄位
            text_columns = [col for col in df.columns if any(keyword in col.lower() 
                           for keyword in ['content', 'text', 'description', 'title', 'summary'])]
            
            for col in text_columns:
                texts.extend(df[col].dropna().astype(str).tolist())
                
        except ImportError:
            logger.warning("pandas 未安裝，跳過 CSV 檔案")
        except Exception as e:
            logger.error(f"載入 CSV 檔案失敗: {str(e)}")
        
        return texts
    
    def _extract_text_from_dict(self, data: Dict[str, Any]) -> List[str]:
        """從字典中提取文本"""
        texts = []
        
        for key, value in data.items():
            if isinstance(value, str) and value.strip():
                texts.append(value)
            elif isinstance(value, dict):
                texts.extend(self._extract_text_from_dict(value))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item.strip():
                        texts.append(item)
                    elif isinstance(item, dict):
                        texts.extend(self._extract_text_from_dict(item))
        
        return texts
    
    def preprocess_texts(self, texts: List[str]) -> List[List[str]]:
        """
        預處理文本
        
        Args:
            texts: 原始文本列表
            
        Returns:
            List[List[str]]: 分詞後的文本列表
        """
        if not ML_AVAILABLE:
            logger.error("jieba 未安裝，無法進行分詞")
            return []
        
        processed_texts = []
        
        for text in texts:
            if not text or not text.strip():
                continue
            
            # 分詞
            words = jieba.lcut(text)
            
            # 過濾停用詞和短詞
            filtered_words = []
            for word in words:
                word = word.strip()
                if len(word) >= 2 and not self._is_stopword(word):
                    filtered_words.append(word)
            
            if filtered_words:
                processed_texts.append(filtered_words)
        
        logger.info(f"預處理完成，共 {len(processed_texts)} 個文本")
        return processed_texts
    
    def _is_stopword(self, word: str) -> bool:
        """檢查是否為停用詞"""
        stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一個', '上', '也', '很', '到', '說', '要', '去', '你', '會', '著', '沒有', '看', '好', '自己', '這', '那', '他', '她', '它', '我們', '你們', '他們', '她們', '它們',
            '這個', '那個', '這些', '那些', '什麼', '怎麼', '為什麼', '哪裡', '什麼時候', '怎麼樣',
            '可以', '應該', '必須', '需要', '想要', '希望', '覺得', '認為', '知道', '了解', '學習',
            '工作', '生活', '時間', '問題', '事情', '東西', '地方', '時候', '方式', '方法', '結果',
            '因為', '所以', '但是', '而且', '或者', '如果', '雖然', '儘管', '除了', '關於', '對於',
            '通過', '根據', '由於', '為了', '由於', '關於', '對於', '在', '從', '到', '向', '對', '給',
            '被', '讓', '使', '得', '地', '得', '的', '地', '得', '著', '了', '過', '來', '去', '上', '下',
            '進', '出', '回', '來', '去', '到', '在', '從', '向', '對', '給', '被', '讓', '使', '得'
        }
        return word in stopwords
    
    def train_word2vec_model(self, processed_texts: List[List[str]]) -> Optional[Word2Vec]:
        """
        訓練 Word2Vec 模型
        
        Args:
            processed_texts: 預處理後的文本列表
            
        Returns:
            Optional[Word2Vec]: 訓練好的模型
        """
        if not ML_AVAILABLE:
            logger.error("gensim 未安裝，無法訓練 Word2Vec 模型")
            return None
        
        if not processed_texts:
            logger.error("沒有文本數據可用於訓練")
            return None
        
        logger.info("開始訓練 Word2Vec 模型...")
        logger.info(f"文本數量: {len(processed_texts)}")
        logger.info(f"最小詞頻: {self.min_count}")
        logger.info(f"向量維度: {self.vector_size}")
        logger.info(f"窗口大小: {self.window}")
        logger.info(f"工作進程: {self.workers}")
        
        try:
            # 訓練模型
            model = Word2Vec(
                sentences=processed_texts,
                vector_size=self.vector_size,
                window=self.window,
                min_count=self.min_count,
                workers=self.workers,
                sg=1,  # Skip-gram
                epochs=10
            )
            
            logger.info("Word2Vec 模型訓練完成")
            logger.info(f"詞彙表大小: {len(model.wv.key_to_index)}")
            
            return model
            
        except Exception as e:
            logger.error(f"訓練 Word2Vec 模型失敗: {str(e)}")
            return None
    
    def evaluate_model(self, model: Word2Vec) -> Dict[str, Any]:
        """
        評估模型
        
        Args:
            model: 訓練好的模型
            
        Returns:
            Dict[str, Any]: 評估結果
        """
        if not model:
            return {}
        
        evaluation_results = {
            'vocabulary_size': len(model.wv.key_to_index),
            'vector_size': model.vector_size,
            'window': model.window,
            'min_count': model.min_count
        }
        
        # 測試相似詞
        test_words = ['投資', '科技', '學習', '工作', '健康']
        similar_words = {}
        
        for word in test_words:
            if word in model.wv:
                try:
                    similar = model.wv.most_similar(word, topn=5)
                    similar_words[word] = similar
                except Exception as e:
                    logger.warning(f"計算 {word} 的相似詞失敗: {str(e)}")
        
        evaluation_results['similar_words'] = similar_words
        
        logger.info("模型評估完成")
        logger.info(f"詞彙表大小: {evaluation_results['vocabulary_size']}")
        
        return evaluation_results
    
    def save_model(self, model: Word2Vec, evaluation_results: Dict[str, Any]) -> bool:
        """
        保存模型和評估結果
        
        Args:
            model: 訓練好的模型
            evaluation_results: 評估結果
            
        Returns:
            bool: 保存是否成功
        """
        if not model:
            return False
        
        try:
            # 保存模型
            model.save(str(self.model_save_path))
            logger.info(f"模型已保存到: {self.model_save_path}")
            
            # 保存評估結果
            eval_path = self.model_save_path.with_suffix('.eval.json')
            with open(eval_path, 'w', encoding='utf-8') as f:
                json.dump(evaluation_results, f, ensure_ascii=False, indent=2)
            logger.info(f"評估結果已保存到: {eval_path}")
            
            # 保存詞彙表
            vocab_path = self.model_save_path.with_suffix('.vocab.txt')
            with open(vocab_path, 'w', encoding='utf-8') as f:
                for word in sorted(model.wv.key_to_index.keys()):
                    f.write(f"{word}\n")
            logger.info(f"詞彙表已保存到: {vocab_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"保存模型失敗: {str(e)}")
            return False
    
    def train_and_save(self) -> bool:
        """
        完整的訓練和保存流程
        
        Returns:
            bool: 是否成功
        """
        logger.info("🚀 開始 Word2Vec 模型訓練流程")
        
        try:
            # 1. 載入數據
            logger.info("步驟 1: 載入 Podcast 數據")
            texts = self.load_podcast_data()
            
            if not texts:
                logger.error("沒有找到可用的文本數據")
                return False
            
            # 2. 預處理
            logger.info("步驟 2: 預處理文本")
            processed_texts = self.preprocess_texts(texts)
            
            if not processed_texts:
                logger.error("預處理後沒有可用的文本")
                return False
            
            # 3. 訓練模型
            logger.info("步驟 3: 訓練 Word2Vec 模型")
            model = self.train_word2vec_model(processed_texts)
            
            if not model:
                logger.error("模型訓練失敗")
                return False
            
            # 4. 評估模型
            logger.info("步驟 4: 評估模型")
            evaluation_results = self.evaluate_model(model)
            
            # 5. 保存模型
            logger.info("步驟 5: 保存模型")
            success = self.save_model(model, evaluation_results)
            
            if success:
                logger.info("✅ Word2Vec 模型訓練完成")
                return True
            else:
                logger.error("❌ 模型保存失敗")
                return False
                
        except Exception as e:
            logger.error(f"❌ 訓練流程失敗: {str(e)}")
            return False


def main():
    """主函數"""
    # 設定日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 初始化訓練器
    trainer = Word2VecTrainer(
        data_dir="../../../data/raw",
        model_save_path="models/word2vec_podcast.model",
        min_count=2,
        vector_size=100,
        window=5,
        workers=4
    )
    
    # 執行訓練
    success = trainer.train_and_save()
    
    if success:
        print("✅ Word2Vec 模型訓練成功")
    else:
        print("❌ Word2Vec 模型訓練失敗")


if __name__ == "__main__":
    main() 