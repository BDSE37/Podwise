"""
Episodes 資料處理腳本

處理 episodes 資料夾中的 JSON 檔案，清理表情符號並對應到 PostgreSQL 資料庫欄位
"""

import json
import re
import os
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
import unicodedata
from cleanup_service import PostgresCleanupService
from config import config


class EpisodeProcessor:
    """Episodes 資料處理類別"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cleanup_service = PostgresCleanupService()
        
        # 表情符號清理規則
        self.emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE
        )
        
        # HTML 標籤清理
        self.html_pattern = re.compile(r'<[^>]+>')
        
        # 特殊字符清理
        self.special_chars_pattern = re.compile(r'[^\w\s\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df\u2a700-\u2b73f\u2b740-\u2b81f\u2b820-\u2ceaf\uf900-\ufaff\u3300-\u33ff\ufe30-\ufe4f\uf900-\ufaff\u3300-\u33ff\ufe30-\ufe4f]')
        
        # 頻道對應
        self.channel_mapping = {
            'business': {
                'channel_id': '1488295306',  # 使用現有的 podcast_id
                'channel_name': '商業頻道',
                'category': 'business'
            },
            'evucation': {
                'channel_id': '1452688611',  # 使用現有的 podcast_id
                'channel_name': '教育頻道',
                'category': 'education'
            }
        }
    
    def clean_emoji(self, text: str) -> str:
        """清理表情符號"""
        if not text:
            return text
        
        # 移除表情符號
        text = self.emoji_pattern.sub('', text)
        
        # 移除 HTML 標籤
        text = self.html_pattern.sub('', text)
        
        # 清理特殊字符但保留中文
        text = self.special_chars_pattern.sub('', text)
        
        # 清理多餘空白
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def clean_description(self, description: str) -> str:
        """清理描述文字"""
        if not description:
            return description
        
        # 移除 HTML 標籤
        description = self.html_pattern.sub('', description)
        
        # 移除表情符號
        description = self.emoji_pattern.sub('', description)
        
        # 移除常見的推廣文字
        promotion_patterns = [
            r'Powered by.*?Firstory Hosting.*?',
            r'IG:.*?',
            r'https?://[^\s]+',
            r'留言告訴我你對這一集的想法.*?',
            r'SUBSCRIBE TO OUR NEWSLETTER.*?',
            r'FIND BBC LEARNING ENGLISH HERE.*?',
            r'LIKE PODCASTS\?.*?',
            r'They\'re all available by searching in your podcast app.*?',
            r'Find a full transcript.*?',
            r'Check out.*?',
            r'Visit our website.*?',
            r'Follow us.*?'
        ]
        
        for pattern in promotion_patterns:
            description = re.sub(pattern, '', description, flags=re.IGNORECASE | re.DOTALL)
        
        # 清理多餘空白和換行
        description = re.sub(r'\s+', ' ', description).strip()
        
        return description
    
    def extract_episode_number(self, title: str) -> Optional[str]:
        """從標題中提取集數"""
        if not title:
            return None
        
        # 匹配 EP001, EP002 等格式
        ep_pattern = re.search(r'EP(\d+)', title, re.IGNORECASE)
        if ep_pattern:
            return ep_pattern.group(1)
        
        # 匹配其他可能的集數格式
        number_pattern = re.search(r'(\d+)', title)
        if number_pattern:
            return number_pattern.group(1)
        
        return None
    
    def parse_published_date(self, published: str) -> Optional[datetime]:
        """解析發布日期"""
        if not published:
            return None
        
        try:
            # 處理不同的日期格式
            date_formats = [
                '%a, %d %b %Y %H:%M:%S %Z',  # Wed, 25 Jun 2025 04:32:47 GMT
                '%a, %d %b %Y %H:%M:%S %z',  # 帶時區偏移
                '%Y-%m-%d %H:%M:%S',         # 標準格式
                '%Y-%m-%d'                   # 僅日期
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(published, fmt)
                except ValueError:
                    continue
            
            # 如果都失敗，嘗試自動解析
            return datetime.fromisoformat(published.replace('Z', '+00:00'))
            
        except Exception as e:
            self.logger.warning(f"無法解析日期 {published}: {e}")
            return None
    
    def process_episode_data(self, episode: Dict[str, Any], channel_info: Dict[str, str]) -> Dict[str, Any]:
        """處理單一 episode 資料"""
        processed = {
            'episode_id': episode.get('id', ''),
            'title': self.clean_emoji(episode.get('title', '')),
            'description': self.clean_description(episode.get('description', '')),
            'audio_url': episode.get('audio_url', ''),
            'published_date': episode.get('published', ''),
            'channel_id': channel_info['channel_id'],
            'channel_name': channel_info['channel_name'],
            'category': channel_info['category'],
            'episode_number': self.extract_episode_number(episode.get('title', '')),
            'processed_at': datetime.now().isoformat()
        }
        
        # 解析發布日期
        published_date = self.parse_published_date(episode.get('published', ''))
        if published_date:
            processed['published_timestamp'] = published_date.isoformat()
            processed['published_year'] = published_date.year
            processed['published_month'] = published_date.month
            processed['published_day'] = published_date.day
            # 新增 date 物件供資料庫插入使用
            processed['published_date_obj'] = published_date.date()
        
        return processed
    
    def load_json_file(self, file_path: str) -> List[Dict[str, Any]]:
        """載入 JSON 檔案"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data if isinstance(data, list) else [data]
        except Exception as e:
            self.logger.error(f"載入檔案失敗 {file_path}: {e}")
            return []
    
    def process_channel_directory(self, channel_dir: str, channel_info: Dict[str, str]) -> List[Dict[str, Any]]:
        """處理整個頻道目錄"""
        processed_episodes = []
        
        if not os.path.exists(channel_dir):
            self.logger.error(f"目錄不存在: {channel_dir}")
            return processed_episodes
        
        # 取得所有 JSON 檔案
        json_files = [f for f in os.listdir(channel_dir) if f.endswith('.json')]
        
        for json_file in json_files:
            file_path = os.path.join(channel_dir, json_file)
            self.logger.info(f"處理檔案: {json_file}")
            
            episodes = self.load_json_file(file_path)
            
            for episode in episodes:
                processed = self.process_episode_data(episode, channel_info)
                processed_episodes.append(processed)
        
        return processed_episodes
    
    def save_processed_data(self, data: List[Dict[str, Any]], output_file: str):
        """儲存處理後的資料"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"資料已儲存到: {output_file}")
        except Exception as e:
            self.logger.error(f"儲存資料失敗: {e}")
    
    def insert_to_database(self, episodes: List[Dict[str, Any]], table_name: str = 'episodes'):
        """將資料插入資料庫"""
        if not self.cleanup_service.connect():
            self.logger.error("無法連線到資料庫")
            return False
        
        try:
            inserted_count = 0
            
            for episode in episodes:
                # 檢查是否已存在 (使用 episode_title 和 published_date 組合檢查)
                check_query = f"SELECT episode_id FROM {table_name} WHERE episode_title = %s AND published_date = %s"
                published_date = episode.get('published_date_obj')
                self.cleanup_service.cursor.execute(check_query, (episode['title'], published_date))
                
                if self.cleanup_service.cursor.fetchone():
                    self.logger.info(f"Episode 已存在: {episode['title']}")
                    continue
                
                # 插入新記錄
                insert_query = f"""
                    INSERT INTO {table_name} (
                        podcast_id, episode_title, published_date, audio_url, description,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, NOW(), NOW()
                    )
                """
                
                values = (
                    episode['channel_id'],  # 使用 channel_id 作為 podcast_id
                    episode['title'],
                    episode.get('published_date_obj'),  # 使用解析後的 date 物件
                    episode['audio_url'],
                    episode['description']
                )
                
                self.cleanup_service.cursor.execute(insert_query, values)
                inserted_count += 1
            
            self.cleanup_service.connection.commit()
            self.logger.info(f"成功插入 {inserted_count} 筆記錄")
            return True
            
        except Exception as e:
            self.cleanup_service.connection.rollback()
            self.logger.error(f"插入資料庫失敗: {e}")
            return False
        finally:
            self.cleanup_service.disconnect()
    
    def process_all_channels(self, episodes_dir: str, output_dir: str = None, insert_db: bool = False):
        """處理所有頻道"""
        all_processed = []
        
        for channel_name, channel_info in self.channel_mapping.items():
            channel_dir = os.path.join(episodes_dir, channel_name)
            
            if not os.path.exists(channel_dir):
                self.logger.warning(f"頻道目錄不存在: {channel_dir}")
                continue
            
            self.logger.info(f"處理頻道: {channel_name} ({channel_info['channel_name']})")
            
            episodes = self.process_channel_directory(channel_dir, channel_info)
            all_processed.extend(episodes)
            
            # 儲存個別頻道資料
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, f"{channel_name}_processed.json")
                self.save_processed_data(episodes, output_file)
        
        # 儲存所有資料
        if output_dir:
            all_output_file = os.path.join(output_dir, "all_episodes_processed.json")
            self.save_processed_data(all_processed, all_output_file)
        
        # 插入資料庫
        if insert_db:
            self.insert_to_database(all_processed)
        
        return all_processed


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='Episodes 資料處理工具')
    parser.add_argument('--episodes-dir', type=str, default='episodes', help='episodes 目錄路徑')
    parser.add_argument('--output-dir', type=str, help='輸出目錄')
    parser.add_argument('--insert-db', action='store_true', help='插入資料庫')
    parser.add_argument('--channel', type=str, choices=['business', 'evucation', 'all'], default='all', help='指定頻道')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細輸出')
    
    args = parser.parse_args()
    
    # 設定日誌
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    processor = EpisodeProcessor()
    
    if args.channel == 'all':
        # 處理所有頻道
        processor.process_all_channels(args.episodes_dir, args.output_dir, args.insert_db)
    else:
        # 處理指定頻道
        channel_info = processor.channel_mapping.get(args.channel)
        if not channel_info:
            print(f"未知頻道: {args.channel}")
            return
        
        channel_dir = os.path.join(args.episodes_dir, args.channel)
        episodes = processor.process_channel_directory(channel_dir, channel_info)
        
        if args.output_dir:
            os.makedirs(args.output_dir, exist_ok=True)
            output_file = os.path.join(args.output_dir, f"{args.channel}_processed.json")
            processor.save_processed_data(episodes, output_file)
        
        if args.insert_db:
            processor.insert_to_database(episodes)


if __name__ == "__main__":
    main() 