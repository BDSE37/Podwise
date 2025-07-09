#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股癌例外處理檔案清理器
專門處理"例外處理_股癌_RSS_1500839292.json"檔案
將episodes中的name欄位轉換為EP{集數}_股癌格式
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class StockCancerExceptionCleaner:
    """股癌例外處理檔案清理器"""
    
    def __init__(self, verbose: bool = True):
        """初始化清理器"""
        self.verbose = verbose
        self.stats = {
            'total_episodes': 0,
            'cleaned_episodes': 0,
            'error_episodes': 0,
            'unknown_episodes': 0
        }
    
    def log(self, message: str):
        """記錄訊息"""
        if self.verbose:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] {message}")
    
    def extract_episode_number(self, name: str) -> Optional[str]:
        """從episode name中提取集數"""
        if not name:
            return None
        
        # 股癌實際使用的集數模式
        patterns = [
            r'EP(\d+)',           # EP570
            r'第(\d+)集',         # 第570集
            r'Episode\s*(\d+)',   # Episode 570
            r'Ep\.\s*(\d+)',      # Ep. 570
            r'#(\d+)',            # #570
            r'(\d+)',             # 純數字（作為備用）
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                episode_num = match.group(1)
                # 驗證是否為合理的集數（1-9999）
                if episode_num.isdigit() and 1 <= int(episode_num) <= 9999:
                    return episode_num
        
        return None
    
    def normalize_episode_name(self, name: str) -> str:
        """將episode name正規化為EP{episode_number}_股癌格式"""
        if not name:
            return "EP0_股癌"
        
        # 提取集數
        episode_number = self.extract_episode_number(name)
        
        if episode_number:
            return f"EP{episode_number}_股癌"
        else:
            self.stats['unknown_episodes'] += 1
            return "EP0_股癌"
    
    def clean_episode(self, episode: Dict[str, Any]) -> Dict[str, Any]:
        """清理單個episode"""
        try:
            self.stats['total_episodes'] += 1
            
            # 複製episode資料
            cleaned_episode = episode.copy()
            
            # 清理name欄位
            if 'name' in cleaned_episode:
                original_name = cleaned_episode['name']
                cleaned_name = self.normalize_episode_name(original_name)
                cleaned_episode['name'] = cleaned_name
                
                if original_name != cleaned_name:
                    self.log(f"清理episode name: {original_name} -> {cleaned_name}")
            
            # 清理其他文本欄位
            text_fields = ['description']
            for field in text_fields:
                if field in cleaned_episode and cleaned_episode[field]:
                    cleaned_episode[field] = self.clean_text(cleaned_episode[field])
            
            self.stats['cleaned_episodes'] += 1
            return cleaned_episode
            
        except Exception as e:
            self.log(f"❌ 清理episode失敗: {e}")
            self.stats['error_episodes'] += 1
            
            # 返回原始資料並標記錯誤
            error_episode = episode.copy()
            error_episode['cleaning_status'] = 'error'
            error_episode['error_message'] = str(e)
            error_episode['cleaned_at'] = datetime.now().isoformat()
            return error_episode
    
    def clean_text(self, text: str) -> str:
        """清理文本內容"""
        if not text:
            return text
        
        # 移除HTML標籤
        text = self.remove_html_tags(text)
        
        # 移除表情符號
        text = self.remove_emoji(text)
        
        # 移除特殊字元
        text = self.remove_special_chars(text)
        
        # 清理多餘空白
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def remove_html_tags(self, text: str) -> str:
        """移除HTML標籤"""
        # 移除HTML標籤
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除HTML實體
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' ',
            '&#xff0c;': '，',
            '&#xff1b;': '；',
            '&#xff1a;': '：',
            '&#xff01;': '！',
            '&#xff1f;': '？',
            '&#xff08;': '（',
            '&#xff09;': '）',
            '&#x43;': '+',
        }
        
        for entity, replacement in html_entities.items():
            text = text.replace(entity, replacement)
        
        return text
    
    def remove_emoji(self, text: str) -> str:
        """移除表情符號"""
        # 移除Unicode表情符號
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE
        )
        return emoji_pattern.sub('', text)
    
    def remove_special_chars(self, text: str) -> str:
        """移除特殊字元"""
        # 移除控制字元
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # 移除零寬字元
        text = re.sub(r'[\u200b-\u200d\uFEFF]', '', text)
        
        return text
    
    def clean_file(self, input_file: str, output_file: Optional[str] = None) -> bool:
        """清理整個檔案"""
        try:
            self.log(f"開始清理檔案: {input_file}")
            
            # 讀取JSON檔案
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 檢查是否包含episodes欄位
            if 'episodes' not in data:
                self.log("❌ 檔案中沒有找到episodes欄位")
                return False
            
            # 清理episodes
            episodes = data['episodes']
            self.log(f"找到 {len(episodes)} 個episodes")
            
            cleaned_episodes = []
            for i, episode in enumerate(episodes):
                cleaned_episode = self.clean_episode(episode)
                cleaned_episodes.append(cleaned_episode)
                
                if (i + 1) % 50 == 0:
                    self.log(f"已處理 {i + 1}/{len(episodes)} 個episodes")
            
            # 更新資料
            data['episodes'] = cleaned_episodes
            
            # 生成輸出檔案名稱
            if not output_file:
                input_path = Path(input_file)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = str(input_path.parent / f"{input_path.stem}_cleaned_{timestamp}.json")
            
            # 寫入清理後的檔案
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.log(f"✅ 清理完成，輸出檔案: {output_file}")
            self.print_stats()
            
            return True
            
        except Exception as e:
            self.log(f"❌ 清理檔案失敗: {e}")
            return False
    
    def print_stats(self):
        """印出統計資訊"""
        print("\n" + "="*50)
        print("清理統計資訊")
        print("="*50)
        print(f"總episodes數: {self.stats['total_episodes']}")
        print(f"成功清理: {self.stats['cleaned_episodes']}")
        print(f"清理失敗: {self.stats['error_episodes']}")
        print(f"未知集數: {self.stats['unknown_episodes']}")
        print("="*50)


def main():
    """主函數"""
    if len(sys.argv) < 2:
        print("使用方法: python clean_stock_cancer_exception.py <input_file> [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # 檢查輸入檔案是否存在
    if not Path(input_file).exists():
        print(f"❌ 輸入檔案不存在: {input_file}")
        sys.exit(1)
    
    # 創建清理器並執行清理
    cleaner = StockCancerExceptionCleaner(verbose=True)
    success = cleaner.clean_file(input_file, output_file)
    
    if success:
        print("✅ 清理完成")
        sys.exit(0)
    else:
        print("❌ 清理失敗")
        sys.exit(1)


if __name__ == "__main__":
    main() 