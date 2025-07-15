#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批次資料補齊處理腳本
從 stage3_tagging 讀取檔案，補齊必要欄位後輸出到 stage4_embedding_prep
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

import psycopg2
from psycopg2.extras import RealDictCursor

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_complete_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataCompleter:
    """資料補齊器 - 從 PostgreSQL 補齊必要欄位"""
    
    def __init__(self):
        """初始化資料補齊器"""
        self.db_config = {
            "host": os.getenv("POSTGRES_HOST", "10.233.50.117"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "podcast"),
            "user": os.getenv("POSTGRES_USER", "bdse37"),
            "password": os.getenv("POSTGRES_PASSWORD", "111111")
        }
        
        # 預設 podcast 名稱快取
        self.podcast_name_cache = {
            "1488295306": "早晨財經速解讀",
            "1500839292": "股癌",
            "1531106786": "台幣漲夠了嗎",
            "1533645986": "熱議華爾街",
            "1536242998": "吳淡如",
            "1590806478": "台幣收關",
            "1626274583": "創作歌手",
            "1707757888": "財經M平方",
            "1776077547": "FIREMAN",
            "1816898458": "V轉投資",
            "1452688611": "工作中那些事",
            "1488718553": "幸福翹翹板",
            "1500162537": "哇賽心觀點",
            "1513786617": "拿錢換快樂",
            "1545511347": "丁學文的財經世界",
            "1567737523": "生活英語通",
            "1693352123": "古典詩詞",
            "262026947": "Climate Change"
        }
        
        # 預設 TAGS 快取
        self.podcast_tags_cache = {
            "1488295306": ["財經分析", "投資理財", "股市趨勢", "經濟政策"],
            "1500839292": ["投資理財", "股票分析", "經濟分析", "財務規劃"],
            "1531106786": ["財經分析", "台幣匯率", "台積電", "投資策略"],
            "1533645986": ["區塊鏈", "加密貨幣", "穩定幣", "金融科技"],
            "1536242998": ["個人成長", "職涯發展", "學習方法", "自我提升"],
            "1590806478": ["財經分析", "台幣匯率", "投資策略", "市場趨勢"],
            "1626274583": ["音樂創作", "職涯發展", "創業故事", "藝術文化"],
            "1707757888": ["財經分析", "投資理財", "職涯轉換", "跨領域學習"],
            "1776077547": ["投資理財", "FIRE理財", "財務規劃", "理財教育"],
            "1816898458": ["投資理財", "財經分析", "投資策略", "市場分析"],
            "1452688611": ["職涯發展", "工作心態", "職場技能", "個人成長"],
            "1488718553": ["教育理念", "體制外教育", "學習方法", "教育創新"],
            "1500162537": ["投資理財", "理財觀念", "生活態度", "財務規劃"],
            "1513786617": ["心理學", "快樂哲學", "人生觀", "自我提升"],
            "1545511347": ["國際財經", "經濟分析", "全球趨勢", "財經新聞"],
            "1567737523": ["英語學習", "語言教育", "生活英語", "教育內容"],
            "1693352123": ["古典文學", "詩詞欣賞", "文化教育", "文學藝術"],
            "262026947": ["氣候變遷", "環境議題", "心理健康", "社會議題"]
        }
    
    def get_db_connection(self):
        """獲取資料庫連接"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            return None
    
    def get_episode_data_from_db(self, podcast_id: str, episode_title: str) -> Optional[Dict[str, Any]]:
        """從資料庫獲取 episode 資料"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return None
            
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 使用 JOIN 查詢 episode 和 podcast 資料
                query = """
                SELECT 
                    e.podcast_id, e.episode_title, p.podcast_name, 
                    e.audio_url, p.images_300 as image_url, p.category
                FROM episodes e
                JOIN podcasts p ON e.podcast_id = p.podcast_id
                WHERE e.podcast_id = %s 
                AND LOWER(REPLACE(e.episode_title, ' ', '')) = LOWER(REPLACE(%s, ' ', ''))
                LIMIT 1
                """
                
                cursor.execute(query, (podcast_id, episode_title))
                result = cursor.fetchone()
                
                if result:
                    return dict(result)
                
                return None
                
        except Exception as e:
            logger.error(f"查詢資料庫失敗: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def get_podcast_data_from_db(self, podcast_id: str) -> Optional[Dict[str, Any]]:
        """從資料庫獲取 podcast 資料"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return None
            
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                SELECT 
                    podcast_id, podcast_name, images_300 as image_url, category
                FROM podcasts 
                WHERE podcast_id = %s
                LIMIT 1
                """
                
                cursor.execute(query, (podcast_id,))
                result = cursor.fetchone()
                
                if result:
                    return dict(result)
                
                return None
                
        except Exception as e:
            logger.error(f"查詢 podcast 資料失敗: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def complete_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """補齊資料欄位"""
        try:
            # 複製原始資料
            completed_data = data.copy()
            
            # 從檔案名稱解析 podcast_id 和 episode_title
            filename = data.get('filename', '')
            if not filename:
                logger.warning("缺少 filename 欄位")
                return None
            
            # 解析檔案名稱格式：RSS_{podcast_id}_podcast_{episode_id}_{episode_title}.json
            parts = filename.replace('.json', '').split('_')
            if len(parts) < 4:
                logger.warning(f"檔案名稱格式錯誤: {filename}")
                return None
            
            podcast_id = parts[1]  # RSS_1488295306_podcast_1321_...
            episode_title = '_'.join(parts[4:])  # 剩餘部分作為 episode_title
            
            # 從資料庫獲取 episode 資料
            db_episode_data = self.get_episode_data_from_db(podcast_id, episode_title)
            
            # 如果沒有找到 episode 資料，嘗試獲取 podcast 資料
            if not db_episode_data:
                db_podcast_data = self.get_podcast_data_from_db(podcast_id)
            else:
                db_podcast_data = None
            
            # 補齊必要欄位
            completed_data.update({
                'podcast_id': podcast_id,
                'episode_id': parts[3] if len(parts) > 3 else 'unknown',
                'episode_title': episode_title,
                'podcast_name': (db_episode_data.get('podcast_name') if db_episode_data 
                               else db_podcast_data.get('podcast_name') if db_podcast_data
                               else self.podcast_name_cache.get(podcast_id, f"Podcast_{podcast_id}")),
                'audio_url': (db_episode_data.get('audio_url') if db_episode_data 
                            else f"http://192.168.32.66:30090/business-one-min-audio/RSS_{podcast_id}_{episode_title}.mp3"),
                'image_url': (db_episode_data.get('image_url') if db_episode_data 
                            else db_podcast_data.get('image_url') if db_podcast_data
                            else f"http://192.168.32.66:30090/podcast-images/RSS_{podcast_id}.jpg"),
                'category': (db_episode_data.get('category') if db_episode_data 
                           else db_podcast_data.get('category') if db_podcast_data
                           else 'business'),
                'rss_id': f"RSS_{podcast_id}",
                'tags': (db_episode_data.get('tags') if db_episode_data 
                        else self.podcast_tags_cache.get(podcast_id, []))
            })
            
            # 確保 tags 是列表格式
            if isinstance(completed_data['tags'], str):
                completed_data['tags'] = [completed_data['tags']]
            elif not isinstance(completed_data['tags'], list):
                completed_data['tags'] = []
            
            # 確保其他欄位型態正確
            completed_data['chunk_id'] = str(completed_data.get('chunk_id', ''))
            completed_data['chunk_index'] = int(completed_data.get('chunk_index', 0))
            completed_data['start_time'] = float(completed_data.get('start_time', 0.0))
            completed_data['end_time'] = float(completed_data.get('end_time', 0.0))
            completed_data['duration'] = float(completed_data.get('duration', 0.0))
            
            # 處理 content 欄位 - 優先使用 chunk_text
            content = completed_data.get('content', '')
            if not content and 'chunk_text' in completed_data:
                content = completed_data['chunk_text']
            completed_data['content'] = str(content).strip()
            
            # 確保所有必要欄位都有值
            required_fields = [
                'chunk_id', 'podcast_id', 'episode_id', 'episode_title',
                'podcast_name', 'content', 'tags', 'chunk_index',
                'start_time', 'end_time', 'duration', 'audio_url',
                'image_url', 'rss_id', 'category'
            ]
            
            for field in required_fields:
                if field not in completed_data or completed_data[field] is None:
                    # 為缺失的欄位提供預設值
                    if field == 'chunk_id':
                        completed_data[field] = str(completed_data.get('chunk_id', ''))
                    elif field == 'podcast_id':
                        completed_data[field] = podcast_id
                    elif field == 'episode_id':
                        completed_data[field] = parts[3] if len(parts) > 3 else 'unknown'
                    elif field == 'episode_title':
                        completed_data[field] = episode_title
                    elif field == 'podcast_name':
                        completed_data[field] = self.podcast_name_cache.get(podcast_id, f"Podcast_{podcast_id}")
                    elif field == 'content':
                        completed_data[field] = str(completed_data.get('chunk_text', '')).strip()
                    elif field == 'tags':
                        completed_data[field] = self.podcast_tags_cache.get(podcast_id, [])
                    elif field == 'chunk_index':
                        completed_data[field] = int(completed_data.get('chunk_index', 0))
                    elif field == 'start_time':
                        completed_data[field] = float(completed_data.get('start_time', 0.0))
                    elif field == 'end_time':
                        completed_data[field] = float(completed_data.get('end_time', 0.0))
                    elif field == 'duration':
                        completed_data[field] = float(completed_data.get('duration', 0.0))
                    elif field == 'audio_url':
                        completed_data[field] = f"http://192.168.32.66:30090/business-one-min-audio/RSS_{podcast_id}_{episode_title}.mp3"
                    elif field == 'image_url':
                        completed_data[field] = f"http://192.168.32.66:30090/podcast-images/RSS_{podcast_id}.jpg"
                    elif field == 'rss_id':
                        completed_data[field] = f"RSS_{podcast_id}"
                    elif field == 'category':
                        completed_data[field] = 'business'
            
            return completed_data
            
        except Exception as e:
            logger.error(f"資料補齊失敗: {e}")
            return None


class BatchDataCompleter:
    """批次資料補齊處理器"""
    
    def __init__(self):
        """初始化批次處理器"""
        self.data_completer = DataCompleter()
        self.stage3_dir = Path("backend/vector_pipeline/data/stage3_tagging")
        self.stage4_dir = Path("backend/vector_pipeline/data/stage4_embedding_prep")
        
        # 確保輸出目錄存在
        self.stage4_dir.mkdir(parents=True, exist_ok=True)
        
        # 統計資訊
        self.stats = {
            "total_files": 0,
            "processed_files": 0,
            "success_files": 0,
            "error_files": 0,
            "skipped_files": 0,
            "error_details": []  # 記錄詳細錯誤資訊
        }
    
    def get_all_json_files(self) -> List[Path]:
        """獲取所有需要處理的 JSON 檔案"""
        json_files = []
        
        if not self.stage3_dir.exists():
            logger.error(f"目錄不存在: {self.stage3_dir}")
            return json_files
        
        # 遍歷所有子目錄
        for rss_dir in self.stage3_dir.iterdir():
            if not rss_dir.is_dir():
                continue
            
            logger.info(f"掃描目錄: {rss_dir.name}")
            
            # 獲取該目錄下的所有 JSON 檔案
            for json_file in rss_dir.glob("*.json"):
                json_files.append(json_file)
        
        logger.info(f"找到 {len(json_files)} 個 JSON 檔案")
        return json_files
    
    def process_single_file(self, json_file: Path) -> bool:
        """處理單個檔案"""
        try:
            logger.info(f"處理檔案: {json_file}")
            
            # 讀取原始資料
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 檢查是否有 chunks 欄位
            if 'chunks' not in data or not data['chunks']:
                logger.warning(f"檔案沒有 chunks 欄位或為空: {json_file}")
                return False
            
            # 處理每個 chunk
            completed_chunks = []
            for chunk in data['chunks']:
                # 將 chunk 資料與檔案級別的資料合併
                chunk_data = {
                    **chunk,
                    'filename': data.get('filename', ''),
                    'episode_id': data.get('episode_id', ''),
                    'collection_name': data.get('collection_name', ''),
                    'total_chunks': data.get('total_chunks', 0)
                }
                
                # 補齊 chunk 資料
                completed_chunk = self.data_completer.complete_data(chunk_data)
                if completed_chunk:
                    completed_chunks.append(completed_chunk)
            
            if not completed_chunks:
                logger.warning(f"沒有成功補齊的 chunks: {json_file}")
                return False
            
            # 建立輸出目錄結構
            rss_dir_name = json_file.parent.name
            output_dir = self.stage4_dir / rss_dir_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 輸出補齊後的資料
            output_file = output_dir / json_file.name
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(completed_chunks, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 成功處理: {json_file.name} ({len(completed_chunks)} chunks)")
            return True
            
        except Exception as e:
            logger.error(f"❌ 處理失敗 {json_file}: {e}")
            return False
    
    def validate_completed_data(self, json_file: Path) -> Dict[str, Any]:
        """驗證補齊後的資料"""
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # 讀取補齊後的資料
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 檢查是否為陣列
            if not isinstance(data, list):
                result["errors"].append(f"資料不是陣列格式")
                result["valid"] = False
                return result
            
            if not data:
                result["errors"].append(f"資料陣列為空")
                result["valid"] = False
                return result
            
            # 檢查必要欄位
            required_fields = [
                'chunk_id', 'podcast_id', 'episode_id', 'episode_title',
                'podcast_name', 'content', 'tags', 'chunk_index',
                'start_time', 'end_time', 'duration', 'audio_url',
                'image_url', 'rss_id', 'category'
            ]
            
            # 檢查第一個 chunk 的欄位
            first_chunk = data[0]
            missing_fields = []
            for field in required_fields:
                if field not in first_chunk or first_chunk[field] is None:
                    missing_fields.append(field)
            
            if missing_fields:
                result["errors"].append(f"缺少欄位: {missing_fields}")
                result["valid"] = False
            
            # 檢查資料型態
            if not isinstance(first_chunk.get('tags', []), list):
                result["errors"].append(f"tags 欄位型態錯誤: {type(first_chunk.get('tags'))}")
                result["valid"] = False
            
            if not isinstance(first_chunk.get('content', ''), str) or len(first_chunk.get('content', '').strip()) == 0:
                result["errors"].append(f"content 欄位為空")
                result["valid"] = False
            
            # 檢查所有 chunks 都有 content
            empty_content_count = 0
            for chunk in data:
                if not isinstance(chunk.get('content', ''), str) or len(chunk.get('content', '').strip()) == 0:
                    empty_content_count += 1
            
            if empty_content_count > 0:
                result["warnings"].append(f"有 {empty_content_count} 個 chunks 的 content 欄位為空")
            
            return result
            
        except Exception as e:
            result["errors"].append(f"驗證過程發生錯誤: {e}")
            result["valid"] = False
            return result
    
    def run_batch_processing(self) -> None:
        """執行批次處理"""
        logger.info("🚀 開始批次資料補齊處理")
        
        # 獲取所有檔案
        json_files = self.get_all_json_files()
        self.stats["total_files"] = len(json_files)
        
        if not json_files:
            logger.warning("沒有找到需要處理的檔案")
            return
        
        # 批次處理
        for i, json_file in enumerate(json_files, 1):
            logger.info(f"進度: {i}/{len(json_files)} - {json_file.name}")
            
            try:
                # 檢查是否已經處理過
                rss_dir_name = json_file.parent.name
                output_file = self.stage4_dir / rss_dir_name / json_file.name
                
                if output_file.exists():
                    logger.info(f"檔案已存在，跳過: {json_file.name}")
                    self.stats["skipped_files"] += 1
                    continue
                
                # 處理檔案
                success = self.process_single_file(json_file)
                self.stats["processed_files"] += 1
                
                if success:
                    # 驗證處理結果
                    validation_result = self.validate_completed_data(output_file)
                    if validation_result["valid"]:
                        self.stats["success_files"] += 1
                        logger.info(f"✅ 驗證通過: {json_file.name}")
                    else:
                        self.stats["error_files"] += 1
                        error_info = {
                            "file": str(json_file),
                            "errors": validation_result["errors"],
                            "warnings": validation_result["warnings"]
                        }
                        self.stats["error_details"].append(error_info)
                        logger.error(f"❌ 驗證失敗: {json_file.name} - {validation_result['errors']}")
                else:
                    self.stats["error_files"] += 1
                    error_info = {
                        "file": str(json_file),
                        "errors": ["處理失敗"],
                        "warnings": []
                    }
                    self.stats["error_details"].append(error_info)
                
            except Exception as e:
                logger.error(f"處理檔案時發生錯誤 {json_file}: {e}")
                self.stats["error_files"] += 1
        
        # 輸出統計結果
        self.print_statistics()
    
    def print_statistics(self) -> None:
        """輸出統計結果"""
        logger.info("=" * 50)
        logger.info("📊 批次處理統計結果")
        logger.info("=" * 50)
        logger.info(f"總檔案數: {self.stats['total_files']}")
        logger.info(f"已處理檔案: {self.stats['processed_files']}")
        logger.info(f"成功處理: {self.stats['success_files']}")
        logger.info(f"處理失敗: {self.stats['error_files']}")
        logger.info(f"跳過檔案: {self.stats['skipped_files']}")
        
        if self.stats['total_files'] > 0:
            success_rate = (self.stats['success_files'] / self.stats['total_files']) * 100
            logger.info(f"成功率: {success_rate:.2f}%")
        
        # 記錄錯誤詳情到檔案
        if self.stats['error_details']:
            error_log_file = "batch_processing_errors.json"
            with open(error_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats['error_details'], f, ensure_ascii=False, indent=2)
            logger.info(f"錯誤詳情已記錄到: {error_log_file}")
            logger.info(f"錯誤檔案數量: {len(self.stats['error_details'])}")
        
        logger.info("=" * 50)


def main():
    """主函數"""
    try:
        # 初始化批次處理器
        batch_processor = BatchDataCompleter()
        
        # 執行批次處理
        batch_processor.run_batch_processing()
        
        logger.info("🎉 批次處理完成")
        
    except Exception as e:
        logger.error(f"批次處理失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 