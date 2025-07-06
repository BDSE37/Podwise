#!/usr/bin/env python3
"""
簡化版基本功能測試腳本
測試文本清理和標籤提取功能（不依賴 emoji 套件）
"""

import re
from typing import List, Dict, Any
import pandas as pd
from pathlib import Path


class TextCleaner:
    """文本清理器"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        清理文本，移除表情符號和特殊字元
        
        Args:
            text: 原始文本
            
        Returns:
            清理後的文本
        """
        if not text:
            return ""
        
        # 移除表情符號（使用 Unicode 範圍）
        text = re.sub(r'[\U0001F600-\U0001F64F]', '', text)  # 表情符號
        text = re.sub(r'[\U0001F300-\U0001F5FF]', '', text)  # 雜項符號
        text = re.sub(r'[\U0001F680-\U0001F6FF]', '', text)  # 交通運輸
        text = re.sub(r'[\U0001F1E0-\U0001F1FF]', '', text)  # 國旗
        text = re.sub(r'[\U00002600-\U000027BF]', '', text)  # 雜項符號
        text = re.sub(r'[\U0001F900-\U0001F9FF]', '', text)  # 補充符號
        
        # 移除顏文字
        text = re.sub(r'[^\u4e00-\u9fff\u3400-\u4dbf\w\s.,!?;:()\[\]{}"\'-]', '', text)
        
        # 移除多餘的空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除開頭和結尾的空白
        text = text.strip()
        
        return text
    
    @staticmethod
    def clean_title(title: str) -> str:
        """
        清理標題，移除表情符號和特殊字元
        
        Args:
            title: 原始標題
            
        Returns:
            清理後的標題
        """
        if not title:
            return ""
        
        # 移除表情符號
        title = re.sub(r'[\U0001F600-\U0001F64F]', '', title)
        title = re.sub(r'[\U0001F300-\U0001F5FF]', '', title)
        title = re.sub(r'[\U0001F680-\U0001F6FF]', '', title)
        title = re.sub(r'[\U0001F1E0-\U0001F1FF]', '', title)
        title = re.sub(r'[\U00002600-\U000027BF]', '', title)
        title = re.sub(r'[\U0001F900-\U0001F9FF]', '', title)
        
        # 移除特殊字元，保留中文、英文、數字和基本標點
        title = re.sub(r'[^\u4e00-\u9fff\u3400-\u4dbf\w\s.,!?;:()\[\]{}"\'-]', '', title)
        
        # 移除多餘的空白
        title = re.sub(r'\s+', ' ', title)
        
        # 移除開頭和結尾的空白
        title = title.strip()
        
        return title


class SimpleTagProcessor:
    """簡單標籤處理器"""
    
    def __init__(self, tag_csv_path: str = "TAG_info.csv"):
        self.tag_csv_path = Path(tag_csv_path)
        self.tag_mappings: Dict[str, str] = {}
        self.keyword_to_tags: Dict[str, List[str]] = {}
        self._load_tags()
    
    def _load_tags(self):
        """載入標籤資料"""
        try:
            if not self.tag_csv_path.exists():
                print(f"標籤檔案不存在: {self.tag_csv_path}")
                self._create_default_tags()
                return
            
            # 讀取 CSV 檔案
            df = pd.read_csv(self.tag_csv_path)
            print(f"成功載入標籤檔案: {self.tag_csv_path}")
            print(f"標籤檔案欄位: {list(df.columns)}")
            
            # 處理每個類別
            for _, row in df.iterrows():
                main_category = row.get("主要類別", "")
                sub_category = row.get("子類別", "")
                tags_str = row.get("標籤", "")
                weight = row.get("權重", 1.0)
                
                if tags_str and isinstance(tags_str, str):
                    # 分割標籤
                    tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
                    
                    # 建立關鍵字映射
                    for tag in tags:
                        self.tag_mappings[tag] = main_category
                        self.keyword_to_tags[tag.lower()] = tags
                        
                        # 也將主要類別和子類別加入映射
                        if main_category:
                            self.keyword_to_tags[main_category.lower()] = tags
                        if sub_category:
                            self.keyword_to_tags[sub_category.lower()] = tags
            
            print(f"載入的標籤映射: {self.tag_mappings}")
            
        except Exception as e:
            print(f"載入標籤檔案失敗: {e}")
            self._create_default_tags()
    
    def _create_default_tags(self):
        """建立預設標籤"""
        default_tags = {
            "科技": ["AI", "人工智慧", "科技", "技術"],
            "商業": ["商業", "企業", "投資", "理財"],
            "教育": ["教育", "學習", "知識"],
            "健康": ["健康", "運動", "飲食"],
            "娛樂": ["娛樂", "音樂", "電影"]
        }
        
        for category, tags in default_tags.items():
            for tag in tags:
                self.tag_mappings[tag] = category
                self.keyword_to_tags[tag.lower()] = tags
    
    def extract_tags(self, chunk_text: str) -> List[str]:
        """
        提取標籤
        
        Args:
            chunk_text: 文本塊
            
        Returns:
            標籤列表
        """
        try:
            tags = []
            chunk_lower = chunk_text.lower()
            
            # 第一階段：基於 TAG_info.csv 的標籤匹配
            for keyword, tag_list in self.keyword_to_tags.items():
                if keyword in chunk_lower:
                    tags.extend(tag_list)
            
            # 第二階段：如果沒有標籤，使用智能標籤系統
            if not tags:
                tags = self._intelligent_tag_extraction(chunk_text)
            
            # 第三階段：最終備援
            if not tags:
                tags = self._fallback_tag_extraction(chunk_text)
            
            # 驗證和清理標籤
            tags = self._validate_and_clean_tags(tags, chunk_text)
            
            return tags[:3]  # 限制最多 3 個標籤
            
        except Exception as e:
            print(f"提取標籤失敗: {e}")
            return self._fallback_tag_extraction(chunk_text)
    
    def _intelligent_tag_extraction(self, chunk_text: str) -> List[str]:
        """智能標籤提取"""
        tags = []
        chunk_lower = chunk_text.lower()
        
        # 關鍵字匹配
        keyword_mapping = {
            'ai': ['AI', '人工智慧'],
            '科技': ['科技', '技術'],
            '商業': ['商業', '企業'],
            '教育': ['教育', '學習'],
            '創業': ['創業', '新創'],
            '管理': ['管理', '領導'],
            '投資': ['投資', '理財'],
            '健康': ['健康', '運動'],
            '娛樂': ['娛樂', '音樂'],
            '政治': ['政治', '政策']
        }
        
        for keyword, tag_list in keyword_mapping.items():
            if keyword in chunk_lower:
                tags.extend(tag_list)
        
        return list(set(tags))  # 去重
    
    def _fallback_tag_extraction(self, chunk_text: str) -> List[str]:
        """備援標籤提取"""
        # 基於文本長度和內容的基本標籤
        if len(chunk_text) > 500:
            return ['長文本', '詳細內容']
        elif len(chunk_text) > 200:
            return ['中等文本', '一般內容']
        else:
            return ['短文本', '簡要內容']
    
    def _validate_and_clean_tags(self, tags: List[str], chunk_text: str) -> List[str]:
        """驗證和清理標籤"""
        valid_tags = []
        
        for tag in tags:
            if tag and len(tag.strip()) > 0:
                # 清理標籤
                clean_tag = re.sub(r'[^\u4e00-\u9fff\u3400-\u4dbf\w\s]', '', tag.strip())
                if clean_tag and len(clean_tag) <= 20:  # 限制標籤長度
                    valid_tags.append(clean_tag)
        
        return valid_tags


def test_text_cleaner():
    """測試文本清理器"""
    print("=== 測試文本清理器 ===")
    
    cleaner = TextCleaner()
    
    # 測試案例
    test_cases = [
        "這是一個測試文本 😊 包含表情符號",
        "Hello World! 🌍 混合中英文",
        "股癌 EP123 📈 投資理財 💰",
        "科技新聞 🔥 AI 人工智慧 🤖",
        "正常文本，沒有特殊字元",
        "包含顏文字 (｡◕‿◕｡) 的文本",
        "多個表情符號 🎉🎊🎈 測試",
        ""
    ]
    
    for i, text in enumerate(test_cases):
        cleaned = cleaner.clean_text(text)
        print(f"原始: {text}")
        print(f"清理後: {cleaned}")
        print(f"長度變化: {len(text)} -> {len(cleaned)}")
        print("-" * 50)
    
    # 測試標題清理
    print("\n=== 測試標題清理 ===")
    title_test_cases = [
        "EP001_股癌 📈 投資理財",
        "科技新聞 🔥 AI 人工智慧",
        "正常標題，沒有特殊字元",
        "包含表情符號的標題 🎉"
    ]
    
    for title in title_test_cases:
        cleaned_title = cleaner.clean_title(title)
        print(f"原始標題: {title}")
        print(f"清理後標題: {cleaned_title}")
        print("-" * 30)


def test_tag_processor():
    """測試標籤處理器"""
    print("\n=== 測試標籤處理器 ===")
    
    processor = SimpleTagProcessor("TAG_info.csv")
    
    # 測試案例
    test_cases = [
        "人工智慧技術正在快速發展，機器學習和深度學習成為熱門話題。",
        "投資理財是現代人必須學習的技能，股票和基金投資需要謹慎。",
        "創業需要創新思維和執行力，新創公司面臨許多挑戰。",
        "健康生活包括運動和飲食，對身體健康至關重要。",
        "這是一段普通的文本，沒有明顯的關鍵字。",
        "科技新聞報導最新的技術發展，包括AI、區塊鏈等領域。",
        "教育學習是終身過程，知識和技能的提升對個人發展很重要。",
        "娛樂音樂讓人放鬆心情，電影和遊戲也是重要的休閒活動。"
    ]
    
    for i, text in enumerate(test_cases):
        print(f"\n測試案例 {i+1}: {text[:50]}...")
        tags = processor.extract_tags(text)
        print(f"提取的標籤: {tags}")


def test_text_chunking():
    """測試文本切分"""
    print("\n=== 測試文本切分 ===")
    
    def split_text_into_chunks(text: str, max_chunk_size: int = 500) -> List[str]:
        """將文本切分為 chunks"""
        if not text:
            return []
        
        # 按句子切分
        sentences = re.split(r'[。！？.!?]', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 如果當前 chunk 加上新句子超過最大長度，保存當前 chunk
            if len(current_chunk) + len(sentence) > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += sentence + "。"
        
        # 添加最後一個 chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    # 測試文本
    test_text = """
    這是第一段文本。它包含了一些基本的內容。我們需要測試文本切分功能是否正常工作。
    
    這是第二段文本。它討論了人工智慧和機器學習的相關話題。AI技術正在快速發展。
    
    這是第三段文本。它談論了投資理財的重要性。股票市場充滿了機會和風險。
    
    這是第四段文本。它介紹了創業的基本概念。新創公司需要創新思維和執行力。
    
    這是第五段文本。它討論了健康生活的重要性。運動和飲食對身體健康至關重要。
    """
    
    chunks = split_text_into_chunks(test_text)
    
    print(f"原始文本長度: {len(test_text)}")
    print(f"切分後 chunks 數量: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1} (長度: {len(chunk)}):")
        print(f"內容: {chunk[:100]}{'...' if len(chunk) > 100 else ''}")


def main():
    """主測試函數"""
    print("開始執行簡化版基本功能測試")
    print("=" * 60)
    
    # 執行各種測試
    test_text_cleaner()
    test_tag_processor()
    test_text_chunking()
    
    print("\n" + "=" * 60)
    print("所有測試完成！")


if __name__ == "__main__":
    main() 