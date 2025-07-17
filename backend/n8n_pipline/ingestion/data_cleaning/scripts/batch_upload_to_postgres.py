#!/usr/bin/env python3
"""
批次上傳 batch_input 資料夾中的所有 JSON 檔案到 PostgreSQL
支援 RSS 和 Podcast 格式的 JSON 檔案
"""

import os
import sys
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import traceback

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BatchPostgreSQLUploader:
    """批次 PostgreSQL 資料上傳類別"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化資料庫連接
        
        Args:
            config: 資料庫配置
        """
        self.config = config
        self.conn = None
        self._connect()
        self._ensure_tables_exist()
    
    def _connect(self):
        """建立資料庫連接"""
        try:
            self.conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            self.conn.autocommit = False
            logger.info("PostgreSQL 連接成功")
            
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            raise
    
    def _ensure_tables_exist(self):
        """確保必要的表格存在"""
        try:
            with self.conn.cursor() as cursor:
                # 檢查 episodes 表格是否存在
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'episodes'
                    );
                """)
                
                if not cursor.fetchone()[0]:
                    logger.info("建立 episodes 表格...")
                    cursor.execute("""
                        CREATE TABLE episodes (
                            episode_id SERIAL PRIMARY KEY,
                            podcast_id INTEGER NOT NULL,
                            episode_title VARCHAR(255) NOT NULL,
                            published_date DATE,
                            audio_url VARCHAR(512),
                            duration INTEGER,
                            description TEXT,
                            audio_preview_url VARCHAR(512),
                            languages VARCHAR(64),
                            explicit BOOLEAN,
                            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            apple_episodes_ranking INTEGER
                        );
                    """)
                    
                    # 建立索引
                    cursor.execute("""
                        CREATE INDEX idx_episodes_podcast_id ON episodes(podcast_id);
                        CREATE INDEX idx_episodes_published_date ON episodes(published_date);
                    """)
                    
                    logger.info("episodes 表格建立完成")
                
                # 檢查 podcasts 表格是否存在
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'podcasts'
                    );
                """)
                
                if not cursor.fetchone()[0]:
                    logger.info("建立 podcasts 表格...")
                    cursor.execute("""
                        CREATE TABLE podcasts (
                            podcast_id INTEGER PRIMARY KEY,
                            name VARCHAR(255) NOT NULL,
                            description TEXT,
                            author VARCHAR(255),
                            rss_link VARCHAR(512) UNIQUE,
                            images_640 VARCHAR(512),
                            images_300 VARCHAR(512),
                            images_64 VARCHAR(512),
                            languages VARCHAR(64),
                            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            apple_podcasts_ranking INTEGER,
                            apple_rating DECIMAL(3,2),
                            category VARCHAR(64),
                            update_frequency VARCHAR(64)
                        );
                    """)
                    
                    logger.info("podcasts 表格建立完成")
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"表格建立失敗: {e}")
            self.conn.rollback()
            raise
    
    def insert_podcast(self, podcast_data: Dict[str, Any]) -> int:
        """插入 Podcast 資料
        
        Args:
            podcast_data: Podcast 資料
            
        Returns:
            podcast_id: 插入的 Podcast ID
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO podcasts (
                        podcast_id, name, description, author, rss_link, 
                        languages, category, created_at, updated_at,
                        apple_rating, update_frequency
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (podcast_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        author = EXCLUDED.author,
                        rss_link = EXCLUDED.rss_link,
                        languages = EXCLUDED.languages,
                        category = EXCLUDED.category,
                        apple_rating = EXCLUDED.apple_rating,
                        update_frequency = EXCLUDED.update_frequency,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING podcast_id
                """, (
                    podcast_data.get('podcast_id'),
                    podcast_data.get('title', ''),
                    podcast_data.get('description', ''),
                    podcast_data.get('provider', ''),
                    podcast_data.get('rss_link', ''),
                    podcast_data.get('languages', 'zh-TW'),
                    podcast_data.get('category', ''),
                    datetime.now(),
                    datetime.now(),
                    self._extract_rating(podcast_data.get('rating', '')),
                    podcast_data.get('update_frequency', '')
                ))
                
                podcast_id = cursor.fetchone()[0]
                self.conn.commit()
                logger.info(f"Podcast 插入成功: {podcast_data.get('title', 'Unknown')} (ID: {podcast_id})")
                return podcast_id
                
        except Exception as e:
            logger.error(f"Podcast 插入失敗: {e}")
            self.conn.rollback()
            raise
    
    def _extract_rating(self, rating_str: str) -> Optional[float]:
        """從評分字串中提取數值"""
        if not rating_str:
            return None
        try:
            # 處理 "4.8（3.3萬則評分）" 格式
            rating = rating_str.split('（')[0]
            return float(rating)
        except:
            return None
    
    def insert_episode(self, episode_data: Dict[str, Any], podcast_id: int) -> int:
        """插入 Episode 資料
        
        Args:
            episode_data: Episode 資料
            podcast_id: 對應的 Podcast ID
            
        Returns:
            episode_id: 插入的 Episode ID
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO episodes (
                        podcast_id, episode_title, published_date, audio_url, 
                        duration, description, audio_preview_url, languages, 
                        explicit, created_at, updated_at, apple_episodes_ranking
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING episode_id
                """, (
                    podcast_id,
                    episode_data.get('title', ''),
                    self._parse_date(episode_data.get('published', '')),
                    episode_data.get('audio_url', ''),
                    episode_data.get('duration'),
                    episode_data.get('description', ''),
                    episode_data.get('audio_preview_url', ''),
                    episode_data.get('languages', 'zh-TW'),
                    episode_data.get('explicit', False),
                    datetime.now(),
                    datetime.now(),
                    episode_data.get('apple_episodes_ranking')
                ))
                
                episode_id = cursor.fetchone()[0]
                self.conn.commit()
                return episode_id
                
        except Exception as e:
            logger.error(f"Episode 插入失敗: {e}")
            self.conn.rollback()
            raise
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字串"""
        if not date_str:
            return None
        try:
            # 處理 "Wed, 02 Jul 2025 08:59:01 GMT" 格式
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str).date()
        except:
            try:
                # 嘗試其他格式
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except:
                return None
    
    def get_table_columns(self, table_name: str) -> Dict[str, dict]:
        """取得表格所有欄位資訊（型別、NOT NULL、預設值）"""
        columns = {}
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                for row in cursor.fetchall():
                    columns[row['column_name']] = {
                        'type': row['data_type'],
                        'not_null': row['is_nullable'] == 'NO',
                        'default': row['column_default']
                    }
        except Exception as e:
            logger.error(f"取得 {table_name} 欄位資訊失敗: {e}")
        return columns

    def get_primary_keys(self, table_name: str) -> List[str]:
        """取得主鍵欄位名稱"""
        keys = []
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT a.attname
                    FROM   pg_index i
                    JOIN   pg_attribute a ON a.attrelid = i.indrelid
                                         AND a.attnum = ANY(i.indkey)
                    WHERE  i.indrelid = %s::regclass
                    AND    i.indisprimary;
                """, (table_name,))
                keys = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"取得 {table_name} 主鍵失敗: {e}")
        return keys

    def convert_type(self, value, col_type):
        """根據型別自動轉換"""
        if value is None:
            return None
        try:
            if col_type in ('integer', 'bigint', 'smallint'):
                return int(value)
            elif col_type in ('double precision', 'real', 'numeric', 'decimal'):
                return float(value)
            elif col_type in ('boolean',):
                if isinstance(value, bool):
                    return value
                if str(value).lower() in ['true', '1', 't', 'yes', 'y']:
                    return True
                return False
            elif col_type in ('date',):
                if isinstance(value, datetime):
                    return value.date()
                from dateutil.parser import parse
                return parse(value).date()
            elif col_type in ('timestamp without time zone', 'timestamp with time zone'):
                if isinstance(value, datetime):
                    return value
                from dateutil.parser import parse
                return parse(value)
            else:
                return str(value)
        except Exception:
            return None

    def prepare_row(self, record: dict, columns: dict) -> dict:
        """根據欄位資訊動態產生插入資料"""
        row = {}
        for col, info in columns.items():
            if col in record:
                row[col] = self.convert_type(record[col], info['type'])
            elif info['default'] is not None:
                # 處理 serial, now(), 'NULL' 等預設值
                if info['default'].startswith('nextval') or info['default'] == 'NULL':
                    row[col] = None
                elif info['default'].startswith('now()'):
                    row[col] = datetime.now()
                else:
                    row[col] = info['default']
            else:
                row[col] = None
        return row

    def validate_row(self, row: dict, columns: dict, primary_keys: List[str]) -> Optional[str]:
        """檢查主鍵/NOT NULL 欄位"""
        for pk in primary_keys:
            if row.get(pk) is None:
                return f"缺少主鍵欄位: {pk}"
        for col, info in columns.items():
            if info['not_null'] and row.get(col) is None:
                return f"缺少 NOT NULL 欄位: {col}"
        return None

    def upsert_row(self, table: str, row: dict, primary_keys: List[str]):
        """執行 upsert"""
        cols = list(row.keys())
        values = [row[c] for c in cols]
        update_cols = [c for c in cols if c not in primary_keys]
        set_clause = ', '.join([f"{c}=EXCLUDED.{c}" for c in update_cols])
        conflict_clause = ', '.join(primary_keys)
        placeholders = ', '.join(['%s'] * len(cols))
        sql = f"""
            INSERT INTO {table} ({', '.join(cols)})
            VALUES ({placeholders})
            ON CONFLICT ({conflict_clause}) DO UPDATE SET {set_clause}
        """
        with self.conn.cursor() as cursor:
            cursor.execute(sql, values)
        self.conn.commit()

    def process_json_file(self, file_path: str, table: str) -> Dict[str, Any]:
        """通用處理 JSON 檔案，動態對應欄位並 upsert"""
        columns = self.get_table_columns(table)
        primary_keys = self.get_primary_keys(table)
        success, fail, errors = 0, 0, []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if table == 'episodes' and not isinstance(data, list):
                return {"success": False, "error": "episodes 檔案格式錯誤"}
            if table == 'podcasts' and not isinstance(data, dict):
                return {"success": False, "error": "podcasts 檔案格式錯誤"}
            records = data if isinstance(data, list) else [data]
            for idx, record in enumerate(records):
                try:
                    row = self.prepare_row(record, columns)
                    err = self.validate_row(row, columns, primary_keys)
                    if err:
                        fail += 1
                        errors.append({"index": idx, "reason": err, "data": record})
                        continue
                    self.upsert_row(table, row, primary_keys)
                    success += 1
                except Exception as e:
                    fail += 1
                    errors.append({"index": idx, "reason": str(e), "trace": traceback.format_exc(), "data": record})
            return {"success": True, "total": len(records), "success_count": success, "fail_count": fail, "errors": errors}
        except Exception as e:
            return {"success": False, "error": str(e), "trace": traceback.format_exc()}

    def process_rss_file(self, file_path: str) -> Dict[str, Any]:
        """處理 RSS 格式的 JSON 檔案
        
        Args:
            file_path: JSON 檔案路徑
            
        Returns:
            處理結果統計
        """
        try:
            logger.info(f"處理 RSS 檔案: {file_path}")
            
            # 從檔案名提取 podcast_id
            filename = Path(file_path).stem
            if filename.startswith('RSS_'):
                podcast_id = int(filename.split('_')[1])
            elif filename.startswith('Spotify_RSS_'):
                podcast_id = int(filename.split('_')[2])
            else:
                logger.error(f"無法從檔案名提取 podcast_id: {filename}")
                return {"success": False, "error": "無法提取 podcast_id"}
            
            # 讀取 JSON 檔案
            with open(file_path, 'r', encoding='utf-8') as f:
                episodes_data = json.load(f)
            
            if not isinstance(episodes_data, list):
                logger.error(f"RSS 檔案格式錯誤: {file_path}")
                return {"success": False, "error": "檔案格式錯誤"}
            
            # 插入 episodes
            success_count = 0
            for episode in episodes_data:
                try:
                    self.insert_episode(episode, podcast_id)
                    success_count += 1
                except Exception as e:
                    logger.error(f"插入 episode 失敗: {episode.get('title', 'Unknown')} - {e}")
            
            logger.info(f"RSS 檔案處理完成: {file_path}, 成功插入 {success_count}/{len(episodes_data)} 筆")
            return {
                "success": True,
                "total_episodes": len(episodes_data),
                "successful_inserts": success_count,
                "failed_inserts": len(episodes_data) - success_count
            }
            
        except Exception as e:
            logger.error(f"處理 RSS 檔案失敗: {file_path} - {e}")
            return {"success": False, "error": str(e)}
    
    def process_podcast_file(self, file_path: str) -> Dict[str, Any]:
        """處理 Podcast 格式的 JSON 檔案
        
        Args:
            file_path: JSON 檔案路徑
            
        Returns:
            處理結果統計
        """
        try:
            logger.info(f"處理 Podcast 檔案: {file_path}")
            
            # 從檔案名提取 podcast_id
            filename = Path(file_path).stem
            if filename.startswith('podcast_'):
                podcast_id = int(filename.split('_')[1])
            else:
                logger.error(f"無法從檔案名提取 podcast_id: {filename}")
                return {"success": False, "error": "無法提取 podcast_id"}
            
            # 讀取 JSON 檔案
            with open(file_path, 'r', encoding='utf-8') as f:
                podcast_data = json.load(f)
            
            if not isinstance(podcast_data, dict):
                logger.error(f"Podcast 檔案格式錯誤: {file_path}")
                return {"success": False, "error": "檔案格式錯誤"}
            
            # 添加 podcast_id
            podcast_data['podcast_id'] = podcast_id
            
            # 插入 podcast
            try:
                self.insert_podcast(podcast_data)
                logger.info(f"Podcast 檔案處理完成: {file_path}")
                return {
                    "success": True,
                    "podcast_inserted": True
                }
            except Exception as e:
                logger.error(f"插入 podcast 失敗: {e}")
                return {"success": False, "error": str(e)}
            
        except Exception as e:
            logger.error(f"處理 Podcast 檔案失敗: {file_path} - {e}")
            return {"success": False, "error": str(e)}
    
    def process_batch_input_folder(self, input_folder: str) -> Dict[str, Any]:
        logger.info(f"開始處理資料夾: {input_folder}")
        if not os.path.exists(input_folder):
            logger.error(f"資料夾不存在: {input_folder}")
            return {"success": False, "error": "資料夾不存在"}
        json_files = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.endswith('.json')]
        logger.info(f"找到 {len(json_files)} 個 JSON 檔案")
        summary = []
        for file_path in json_files:
            filename = Path(file_path).name
            if filename.startswith('RSS_') or filename.startswith('Spotify_RSS_'):
                table = 'episodes'
            elif filename.startswith('podcast_'):
                table = 'podcasts'
            else:
                logger.warning(f"跳過未知格式檔案: {filename}")
                continue
            logger.info(f"處理檔案: {filename} -> {table}")
            result = self.process_json_file(file_path, table)
            summary.append({"file": filename, **result})
            if not result.get('success'):
                logger.error(f"處理失敗: {filename} - {result.get('error')}\n{result.get('trace', '')}")
        return summary
    
    def close(self):
        """關閉資料庫連接"""
        if self.conn:
            self.conn.close()
            logger.info("資料庫連接已關閉")

def main():
    """主程式"""
    logger.info("=== 批次上傳 batch_input 資料夾到 PostgreSQL ===")
    
    # 資料庫配置 - 使用正確的 PostgreSQL 服務地址
    config = {
        'host': os.getenv('POSTGRES_HOST', 'postgres.podwise.svc.cluster.local'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'podcast'),
        'user': os.getenv('POSTGRES_USER', 'bdse37'),
        'password': os.getenv('POSTGRES_PASSWORD', '111111')
    }
    
    # 輸入資料夾路徑
    input_folder = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'batch_input'
    )
    
    try:
        # 建立上傳器
        uploader = BatchPostgreSQLUploader(config)
        
        # 處理批次資料
        summary = uploader.process_batch_input_folder(input_folder)
        
        print("\n=== 匯入結果總結 ===")
        for item in summary:
            print(f"檔案: {item['file']} | 成功: {item.get('success_count', 0)} | 失敗: {item.get('fail_count', 0)}")
            if item.get('errors'):
                print(f"  失敗明細: {item['errors']}")
        print("\n🎉 批次上傳結束！")
        
        uploader.close()
        
    except Exception as e:
        logger.error(f"批次上傳執行失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 