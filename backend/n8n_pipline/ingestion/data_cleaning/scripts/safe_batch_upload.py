#!/usr/bin/env python3
"""
安全的批次上傳腳本
確保 JSON 資料正確對應到 PostgreSQL 欄位，並避免重複插入
使用 UPSERT 操作和詳細的錯誤處理
"""

import os
import sys
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import traceback

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SafeBatchUploader:
    """安全的批次上傳類別"""
    
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
                        CREATE UNIQUE INDEX idx_episodes_podcast_title ON episodes(podcast_id, episode_title);
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
    
    def get_table_columns(self, table_name: str) -> Dict[str, dict]:
        """獲取表格欄位資訊"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    ORDER BY ordinal_position
                """, (table_name,))
                
                columns = {}
                for row in cursor.fetchall():
                    columns[row[0]] = {
                        'type': row[1],
                        'nullable': row[2] == 'YES',
                        'default': row[3]
                    }
                return columns
                
        except Exception as e:
            logger.error(f"獲取表格欄位失敗: {e}")
            raise
    
    def safe_insert_podcast(self, podcast_data: Dict[str, Any]) -> Dict[str, Any]:
        """安全插入 Podcast 資料，使用 UPSERT
        
        Args:
            podcast_data: Podcast 資料
            
        Returns:
            插入結果
        """
        try:
            # 從檔案名提取 podcast_id
            filename = Path(podcast_data.get('_file_path', '')).stem
            if filename.startswith('podcast_'):
                podcast_id = int(filename.split('_')[1])
            else:
                podcast_id = podcast_data.get('id')
            
            if not podcast_id:
                return {
                    'success': False,
                    'error': '無法提取 podcast_id',
                    'data': podcast_data
                }
            
            # 準備插入資料
            insert_data = {
                'podcast_id': int(podcast_id),
                'name': podcast_data.get('title', ''),
                'description': podcast_data.get('description', ''),
                'author': podcast_data.get('provider', ''),
                'rss_link': podcast_data.get('url', ''),
                'languages': 'zh-TW',
                'category': podcast_data.get('category', ''),
                'apple_rating': self._extract_rating(podcast_data.get('rating', '')),
                'update_frequency': podcast_data.get('update_frequency', ''),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO podcasts (
                        podcast_id, name, description, author, rss_link, 
                        languages, category, apple_rating, update_frequency,
                        created_at, updated_at
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
                    insert_data['podcast_id'],
                    insert_data['name'],
                    insert_data['description'],
                    insert_data['author'],
                    insert_data['rss_link'],
                    insert_data['languages'],
                    insert_data['category'],
                    insert_data['apple_rating'],
                    insert_data['update_frequency'],
                    insert_data['created_at'],
                    insert_data['updated_at']
                ))
                
                result_id = cursor.fetchone()[0]
                self.conn.commit()
                
                return {
                    'success': True,
                    'podcast_id': result_id,
                    'action': 'inserted' if result_id == insert_data['podcast_id'] else 'updated',
                    'data': insert_data
                }
                
        except Exception as e:
            logger.error(f"Podcast 插入失敗: {e}")
            self.conn.rollback()
            return {
                'success': False,
                'error': str(e),
                'data': podcast_data
            }
    
    def safe_insert_episodes(self, episodes_data: List[Dict[str, Any]], podcast_id: int) -> Dict[str, Any]:
        """安全插入 Episodes 資料，使用 UPSERT
        
        Args:
            episodes_data: Episodes 資料列表
            podcast_id: Podcast ID
            
        Returns:
            插入結果統計
        """
        try:
            results = {
                'total': len(episodes_data),
                'inserted': 0,
                'updated': 0,
                'skipped': 0,
                'errors': []
            }
            
            for idx, episode in enumerate(episodes_data):
                try:
                    # 準備插入資料
                    insert_data = {
                        'podcast_id': podcast_id,
                        'episode_title': episode.get('title', ''),
                        'published_date': self._parse_date(episode.get('published_date')),
                        'audio_url': episode.get('audio_url', ''),
                        'duration': episode.get('duration'),
                        'description': episode.get('description', ''),
                        'audio_preview_url': episode.get('audio_preview_url', ''),
                        'languages': episode.get('languages', 'zh-TW'),
                        'explicit': episode.get('explicit', False),
                        'apple_episodes_ranking': episode.get('apple_episodes_ranking'),
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    # 檢查必要欄位
                    if not insert_data['episode_title']:
                        results['skipped'] += 1
                        results['errors'].append({
                            'index': idx,
                            'error': '缺少 episode_title',
                            'data': episode
                        })
                        continue
                    
                    with self.conn.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO episodes (
                                podcast_id, episode_title, published_date, audio_url,
                                duration, description, audio_preview_url, languages,
                                explicit, apple_episodes_ranking, created_at, updated_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (podcast_id, episode_title) DO UPDATE SET
                                published_date = EXCLUDED.published_date,
                                audio_url = EXCLUDED.audio_url,
                                duration = EXCLUDED.duration,
                                description = EXCLUDED.description,
                                audio_preview_url = EXCLUDED.audio_preview_url,
                                languages = EXCLUDED.languages,
                                explicit = EXCLUDED.explicit,
                                apple_episodes_ranking = EXCLUDED.apple_episodes_ranking,
                                updated_at = CURRENT_TIMESTAMP
                            RETURNING episode_id, (xmax = 0) as is_insert
                        """, (
                            insert_data['podcast_id'],
                            insert_data['episode_title'],
                            insert_data['published_date'],
                            insert_data['audio_url'],
                            insert_data['duration'],
                            insert_data['description'],
                            insert_data['audio_preview_url'],
                            insert_data['languages'],
                            insert_data['explicit'],
                            insert_data['apple_episodes_ranking'],
                            insert_data['created_at'],
                            insert_data['updated_at']
                        ))
                        
                        row = cursor.fetchone()
                        if row[1]:  # is_insert
                            results['inserted'] += 1
                        else:
                            results['updated'] += 1
                    
                except Exception as e:
                    results['errors'].append({
                        'index': idx,
                        'error': str(e),
                        'data': episode
                    })
                    logger.error(f"Episode 插入失敗 (索引 {idx}): {e}")
            
            self.conn.commit()
            return results
            
        except Exception as e:
            logger.error(f"Episodes 批次插入失敗: {e}")
            self.conn.rollback()
            return {
                'total': len(episodes_data),
                'inserted': 0,
                'updated': 0,
                'skipped': 0,
                'errors': [{'error': str(e)}]
            }
    
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
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字串"""
        if not date_str:
            return None
        try:
            # 嘗試多種日期格式
            formats = [
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%d/%m/%Y',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%SZ'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            return None
        except:
            return None
    
    def process_podcast_file(self, file_path: str) -> Dict[str, Any]:
        """處理 Podcast 檔案
        
        Args:
            file_path: JSON 檔案路徑
            
        Returns:
            處理結果
        """
        try:
            logger.info(f"處理 Podcast 檔案: {file_path}")
            
            # 讀取 JSON 檔案
            with open(file_path, 'r', encoding='utf-8') as f:
                podcast_data = json.load(f)
            
            # 添加檔案路徑資訊
            podcast_data['_file_path'] = file_path
            
            # 插入 podcast
            result = self.safe_insert_podcast(podcast_data)
            
            if result['success']:
                logger.info(f"Podcast 處理成功: {Path(file_path).name} (ID: {result['podcast_id']})")
            else:
                logger.error(f"Podcast 處理失敗: {Path(file_path).name} - {result['error']}")
            
            return result
            
        except Exception as e:
            logger.error(f"處理 Podcast 檔案失敗: {file_path} - {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }
    
    def process_rss_file(self, file_path: str) -> Dict[str, Any]:
        """處理 RSS 檔案
        
        Args:
            file_path: JSON 檔案路徑
            
        Returns:
            處理結果
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
                return {
                    'success': False,
                    'error': f'無法從檔案名提取 podcast_id: {filename}',
                    'file_path': file_path
                }
            
            # 讀取 JSON 檔案
            with open(file_path, 'r', encoding='utf-8') as f:
                episodes_data = json.load(f)
            
            if not isinstance(episodes_data, list):
                return {
                    'success': False,
                    'error': 'RSS 檔案格式錯誤，應該是陣列格式',
                    'file_path': file_path
                }
            
            # 插入 episodes
            result = self.safe_insert_episodes(episodes_data, podcast_id)
            
            logger.info(f"RSS 檔案處理完成: {Path(file_path).name}")
            logger.info(f"  總計: {result['total']}, 新增: {result['inserted']}, 更新: {result['updated']}, 跳過: {result['skipped']}")
            
            if result['errors']:
                logger.warning(f"  錯誤數量: {len(result['errors'])}")
            
            return {
                'success': True,
                'podcast_id': podcast_id,
                'episodes_result': result,
                'file_path': file_path
            }
            
        except Exception as e:
            logger.error(f"處理 RSS 檔案失敗: {file_path} - {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }
    
    def process_batch_input_folder(self, input_folder: str) -> Dict[str, Any]:
        """處理整個 batch_input 資料夾
        
        Args:
            input_folder: 輸入資料夾路徑
            
        Returns:
            處理結果摘要
        """
        logger.info(f"開始處理資料夾: {input_folder}")
        
        if not os.path.exists(input_folder):
            return {"error": "資料夾不存在"}
        
        json_files = [f for f in os.listdir(input_folder) if f.endswith('.json')]
        logger.info(f"找到 {len(json_files)} 個 JSON 檔案")
        
        results = {
            'podcasts': [],
            'rss_files': [],
            'summary': {
                'total_files': len(json_files),
                'podcast_files': 0,
                'rss_files': 0,
                'successful_podcasts': 0,
                'successful_rss': 0,
                'failed_files': 0
            }
        }
        
        for filename in json_files:
            file_path = os.path.join(input_folder, filename)
            
            if filename.startswith('podcast_'):
                result = self.process_podcast_file(file_path)
                results['podcasts'].append(result)
                results['summary']['podcast_files'] += 1
                
                if result.get('success'):
                    results['summary']['successful_podcasts'] += 1
                else:
                    results['summary']['failed_files'] += 1
                    
            elif filename.startswith('RSS_') or filename.startswith('Spotify_RSS_'):
                result = self.process_rss_file(file_path)
                results['rss_files'].append(result)
                results['summary']['rss_files'] += 1
                
                if result.get('success'):
                    results['summary']['successful_rss'] += 1
                else:
                    results['summary']['failed_files'] += 1
            else:
                logger.warning(f"跳過未知格式檔案: {filename}")
        
        return results
    
    def generate_summary_report(self, results: Dict[str, Any]) -> str:
        """生成摘要報告"""
        summary = results.get('summary', {})
        
        report = []
        report.append("=" * 60)
        report.append("批次上傳摘要報告")
        report.append("=" * 60)
        
        report.append(f"\n📊 檔案處理統計:")
        report.append(f"   - 總檔案數: {summary.get('total_files', 0)}")
        report.append(f"   - Podcast 檔案: {summary.get('podcast_files', 0)}")
        report.append(f"   - RSS 檔案: {summary.get('rss_files', 0)}")
        report.append(f"   - 成功處理: {summary.get('successful_podcasts', 0) + summary.get('successful_rss', 0)}")
        report.append(f"   - 處理失敗: {summary.get('failed_files', 0)}")
        
        # Podcast 處理結果
        if results.get('podcasts'):
            report.append(f"\n🎙️ Podcast 處理結果:")
            for podcast in results['podcasts']:
                filename = Path(podcast.get('file_path', '')).name
                if podcast.get('success'):
                    report.append(f"   ✅ {filename}: {podcast.get('action', 'processed')}")
                else:
                    report.append(f"   ❌ {filename}: {podcast.get('error', 'unknown error')}")
        
        # RSS 處理結果
        if results.get('rss_files'):
            report.append(f"\n📻 RSS 處理結果:")
            for rss in results['rss_files']:
                filename = Path(rss.get('file_path', '')).name
                if rss.get('success'):
                    episodes_result = rss.get('episodes_result', {})
                    report.append(f"   ✅ {filename}: {episodes_result.get('inserted', 0)} 新增, {episodes_result.get('updated', 0)} 更新")
                else:
                    report.append(f"   ❌ {filename}: {rss.get('error', 'unknown error')}")
        
        report.append("\n" + "=" * 60)
        return "\n".join(report)
    
    def close(self):
        """關閉資料庫連接"""
        if self.conn:
            self.conn.close()
            logger.info("資料庫連接已關閉")

def main():
    """主程式"""
    logger.info("=== 安全批次上傳 batch_input 資料夾到 PostgreSQL ===")
    
    # 資料庫配置
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
        uploader = SafeBatchUploader(config)
        
        # 處理批次資料
        results = uploader.process_batch_input_folder(input_folder)
        
        # 生成報告
        report = uploader.generate_summary_report(results)
        print(report)
        
        # 儲存報告到檔案
        report_file = os.path.join(os.path.dirname(input_folder), 'safe_upload_report.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"上傳報告已儲存到: {report_file}")
        
        # 關閉連接
        uploader.close()
        
        # 檢查是否有錯誤
        if results.get('summary', {}).get('failed_files', 0) > 0:
            logger.warning("部分檔案處理失敗，請檢查報告")
            sys.exit(1)
        else:
            logger.info("所有檔案處理完成")
        
    except Exception as e:
        logger.error(f"批次上傳失敗: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 