#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
將 stage3_tagging 的 JSON 格式轉換為符合 Milvus 插入格式的資料結構
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MilvusDataConverter:
    """Milvus 資料轉換器"""
    
    def __init__(self):
        """初始化轉換器"""
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
        
        # 預設 podcast 作者快取
        self.podcast_author_cache = {
            "1488295306": "財經M平方",
            "1500839292": "謝孟恭",
            "1531106786": "財經M平方",
            "1533645986": "財經M平方",
            "1536242998": "吳淡如",
            "1590806478": "財經M平方",
            "1626274583": "謝孟恭",
            "1707757888": "財經M平方",
            "1776077547": "FIREMAN",
            "1816898458": "V轉投資",
            "1452688611": "謝孟恭",
            "1488718553": "謝孟恭",
            "1500162537": "謝孟恭",
            "1513786617": "謝孟恭",
            "1545511347": "丁學文",
            "1567737523": "謝孟恭",
            "1693352123": "謝孟恭",
            "262026947": "BBC Learning English"
        }
        
        # 預設 podcast 分類快取
        self.podcast_category_cache = {
            "1488295306": "business",
            "1500839292": "business",
            "1531106786": "business",
            "1533645986": "business",
            "1536242998": "business",
            "1590806478": "business",
            "1626274583": "business",
            "1707757888": "business",
            "1776077547": "business",
            "1816898458": "business",
            "1452688611": "education",
            "1488718553": "education",
            "1500162537": "education",
            "1513786617": "education",
            "1545511347": "education",
            "1567737523": "education",
            "1693352123": "education",
            "262026947": "education"
        }
    
    def get_db_connection(self):
        """獲取資料庫連接"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            return None
    
    def parse_filename(self, filename: str) -> Optional[Dict[str, str]]:
        """解析檔案名稱獲取 podcast_id 和 episode_title"""
        try:
            # 移除 .json 副檔名
            base_name = filename.replace('.json', '')
            
            # 解析格式：RSS_{podcast_id}_podcast_{episode_id}_{episode_title}
            if not base_name.startswith('RSS_'):
                logger.warning(f"檔案名稱格式錯誤，不是 RSS_ 開頭: {filename}")
                return None
            
            # 移除 "RSS_" 前綴
            base_name = base_name[4:]  # 移除 "RSS_"
            
            # 找到第一個下劃線後的位置（podcast_id）
            first_underscore = base_name.find('_')
            if first_underscore == -1:
                logger.warning(f"檔案名稱格式錯誤，找不到 podcast_id: {filename}")
                return None
            
            podcast_id = base_name[:first_underscore]
            
            # 找到最後一個下劃線的位置（episode_title 開始位置）
            last_underscore = base_name.rfind('_')
            if last_underscore == -1 or last_underscore <= first_underscore:
                logger.warning(f"檔案名稱格式錯誤，找不到 episode_title: {filename}")
                return None
            
            episode_title = base_name[last_underscore + 1:]  # 最後一個_之後的部分
            
            return {
                'podcast_id': podcast_id,
                'episode_title': episode_title
            }
            
        except Exception as e:
            logger.error(f"解析檔案名稱失敗: {e}")
            return None

    def get_podcast_metadata_from_db(self, podcast_id: str) -> Optional[Dict[str, Any]]:
        """從資料庫獲取 podcast 完整元資料"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return None
            
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                SELECT 
                    podcast_id,
                    podcast_name,
                    author,
                    category,
                    apple_rating,
                    rss_link,
                    languages,
                    created_at,
                    updated_at
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

    def get_episode_metadata_from_db(self, podcast_id: str, episode_title: str) -> Optional[Dict[str, Any]]:
        """從資料庫獲取 episode 完整元資料，使用模糊比對"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return None
            
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 使用模糊比對查詢 episode
                query = """
                SELECT 
                    e.episode_id,
                    e.podcast_id,
                    e.episode_title,
                    e.published_date,
                    e.duration,
                    e.description,
                    e.created_at,
                    p.podcast_name,
                    p.author,
                    p.category,
                    p.apple_rating,
                    p.rss_link,
                    p.languages
                FROM episodes e
                JOIN podcasts p ON e.podcast_id = p.podcast_id
                WHERE e.podcast_id = %s 
                AND e.episode_title ILIKE %s
                ORDER BY e.created_at DESC
                LIMIT 1
                """
                
                # 使用模糊比對，包含 episode_title
                search_pattern = f"%{episode_title}%"
                cursor.execute(query, (podcast_id, search_pattern))
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

    def convert_chunk_to_milvus_format(self, chunk: Dict[str, Any], episode_metadata: Optional[Dict[str, Any]] = None, podcast_metadata: Optional[Dict[str, Any]] = None, parsed_info: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """將單個 chunk 轉換為 Milvus 格式，確保所有欄位都有正確值"""
        try:
            # 從檔名解析的 podcast_id
            podcast_id = 0
            if parsed_info:
                podcast_id = int(parsed_info.get('podcast_id', '0'))
            
            # 基本欄位
            milvus_data = {
                'chunk_id': chunk.get('chunk_id', ''),
                'chunk_index': chunk.get('chunk_index', 0),
                'chunk_text': chunk.get('chunk_text', ''),
                'language': chunk.get('language', 'zh'),
                'created_at': chunk.get('created_at', datetime.now().isoformat()),
                'source_model': chunk.get('source_model', 'bge-m3'),
                'embedding': chunk.get('embedding', []),
                'podcast_id': podcast_id
            }
            
            # 處理 episode_id
            episode_id_str = chunk.get('episode_id', '')
            if episode_id_str:
                try:
                    if isinstance(episode_id_str, str) and len(episode_id_str) > 10:
                        episode_id = abs(hash(episode_id_str)) % (2**63)
                    else:
                        episode_id = int(episode_id_str)
                except (ValueError, TypeError):
                    episode_id = abs(hash(str(episode_id_str))) % (2**63)
            else:
                episode_id = 0
            milvus_data['episode_id'] = episode_id
            
            # 優先使用 episode_metadata，其次使用 podcast_metadata，最後使用快取
            if episode_metadata:
                # 使用 episode 查詢結果（包含 podcast 資訊）
                # 處理 Decimal 型態
                apple_rating = episode_metadata.get('apple_rating', 0)
                if hasattr(apple_rating, '__float__'):
                    apple_rating = float(apple_rating)
                else:
                    apple_rating = int(apple_rating) if apple_rating else 0
                
                # 處理 duration
                duration = episode_metadata.get('duration', '')
                if duration:
                    duration = str(duration)
                else:
                    duration = 'Unknown'
                
                # 處理 published_date
                published_date = episode_metadata.get('published_date', '')
                if published_date:
                    published_date = published_date.isoformat()
                else:
                    published_date = 'Unknown'
                
                milvus_data.update({
                    'podcast_name': episode_metadata.get('podcast_name', f"Podcast_{podcast_id}"),
                    'author': episode_metadata.get('author', 'Unknown'),
                    'category': episode_metadata.get('category', 'business'),
                    'episode_title': episode_metadata.get('episode_title', parsed_info.get('episode_title', '') if parsed_info else ''),
                    'duration': duration,
                    'published_date': published_date,
                    'apple_rating': apple_rating
                })
            elif podcast_metadata:
                # 使用 podcast 查詢結果
                # 處理 Decimal 型態
                apple_rating = podcast_metadata.get('apple_rating', 0)
                if hasattr(apple_rating, '__float__'):
                    apple_rating = float(apple_rating)
                else:
                    apple_rating = int(apple_rating) if apple_rating else 0
                
                milvus_data.update({
                    'podcast_name': podcast_metadata.get('podcast_name', f"Podcast_{podcast_id}"),
                    'author': podcast_metadata.get('author', 'Unknown'),
                    'category': podcast_metadata.get('category', 'business'),
                    'episode_title': parsed_info.get('episode_title', '') if parsed_info else '',
                    'duration': 'Unknown',
                    'published_date': 'Unknown',
                    'apple_rating': apple_rating
                })
            else:
                # 使用快取資料
                podcast_id_str = str(podcast_id)
                milvus_data.update({
                    'podcast_name': self.podcast_name_cache.get(podcast_id_str, f"Podcast_{podcast_id}"),
                    'author': self.podcast_author_cache.get(podcast_id_str, 'Unknown'),
                    'category': self.podcast_category_cache.get(podcast_id_str, 'business'),
                    'episode_title': parsed_info.get('episode_title', '') if parsed_info else '',
                    'duration': 'Unknown',
                    'published_date': 'Unknown',
                    'apple_rating': int(chunk.get('apple_rating', 0)) if chunk.get('apple_rating') else 0
                })
            
            # 處理 tags
            tags = chunk.get('enhanced_tags', [])
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except json.JSONDecodeError:
                    tags = []
            elif not isinstance(tags, list):
                tags = []
            milvus_data['tags'] = json.dumps(tags, ensure_ascii=False)
            
            return milvus_data
            
        except Exception as e:
            logger.error(f"轉換 chunk 失敗: {e}")
            return None

    def convert_file_to_milvus_format(self, file_path: Path) -> Optional[List[Dict[str, Any]]]:
        """將單個檔案轉換為 Milvus 格式"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            filename = data.get('filename', '')
            chunks = data.get('chunks', [])
            
            if not chunks:
                logger.warning(f"檔案 {filename} 沒有 chunks")
                return None
            
            # 解析檔案名稱
            parsed_info = self.parse_filename(filename)
            if not parsed_info:
                logger.warning(f"無法解析檔案名稱: {filename}")
                return None
            
            podcast_id = parsed_info['podcast_id']
            episode_title = parsed_info['episode_title']
            
            # 從資料庫獲取 episode 和 podcast 元資料
            episode_metadata = self.get_episode_metadata_from_db(podcast_id, episode_title)
            podcast_metadata = self.get_podcast_metadata_from_db(podcast_id)
            
            # 轉換所有 chunks，確保同一檔案內所有 chunks 的 episode_title、duration、published_date 都相同
            milvus_chunks = []
            for chunk in chunks:
                milvus_chunk = self.convert_chunk_to_milvus_format(chunk, episode_metadata, podcast_metadata, parsed_info)
                if milvus_chunk:
                    milvus_chunks.append(milvus_chunk)
            
            return milvus_chunks if milvus_chunks else None
            
        except Exception as e:
            logger.error(f"轉換檔案 {file_path} 失敗: {e}")
            return None
    
    def convert_stage3_to_milvus_format(self, stage3_dir: str = "data/stage3_tagging", 
                                      output_dir: str = "data/stage4_embedding_prep") -> Dict[str, Any]:
        """將 stage3_tagging 目錄下的所有檔案轉換為 Milvus 格式"""
        try:
            stage3_path = Path(stage3_dir)
            output_path = Path(output_dir)
            
            if not stage3_path.exists():
                return {"error": f"目錄不存在: {stage3_dir}"}
            
            # 確保輸出目錄存在
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 處理所有 JSON 檔案
            json_files = list(stage3_path.rglob("*.json"))
            
            total_files = len(json_files)
            successful_files = 0
            failed_files = 0
            total_chunks = 0
            failed_files_list = []
            
            logger.info(f"開始處理 {total_files} 個檔案...")
            
            for json_file in json_files:
                try:
                    logger.info(f"處理檔案: {json_file.name}")
                    
                    # 轉換檔案
                    milvus_chunks = self.convert_file_to_milvus_format(json_file)
                    
                    if milvus_chunks:
                        # 儲存轉換後的資料
                        output_file = output_path / f"{json_file.stem}_milvus.json"
                        
                        output_data = {
                            "filename": json_file.name,
                            "total_chunks": len(milvus_chunks),
                            "converted_at": datetime.now().isoformat(),
                            "chunks": milvus_chunks
                        }
                        
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(output_data, f, ensure_ascii=False, indent=2)
                        
                        successful_files += 1
                        total_chunks += len(milvus_chunks)
                        
                        logger.info(f"✅ 成功轉換 {json_file.name}: {len(milvus_chunks)} chunks")
                    else:
                        failed_files += 1
                        failed_files_list.append(str(json_file))
                        logger.warning(f"❌ 轉換失敗: {json_file.name}")
                    
                except Exception as e:
                    failed_files += 1
                    failed_files_list.append(str(json_file))
                    logger.error(f"處理檔案失敗 {json_file.name}: {e}")
            
            # 生成統計報告
            stats = {
                "total_files": total_files,
                "successful_files": successful_files,
                "failed_files": failed_files,
                "total_chunks": total_chunks,
                "success_rate": successful_files / total_files * 100 if total_files > 0 else 0,
                "failed_files_list": failed_files_list
            }
            
            # 儲存統計報告
            stats_file = output_path / "conversion_stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            
            logger.info(f"🎉 轉換完成！成功: {successful_files}/{total_files}, 總 chunks: {total_chunks}")
            return stats
            
        except Exception as e:
            logger.error(f"轉換過程失敗: {e}")
            return {"error": str(e)}


def main():
    """主函數"""
    try:
        converter = MilvusDataConverter()
        
        # 轉換 stage3_tagging 到 stage4_embedding_prep
        result = converter.convert_stage3_to_milvus_format()
        
        if "error" in result:
            logger.error(f"轉換失敗: {result['error']}")
            sys.exit(1)
        else:
            logger.info("✅ 轉換成功完成")
            print(f"統計結果: {result}")
            
    except Exception as e:
        logger.error(f"執行失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 