#!/usr/bin/env python3
"""
驗證上傳結果腳本
確認資料是否正確插入且沒有重複
"""

import os
import sys
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

class UploadResultVerifier:
    """上傳結果驗證類別"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化資料庫連接"""
        self.config = config
        self.conn = None
        self._connect()
    
    def _connect(self):
        """建立資料庫連接"""
        try:
            if self.conn:
                self.conn.close()
            
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
    
    def get_podcasts_summary(self) -> Dict[str, Any]:
        """獲取 Podcasts 表格摘要"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 總數
                cursor.execute("SELECT COUNT(*) as total FROM podcasts")
                total = cursor.fetchone()['total']
                
                # 最近新增的
                cursor.execute("""
                    SELECT COUNT(*) as recent_count 
                    FROM podcasts 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '1 day'
                """)
                recent_count = cursor.fetchone()['recent_count']
                
                # 分類統計
                cursor.execute("""
                    SELECT category, COUNT(*) as count 
                    FROM podcasts 
                    WHERE category IS NOT NULL 
                    GROUP BY category 
                    ORDER BY count DESC
                """)
                categories = cursor.fetchall()
                
                # 語言統計
                cursor.execute("""
                    SELECT languages, COUNT(*) as count 
                    FROM podcasts 
                    WHERE languages IS NOT NULL 
                    GROUP BY languages 
                    ORDER BY count DESC
                """)
                languages = cursor.fetchall()
                
                return {
                    'total': total,
                    'recent_count': recent_count,
                    'categories': categories,
                    'languages': languages
                }
                
        except Exception as e:
            logger.error(f"獲取 Podcasts 摘要失敗: {e}")
            return {}
    
    def get_episodes_summary(self) -> Dict[str, Any]:
        """獲取 Episodes 表格摘要"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 總數
                cursor.execute("SELECT COUNT(*) as total FROM episodes")
                total = cursor.fetchone()['total']
                
                # 最近新增的
                cursor.execute("""
                    SELECT COUNT(*) as recent_count 
                    FROM episodes 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '1 day'
                """)
                recent_count = cursor.fetchone()['recent_count']
                
                # 按 podcast_id 統計
                cursor.execute("""
                    SELECT podcast_id, COUNT(*) as episode_count 
                    FROM episodes 
                    GROUP BY podcast_id 
                    ORDER BY episode_count DESC 
                    LIMIT 10
                """)
                podcast_stats = cursor.fetchall()
                
                # 檢查重複
                cursor.execute("""
                    SELECT podcast_id, episode_title, COUNT(*) as duplicate_count
                    FROM episodes 
                    GROUP BY podcast_id, episode_title 
                    HAVING COUNT(*) > 1
                    ORDER BY duplicate_count DESC
                """)
                duplicates = cursor.fetchall()
                
                # 語言統計
                cursor.execute("""
                    SELECT languages, COUNT(*) as count 
                    FROM episodes 
                    WHERE languages IS NOT NULL 
                    GROUP BY languages 
                    ORDER BY count DESC
                """)
                languages = cursor.fetchall()
                
                return {
                    'total': total,
                    'recent_count': recent_count,
                    'podcast_stats': podcast_stats,
                    'duplicates': duplicates,
                    'languages': languages
                }
                
        except Exception as e:
            logger.error(f"獲取 Episodes 摘要失敗: {e}")
            return {}
    
    def check_data_integrity(self) -> Dict[str, Any]:
        """檢查資料完整性"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 檢查外鍵完整性
                cursor.execute("""
                    SELECT COUNT(*) as orphan_count
                    FROM episodes e
                    LEFT JOIN podcasts p ON e.podcast_id = p.podcast_id
                    WHERE p.podcast_id IS NULL
                """)
                orphan_episodes = cursor.fetchone()['orphan_count']
                
                # 檢查空標題
                cursor.execute("""
                    SELECT COUNT(*) as empty_title_count
                    FROM episodes 
                    WHERE episode_title IS NULL OR episode_title = ''
                """)
                empty_titles = cursor.fetchone()['empty_title_count']
                
                # 檢查空 podcast 名稱
                cursor.execute("""
                    SELECT COUNT(*) as empty_name_count
                    FROM podcasts 
                    WHERE name IS NULL OR name = ''
                """)
                empty_names = cursor.fetchone()['empty_name_count']
                
                return {
                    'orphan_episodes': orphan_episodes,
                    'empty_titles': empty_titles,
                    'empty_names': empty_names
                }
                
        except Exception as e:
            logger.error(f"檢查資料完整性失敗: {e}")
            return {}
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """獲取樣本資料"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(f"SELECT * FROM {table_name} ORDER BY created_at DESC LIMIT {limit}")
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"獲取 {table_name} 樣本資料失敗: {e}")
            return []
    
    def verify_batch_input_mapping(self, batch_input_folder: str) -> Dict[str, Any]:
        """驗證 batch_input 資料夾的映射"""
        try:
            json_files = [f for f in os.listdir(batch_input_folder) if f.endswith('.json')]
            
            podcast_files = [f for f in json_files if f.startswith('podcast_')]
            rss_files = [f for f in json_files if f.startswith('RSS_') or f.startswith('Spotify_RSS_')]
            
            # 提取 podcast_id
            podcast_ids_from_files = set()
            for filename in podcast_files:
                if filename.startswith('podcast_'):
                    try:
                        # 移除 .json 副檔名後再分割
                        name_without_ext = filename.replace('.json', '')
                        podcast_id = int(name_without_ext.split('_')[1])
                        podcast_ids_from_files.add(podcast_id)
                    except (IndexError, ValueError) as e:
                        logger.warning(f"無法解析 podcast 檔案名稱: {filename}, 錯誤: {e}")
                        continue
            
            for filename in rss_files:
                try:
                    # 移除 .json 副檔名後再分割
                    name_without_ext = filename.replace('.json', '')
                    if filename.startswith('RSS_'):
                        podcast_id = int(name_without_ext.split('_')[1])
                        podcast_ids_from_files.add(podcast_id)
                    elif filename.startswith('Spotify_RSS_'):
                        podcast_id = int(name_without_ext.split('_')[2])
                        podcast_ids_from_files.add(podcast_id)
                except (IndexError, ValueError) as e:
                    logger.warning(f"無法解析 RSS 檔案名稱: {filename}, 錯誤: {e}")
                    continue
            
            # 檢查資料庫中的 podcast_id
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT podcast_id FROM podcasts")
                podcast_ids_in_db = {row[0] for row in cursor.fetchall()}
            
            # 檢查映射
            missing_in_db = podcast_ids_from_files - podcast_ids_in_db
            extra_in_db = podcast_ids_in_db - podcast_ids_from_files
            
            return {
                'total_files': len(json_files),
                'podcast_files': len(podcast_files),
                'rss_files': len(rss_files),
                'podcast_ids_from_files': len(podcast_ids_from_files),
                'podcast_ids_in_db': len(podcast_ids_in_db),
                'missing_in_db': list(missing_in_db),
                'extra_in_db': list(extra_in_db),
                'mapping_complete': len(missing_in_db) == 0
            }
            
        except Exception as e:
            logger.error(f"驗證 batch_input 映射失敗: {e}")
            return {}
    
    def generate_verification_report(self, batch_input_folder: str) -> str:
        """生成驗證報告"""
        logger.info("開始生成驗證報告...")
        
        # 獲取各項統計
        podcasts_summary = self.get_podcasts_summary()
        episodes_summary = self.get_episodes_summary()
        data_integrity = self.check_data_integrity()
        mapping_verification = self.verify_batch_input_mapping(batch_input_folder)
        
        # 生成報告
        report = []
        report.append("=" * 80)
        report.append("資料上傳結果驗證報告")
        report.append("=" * 80)
        report.append(f"驗證時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Podcasts 統計
        report.append(f"\n📊 Podcasts 統計:")
        report.append(f"   - 總數: {podcasts_summary.get('total', 0):,}")
        report.append(f"   - 今日新增: {podcasts_summary.get('recent_count', 0):,}")
        
        if podcasts_summary.get('categories'):
            report.append(f"   - 分類統計:")
            for cat in podcasts_summary['categories'][:5]:  # 只顯示前5個
                report.append(f"     • {cat['category']}: {cat['count']}")
        
        if podcasts_summary.get('languages'):
            report.append(f"   - 語言統計:")
            for lang in podcasts_summary['languages'][:3]:  # 只顯示前3個
                report.append(f"     • {lang['languages']}: {lang['count']}")
        
        # Episodes 統計
        report.append(f"\n📻 Episodes 統計:")
        report.append(f"   - 總數: {episodes_summary.get('total', 0):,}")
        report.append(f"   - 今日新增: {episodes_summary.get('recent_count', 0):,}")
        
        if episodes_summary.get('podcast_stats'):
            report.append(f"   - 前5個 Podcast 的 Episode 數量:")
            for stat in episodes_summary['podcast_stats'][:5]:
                report.append(f"     • Podcast {stat['podcast_id']}: {stat['episode_count']} episodes")
        
        if episodes_summary.get('languages'):
            report.append(f"   - 語言統計:")
            for lang in episodes_summary['languages'][:3]:
                report.append(f"     • {lang['languages']}: {lang['count']}")
        
        # 資料完整性檢查
        report.append(f"\n🔍 資料完整性檢查:")
        report.append(f"   - 孤立 Episodes: {data_integrity.get('orphan_episodes', 0)}")
        report.append(f"   - 空標題 Episodes: {data_integrity.get('empty_titles', 0)}")
        report.append(f"   - 空名稱 Podcasts: {data_integrity.get('empty_names', 0)}")
        
        # 重複檢查
        if episodes_summary.get('duplicates'):
            report.append(f"   - 重複 Episodes: {len(episodes_summary['duplicates'])} 組")
            for dup in episodes_summary['duplicates'][:3]:  # 只顯示前3個
                report.append(f"     • Podcast {dup['podcast_id']} - {dup['episode_title']}: {dup['duplicate_count']} 次")
        else:
            report.append(f"   - 重複 Episodes: ✅ 無重複")
        
        # 映射驗證
        report.append(f"\n📁 Batch Input 映射驗證:")
        report.append(f"   - 總檔案數: {mapping_verification.get('total_files', 0)}")
        report.append(f"   - Podcast 檔案: {mapping_verification.get('podcast_files', 0)}")
        report.append(f"   - RSS 檔案: {mapping_verification.get('rss_files', 0)}")
        report.append(f"   - 檔案中的 Podcast ID: {mapping_verification.get('podcast_ids_from_files', 0)}")
        report.append(f"   - 資料庫中的 Podcast ID: {mapping_verification.get('podcast_ids_in_db', 0)}")
        
        if mapping_verification.get('missing_in_db'):
            report.append(f"   - 缺少在資料庫: {mapping_verification['missing_in_db']}")
        
        if mapping_verification.get('extra_in_db'):
            report.append(f"   - 資料庫中多餘: {mapping_verification['extra_in_db']}")
        
        if mapping_verification.get('mapping_complete'):
            report.append(f"   - 映射狀態: ✅ 完整")
        else:
            report.append(f"   - 映射狀態: ⚠️ 不完整")
        
        # 總結
        report.append(f"\n{'='*80}")
        report.append("總結")
        report.append(f"{'='*80}")
        
        total_issues = (
            data_integrity.get('orphan_episodes', 0) +
            data_integrity.get('empty_titles', 0) +
            data_integrity.get('empty_names', 0) +
            len(episodes_summary.get('duplicates', []))
        )
        
        if total_issues == 0 and mapping_verification.get('mapping_complete'):
            report.append("✅ 資料上傳驗證成功！所有資料正確插入且無重複")
        else:
            report.append(f"⚠️ 發現 {total_issues} 個問題，請檢查上述詳細資訊")
        
        report.append(f"\n{'='*80}")
        return "\n".join(report)
    
    def close(self):
        """關閉資料庫連接"""
        if self.conn:
            self.conn.close()
            logger.info("資料庫連接已關閉")

def main():
    """主程式"""
    logger.info("=== 驗證上傳結果 ===")
    
    # 資料庫配置
    config = {
        'host': os.getenv('POSTGRES_HOST', 'postgres.podwise.svc.cluster.local'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'podcast'),
        'user': os.getenv('POSTGRES_USER', 'bdse37'),
        'password': os.getenv('POSTGRES_PASSWORD', '111111')
    }
    
    # batch_input 資料夾路徑
    batch_input_folder = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'batch_input'
    )
    
    try:
        # 建立驗證器
        verifier = UploadResultVerifier(config)
        
        # 生成驗證報告
        report = verifier.generate_verification_report(batch_input_folder)
        print(report)
        
        # 儲存報告
        report_file = os.path.join(os.path.dirname(batch_input_folder), 'upload_verification_report.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"驗證報告已儲存到: {report_file}")
        
        # 關閉連接
        verifier.close()
        
    except Exception as e:
        logger.error(f"驗證失敗: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 