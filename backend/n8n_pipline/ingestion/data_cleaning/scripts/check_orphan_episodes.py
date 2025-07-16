#!/usr/bin/env python3
"""
檢查孤立 Episodes 腳本
分析沒有對應 Podcast 的 Episodes
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import List, Dict, Any
import traceback

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OrphanEpisodesChecker:
    """孤立 Episodes 檢查類別"""
    
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
    
    def get_orphan_episodes(self) -> List[Dict[str, Any]]:
        """獲取孤立的 Episodes"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT e.podcast_id, e.episode_title, e.audio_url, e.created_at
                    FROM episodes e
                    LEFT JOIN podcasts p ON e.podcast_id = p.podcast_id
                    WHERE p.podcast_id IS NULL
                    ORDER BY e.created_at DESC
                    LIMIT 100
                """)
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"獲取孤立 Episodes 失敗: {e}")
            return []
    
    def get_orphan_podcast_ids(self) -> List[int]:
        """獲取孤立的 podcast_id 列表"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT e.podcast_id
                    FROM episodes e
                    LEFT JOIN podcasts p ON e.podcast_id = p.podcast_id
                    WHERE p.podcast_id IS NULL
                    ORDER BY e.podcast_id
                """)
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"獲取孤立 podcast_id 失敗: {e}")
            return []
    
    def get_podcast_summary(self) -> Dict[str, Any]:
        """獲取 Podcast 摘要"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT COUNT(*) as total FROM podcasts")
                total = cursor.fetchone()['total']
                
                cursor.execute("SELECT podcast_id FROM podcasts ORDER BY podcast_id")
                podcast_ids = [row['podcast_id'] for row in cursor.fetchall()]
                
                return {
                    'total': total,
                    'podcast_ids': podcast_ids
                }
                
        except Exception as e:
            logger.error(f"獲取 Podcast 摘要失敗: {e}")
            return {}
    
    def get_episode_summary(self) -> Dict[str, Any]:
        """獲取 Episode 摘要"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT COUNT(*) as total FROM episodes")
                total = cursor.fetchone()['total']
                
                cursor.execute("""
                    SELECT podcast_id, COUNT(*) as episode_count
                    FROM episodes
                    GROUP BY podcast_id
                    ORDER BY episode_count DESC
                """)
                podcast_stats = cursor.fetchall()
                
                return {
                    'total': total,
                    'podcast_stats': podcast_stats
                }
                
        except Exception as e:
            logger.error(f"獲取 Episode 摘要失敗: {e}")
            return {}
    
    def generate_orphan_report(self) -> str:
        """生成孤立 Episodes 報告"""
        logger.info("開始生成孤立 Episodes 報告...")
        
        # 獲取資料
        orphan_episodes = self.get_orphan_episodes()
        orphan_podcast_ids = self.get_orphan_podcast_ids()
        podcast_summary = self.get_podcast_summary()
        episode_summary = self.get_episode_summary()
        
        # 生成報告
        report = []
        report.append("=" * 80)
        report.append("孤立 Episodes 檢查報告")
        report.append("=" * 80)
        report.append(f"檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 統計摘要
        report.append(f"\n📊 統計摘要:")
        report.append(f"   - Podcasts 總數: {podcast_summary.get('total', 0):,}")
        report.append(f"   - Episodes 總數: {episode_summary.get('total', 0):,}")
        report.append(f"   - 孤立 Episodes: {len(orphan_episodes):,}")
        report.append(f"   - 孤立 Podcast ID: {len(orphan_podcast_ids)} 個")
        
        # 孤立 Podcast ID 列表
        if orphan_podcast_ids:
            report.append(f"\n🔍 孤立的 Podcast ID:")
            report.append(f"   - 總數: {len(orphan_podcast_ids)}")
            report.append(f"   - ID 列表: {orphan_podcast_ids}")
            
            # 按 ID 分組統計
            report.append(f"\n📋 按 Podcast ID 分組的孤立 Episodes:")
            for podcast_id in orphan_podcast_ids[:10]:  # 只顯示前10個
                count = sum(1 for ep in orphan_episodes if ep['podcast_id'] == podcast_id)
                report.append(f"   - Podcast {podcast_id}: {count} episodes")
        
        # 樣本孤立 Episodes
        if orphan_episodes:
            report.append(f"\n📝 樣本孤立 Episodes (前10個):")
            for i, episode in enumerate(orphan_episodes[:10], 1):
                title = episode['episode_title'][:50] + "..." if len(episode['episode_title']) > 50 else episode['episode_title']
                report.append(f"   {i}. Podcast {episode['podcast_id']} - {title}")
                report.append(f"      建立時間: {episode['created_at']}")
        
        # 建議解決方案
        report.append(f"\n💡 建議解決方案:")
        report.append(f"   1. 檢查 batch_input 資料夾中是否有對應的 podcast_*.json 檔案")
        report.append(f"   2. 確認 podcast_*.json 檔案是否正確上傳到資料庫")
        report.append(f"   3. 檢查 podcast_id 是否一致")
        report.append(f"   4. 如果不需要這些 Episodes，可以刪除它們")
        
        # 刪除孤立 Episodes 的 SQL
        if orphan_podcast_ids:
            report.append(f"\n🗑️ 刪除孤立 Episodes 的 SQL:")
            report.append(f"   DELETE FROM episodes WHERE podcast_id IN ({','.join(map(str, orphan_podcast_ids))});")
        
        report.append(f"\n{'='*80}")
        return "\n".join(report)
    
    def close(self):
        """關閉資料庫連接"""
        if self.conn:
            self.conn.close()
            logger.info("資料庫連接已關閉")

def main():
    """主程式"""
    logger.info("=== 檢查孤立 Episodes ===")
    
    # 資料庫配置
    config = {
        'host': os.getenv('POSTGRES_HOST', 'postgres.podwise.svc.cluster.local'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'podcast'),
        'user': os.getenv('POSTGRES_USER', 'bdse37'),
        'password': os.getenv('POSTGRES_PASSWORD', '111111')
    }
    
    try:
        # 建立檢查器
        checker = OrphanEpisodesChecker(config)
        
        # 生成報告
        report = checker.generate_orphan_report()
        print(report)
        
        # 儲存報告
        report_file = os.path.join(os.path.dirname(__file__), 'orphan_episodes_report.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"孤立 Episodes 報告已儲存到: {report_file}")
        
        # 關閉連接
        checker.close()
        
    except Exception as e:
        logger.error(f"檢查失敗: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 