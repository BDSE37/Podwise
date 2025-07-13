#!/usr/bin/env python3
"""
TAG 處理器

此腳本用於處理 TAG_info.csv 檔案，提供：
- 標籤匹配與提取
- 智能標籤提取（Word2Vec + Transformer）
- 標籤統計與分析
- 若 chunk 內無任何標籤命中，自動 fallback 執行 SmartTagExtractor 智能標籤提取

作者: Podwise Team
版本: 1.0.0
"""

import logging
import pandas as pd
import re
import json
from typing import List, Dict, Tuple, Set, Any, Optional
from collections import defaultdict
from pathlib import Path

# 導入工具
from ..core.enhanced_vector_search import SmartTagExtractor

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TagProcessor:
    """
    標籤處理器
    - 從 csv/TAG_info.csv 讀取標籤與同義詞對應
    - 若無命中自動 fallback 到 SmartTagExtractor
    """
    
    def __init__(self, tag_csv_path: str = "csv/TAG_info.csv"):
        """
        初始化標籤處理器
        Args:
            tag_csv_path: 標籤對應 CSV 檔案路徑
        """
        self.tag_csv_path = tag_csv_path
        self.tag_mappings = {}
        self.keyword_to_tags = defaultdict(set)
        self.smart_tag_extractor = SmartTagExtractor(existing_tags_file=tag_csv_path)
        self.load_tag_mappings()
    
    def load_tag_mappings(self):
        """
        載入標籤對應關係，支援多欄同義詞
        """
        try:
            df = pd.read_csv(self.tag_csv_path, header=1)  # 跳過第一行中文欄位名，第二行為英文
            logger.info(f"成功載入標籤檔案: {self.tag_csv_path}")
            tag_col = None
            # 找到 TAG 欄位
            for col in df.columns:
                if str(col).strip().lower() == 'tag':
                    tag_col = col
                    break
            if not tag_col:
                raise ValueError('找不到 TAG 欄位')
            # 相關詞欄位
            synonym_cols = [col for col in df.columns if col != tag_col and ("sync" in str(col).lower() or "相關" in str(col))]
            for _, row in df.iterrows():
                tag = str(row[tag_col]).strip()
                if not tag or tag == 'nan':
                    continue
                # 將 TAG 本身也視為關鍵字
                self.keyword_to_tags[tag.lower()].add(tag)
                self.tag_mappings[tag] = tag
                # 處理所有同義詞欄位
                for col in synonym_cols:
                    syn = str(row[col]).strip()
                    if syn and syn != 'nan':
                        self.keyword_to_tags[syn.lower()].add(tag)
            logger.info(f"載入 {len(self.tag_mappings)} 個標籤對應關係，{len(self.keyword_to_tags)} 組關鍵字")
        except Exception as e:
            logger.error(f"載入標籤檔案失敗: {e}")
            self.create_default_tags()
    
    def create_default_tags(self):
        """
        建立預設標籤對應關係
        """
        default_tags = {
            '人工智慧': ['AI', '機器學習', '深度學習', '自然語言處理'],
            '科技': ['技術', '創新', '數位化'],
            '商業': ['企業', '管理', '策略', '市場'],
            '教育': ['學習', '培訓', '知識', '技能'],
            '創業': ['新創', '商業模式', '投資'],
            '工作': ['職場', '效率', '生產力'],
            '時間管理': ['效率', '規劃', '優先級'],
            '領導力': ['管理', '團隊', '溝通'],
            '雲端運算': ['雲端', '技術架構', '基礎設施'],
            '區塊鏈': ['加密貨幣', '去中心化', '智能合約'],
            '半導體': ['晶片', '製造', '供應鏈'],
            '新創': ['創業', '創新', '投資'],
            '台灣產業': ['本土', '製造業', '科技業'],
            '全球供應鏈': ['國際', '貿易', '物流'],
            '生態系統': ['環境', '合作', '夥伴關係']
        }
        for keyword, tags in default_tags.items():
            self.keyword_to_tags[keyword.lower()] = set(tags)
            self.tag_mappings[keyword] = tags[0]
        logger.info("使用預設標籤對應關係")
    
    def split_text_into_chunks(self, text: str, max_chunk_size: int = 1024) -> List[str]:
        if not text:
            return []
        sentences = re.split(r'[\n\r]+', text)
        chunks = []
        current_chunk = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += "\n" + sentence
                else:
                    current_chunk = sentence
        if current_chunk:
            chunks.append(current_chunk.strip())
        logger.info(f"文本切斷成 {len(chunks)} 個 chunks")
        return chunks
    
    def extract_tags_from_chunk(self, chunk: str) -> List[str]:
        matched_tags = set()
        chunk_lower = chunk.lower()
        for keyword, tags in self.keyword_to_tags.items():
            if keyword and keyword in chunk_lower:
                matched_tags.update(tags)
        additional_tags = self.apply_tag_rules(chunk)
        matched_tags.update(additional_tags)
        # fallback: 若無任何標籤命中，呼叫 SmartTagExtractor
        if not matched_tags:
            smart_result = self.smart_tag_extractor.extract_smart_tags(chunk)
            logger.info(f"SmartTagExtractor fallback: {smart_result.extracted_tags}")
            matched_tags.update(smart_result.extracted_tags)
        return list(matched_tags)
    
    def apply_tag_rules(self, chunk: str) -> Set[str]:
        additional_tags = set()
        chunk_lower = chunk.lower()
        rules = {
            r'\bai\b|\b人工智慧\b|\b機器學習\b': ['人工智慧', 'AI'],
            r'\b雲端\b|\bcloud\b': ['雲端運算'],
            r'\b區塊鏈\b|\bblockchain\b': ['區塊鏈'],
            r'\b創業\b|\b新創\b': ['創業', '新創'],
            r'\b領導\b|\b管理\b': ['領導力', '管理'],
            r'\b時間\b|\b效率\b': ['時間管理', '效率'],
            r'\b半導體\b|\b晶片\b': ['半導體'],
            r'\b台灣\b|\b本土\b': ['台灣產業'],
            r'\b全球\b|\b國際\b': ['全球供應鏈'],
            r'\b教育\b|\b學習\b': ['教育', '學習'],
            r'\b商業\b|\b企業\b': ['商業', '企業']
        }
        for pattern, tags in rules.items():
            if re.search(pattern, chunk_lower):
                additional_tags.update(tags)
        return additional_tags
    
    def process_mongodb_document(self, document: Dict, text_field: str = 'content') -> List[Dict]:
        if text_field not in document:
            logger.warning(f"文件缺少 {text_field} 欄位")
            return []
        text = document[text_field]
        chunks = self.split_text_into_chunks(text)
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            tags = self.extract_tags_from_chunk(chunk)
            processed_chunk = {
                'chunk_id': f"{document.get('_id', 'unknown')}_{i}",
                'chunk_index': i,
                'chunk_text': chunk,
                'tags': tags,
                'source_document_id': str(document.get('_id')),
                'source_field': text_field,
                'chunk_length': len(chunk),
                'tag_count': len(tags)
            }
            processed_chunks.append(processed_chunk)
        logger.info(f"處理文件 {document.get('_id')}，產生 {len(processed_chunks)} 個 chunks")
        return processed_chunks
    
    def get_tag_statistics(self) -> Dict:
        tag_counts = defaultdict(int)
        for tags in self.keyword_to_tags.values():
            for tag in tags:
                tag_counts[tag] += 1
        return {
            'total_keywords': len(self.keyword_to_tags),
            'total_unique_tags': len(tag_counts),
            'tag_frequency': dict(tag_counts),
            'keyword_to_tags': dict(self.keyword_to_tags)
        }
    
    def export_tag_mappings(self, output_file: str = 'tag_mappings.json'):
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.tag_mappings, f, ensure_ascii=False, indent=2)
            logger.info(f"標籤對應關係已匯出到 {output_file}")
        except Exception as e:
            logger.error(f"匯出標籤對應關係失敗: {e}")

def test_tag_processor():
    """測試標籤處理器"""
    processor = TagProcessor()
    # 測試文本
    test_text = """
    人工智慧正在改變我們的工作方式。機器學習技術讓電腦能夠從資料中學習，
    深度學習在圖像識別方面表現優異。雲端運算提供了彈性的基礎設施，
    區塊鏈技術確保了資料的安全性。台灣的半導體產業在全球供應鏈中扮演重要角色。
    創業家需要具備領導力，有效的時間管理對於提升工作效率很重要。
    教育系統需要跟上科技發展的腳步，商業模式也在不斷創新。
    """
    # 測試文本切斷
    chunks = processor.split_text_into_chunks(test_text)
    print("文本切斷結果:")
    for i, chunk in enumerate(chunks):
        tags = processor.extract_tags_from_chunk(chunk)
        print(f"Chunk {i+1}: {chunk[:100]}...")
        print(f"標籤: {tags}")
        print()
    # 顯示統計資訊
    stats = processor.get_tag_statistics()
    print("標籤統計:")
    print(f"關鍵字數量: {stats['total_keywords']}")
    print(f"唯一標籤數量: {stats['total_unique_tags']}")
    print(f"標籤頻率: {stats['tag_frequency']}")

if __name__ == "__main__":
    test_tag_processor() 