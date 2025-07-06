"""資料提取器模組，負責從SQL備份檔案中提取測試資料。"""

import re
import json
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# 添加父目錄到路徑以支援絕對導入
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from data_cleaning.config.config import Config
except ImportError:
    # Fallback: 相對導入
    from config.config import Config

logger = logging.getLogger(__name__)


class DataExtractor:
    """資料提取器類別，負責從SQL備份檔案中提取和處理資料。"""
    
    def __init__(self, config: Config):
        """初始化資料提取器。
        
        Args:
            config: 設定物件
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def extract_episodes_from_sql(self, sample_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """從SQL備份檔案中提取episodes資料。
        
        Args:
            sample_size: 提取的資料量，如果為None則使用設定中的預設值
            
        Returns:
            提取的episodes資料列表
        """
        if sample_size is None:
            sample_size = self.config.get_test_config().sample_size
            
        backup_file_path = self.config.get_backup_file_path()
        self.logger.info(f"開始從 {backup_file_path} 提取 {sample_size} 筆資料")
        
        episodes = []
        try:
            with open(backup_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # 尋找COPY語句
            copy_pattern = r'COPY public\.episodes.*?FROM stdin;\n(.*?)\\\.'
            copy_match = re.search(copy_pattern, content, re.DOTALL)
            
            if not copy_match:
                self.logger.error("找不到COPY語句")
                return []
                
            data_section = copy_match.group(1)
            lines = data_section.strip().split('\n')
            
            # 解析每一行資料
            for i, line in enumerate(lines[:sample_size]):
                episode = self._parse_episode_line(line)
                if episode:
                    episodes.append(episode)
                    
            self.logger.info(f"成功提取 {len(episodes)} 筆episodes資料")
            return episodes
            
        except Exception as e:
            self.logger.error(f"提取資料時發生錯誤: {e}")
            return []
    
    def _parse_episode_line(self, line: str) -> Optional[Dict[str, Any]]:
        """解析單行episode資料。
        
        Args:
            line: 單行資料
            
        Returns:
            解析後的episode字典，如果解析失敗則返回None
        """
        try:
            # 使用tab分割，但需要處理欄位內可能包含tab的情況
            # 這裡使用簡單的分割方法，實際可能需要更複雜的解析
            parts = line.split('\t')
            
            if len(parts) < 13:  # 確保有足夠的欄位
                return None
                
            episode = {
                'episode_id': parts[0].strip(),
                'podcast_id': parts[1].strip(),
                'episode_title': parts[2].strip(),
                'published_date': parts[3].strip(),
                'audio_url': parts[4].strip(),
                'duration': parts[5].strip(),
                'description': parts[6].strip(),
                'audio_preview_url': parts[7].strip(),
                'languages': parts[8].strip(),
                'explicit': parts[9].strip(),
                'created_at': parts[10].strip(),
                'updated_at': parts[11].strip(),
                'apple_episodes_ranking': parts[12].strip() if len(parts) > 12 else None
            }
            
            return episode
            
        except Exception as e:
            self.logger.warning(f"解析行資料時發生錯誤: {e}")
            return None
    
    def save_to_json(self, episodes: List[Dict[str, Any]], filename: str = "extracted_episodes.json") -> str:
        """將提取的資料儲存為JSON檔案。
        
        Args:
            episodes: episodes資料列表
            filename: 輸出檔案名稱
            
        Returns:
            輸出檔案路徑
        """
        output_path = self.config.get_test_output_path()
        file_path = f"{output_path}/{filename}"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(episodes, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"資料已儲存至 {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"儲存JSON檔案時發生錯誤: {e}")
            return ""
    
    def save_to_csv(self, episodes: List[Dict[str, Any]], filename: str = "extracted_episodes.csv") -> str:
        """將提取的資料儲存為CSV檔案。
        
        Args:
            episodes: episodes資料列表
            filename: 輸出檔案名稱
            
        Returns:
            輸出檔案路徑
        """
        if not episodes:
            return ""
            
        output_path = self.config.get_test_output_path()
        file_path = f"{output_path}/{filename}"
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=episodes[0].keys())
                writer.writeheader()
                writer.writerows(episodes)
            
            self.logger.info(f"資料已儲存至 {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"儲存CSV檔案時發生錯誤: {e}")
            return ""
    
    def get_sample_data(self, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """取得樣本資料，包含統計資訊。
        
        Args:
            sample_size: 樣本大小
            
        Returns:
            包含樣本資料和統計資訊的字典
        """
        episodes = self.extract_episodes_from_sql(sample_size)
        
        if not episodes:
            return {"episodes": [], "statistics": {}}
        
        # 計算統計資訊
        statistics = {
            "total_episodes": len(episodes),
            "unique_podcasts": len(set(ep['podcast_id'] for ep in episodes)),
            "languages": list(set(ep['languages'] for ep in episodes if ep['languages'])),
            "date_range": {
                "earliest": min(ep['published_date'] for ep in episodes if ep['published_date']),
                "latest": max(ep['published_date'] for ep in episodes if ep['published_date'])
            }
        }
        
        return {
            "episodes": episodes,
            "statistics": statistics
        } 