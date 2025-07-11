#!/usr/bin/env python3
"""
檢查和修復資料庫結構腳本
確保表格結構正確並添加必要的約束
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import List, Dict, Any, Optional
import traceback

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseStructureChecker:
    """資料庫結構檢查和修復類別"""
    
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
    
    def check_table_exists(self, table_name: str) -> bool:
        """檢查表格是否存在"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """, (table_name,))
                
                return cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"檢查表格 {table_name} 失敗: {e}")
            return False
    
    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """獲取表格欄位資訊"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                    ORDER BY ordinal_position;
                """, (table_name,))
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"獲取表格 {table_name} 欄位失敗: {e}")
            return []
    
    def get_table_constraints(self, table_name: str) -> List[Dict[str, Any]]:
        """獲取表格約束資訊"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        tc.constraint_name,
                        tc.constraint_type,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints tc
                    LEFT JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    LEFT JOIN information_schema.constraint_column_usage ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.table_schema = 'public'
                    AND tc.table_name = %s
                    ORDER BY tc.constraint_type, tc.constraint_name;
                """, (table_name,))
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"獲取表格 {table_name} 約束失敗: {e}")
            return []
    
    def check_episodes_table_structure(self) -> Dict[str, Any]:
        """檢查 episodes 表格結構"""
        logger.info("檢查 episodes 表格結構...")
        
        result = {
            'table_exists': False,
            'columns': [],
            'constraints': [],
            'missing_constraints': [],
            'issues': []
        }
        
        # 檢查表格是否存在
        result['table_exists'] = self.check_table_exists('episodes')
        if not result['table_exists']:
            result['issues'].append("episodes 表格不存在")
            return result
        
        # 獲取欄位資訊
        result['columns'] = self.get_table_columns('episodes')
        
        # 獲取約束資訊
        result['constraints'] = self.get_table_constraints('episodes')
        
        # 檢查必要的約束
        constraint_types = [c['constraint_type'] for c in result['constraints']]
        constraint_columns = [c['column_name'] for c in result['constraints'] if c['column_name']]
        
        # 檢查主鍵
        if 'PRIMARY KEY' not in constraint_types:
            result['missing_constraints'].append("缺少主鍵約束")
        
        # 檢查外鍵
        if 'FOREIGN KEY' not in constraint_types:
            result['missing_constraints'].append("缺少外鍵約束 (podcast_id)")
        
        # 檢查唯一約束（用於 ON CONFLICT）
        if 'UNIQUE' not in constraint_types:
            result['missing_constraints'].append("缺少唯一約束（用於避免重複插入）")
        
        # 檢查索引
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT indexname, indexdef 
                    FROM pg_indexes 
                    WHERE tablename = 'episodes';
                """)
                indexes = cursor.fetchall()
                result['indexes'] = indexes
                
                # 檢查必要的索引
                index_names = [idx[0] for idx in indexes]
                if 'idx_episodes_podcast_id' not in index_names:
                    result['missing_constraints'].append("缺少 podcast_id 索引")
                if 'idx_episodes_published_date' not in index_names:
                    result['missing_constraints'].append("缺少 published_date 索引")
                    
        except Exception as e:
            logger.error(f"檢查索引失敗: {e}")
            result['issues'].append(f"檢查索引失敗: {e}")
        
        return result
    
    def fix_episodes_table_structure(self) -> Dict[str, Any]:
        """修復 episodes 表格結構"""
        logger.info("修復 episodes 表格結構...")
        
        result = {
            'success': False,
            'actions': [],
            'errors': []
        }
        
        try:
            with self.conn.cursor() as cursor:
                # 1. 添加唯一約束（用於 ON CONFLICT）
                try:
                    cursor.execute("""
                        ALTER TABLE episodes 
                        ADD CONSTRAINT episodes_podcast_title_unique 
                        UNIQUE (podcast_id, episode_title);
                    """)
                    result['actions'].append("添加唯一約束 (podcast_id, episode_title)")
                except Exception as e:
                    if "already exists" not in str(e):
                        result['errors'].append(f"添加唯一約束失敗: {e}")
                    else:
                        result['actions'].append("唯一約束已存在")
                
                # 2. 確保外鍵約束存在
                try:
                    cursor.execute("""
                        ALTER TABLE episodes 
                        ADD CONSTRAINT episodes_podcast_id_fkey 
                        FOREIGN KEY (podcast_id) 
                        REFERENCES podcasts(podcast_id) 
                        ON DELETE CASCADE ON UPDATE CASCADE;
                    """)
                    result['actions'].append("添加外鍵約束 (podcast_id)")
                except Exception as e:
                    if "already exists" not in str(e):
                        result['errors'].append(f"添加外鍵約束失敗: {e}")
                    else:
                        result['actions'].append("外鍵約束已存在")
                
                # 3. 添加必要的索引
                try:
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_episodes_podcast_id 
                        ON episodes(podcast_id);
                    """)
                    result['actions'].append("添加 podcast_id 索引")
                except Exception as e:
                    result['errors'].append(f"添加 podcast_id 索引失敗: {e}")
                
                try:
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_episodes_published_date 
                        ON episodes(published_date);
                    """)
                    result['actions'].append("添加 published_date 索引")
                except Exception as e:
                    result['errors'].append(f"添加 published_date 索引失敗: {e}")
                
                # 4. 添加 episode_title 索引（用於查詢）
                try:
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_episodes_title 
                        ON episodes(episode_title);
                    """)
                    result['actions'].append("添加 episode_title 索引")
                except Exception as e:
                    result['errors'].append(f"添加 episode_title 索引失敗: {e}")
                
                self.conn.commit()
                result['success'] = True
                
        except Exception as e:
            logger.error(f"修復表格結構失敗: {e}")
            self.conn.rollback()
            result['errors'].append(f"修復失敗: {e}")
        
        return result
    
    def check_podcasts_table_structure(self) -> Dict[str, Any]:
        """檢查 podcasts 表格結構"""
        logger.info("檢查 podcasts 表格結構...")
        
        result = {
            'table_exists': False,
            'columns': [],
            'constraints': [],
            'missing_constraints': [],
            'issues': []
        }
        
        # 檢查表格是否存在
        result['table_exists'] = self.check_table_exists('podcasts')
        if not result['table_exists']:
            result['issues'].append("podcasts 表格不存在")
            return result
        
        # 獲取欄位資訊
        result['columns'] = self.get_table_columns('podcasts')
        
        # 獲取約束資訊
        result['constraints'] = self.get_table_constraints('podcasts')
        
        return result
    
    def generate_structure_report(self, episodes_result: Dict[str, Any], podcasts_result: Dict[str, Any]) -> str:
        """生成結構檢查報告"""
        report = []
        report.append("=" * 60)
        report.append("資料庫結構檢查報告")
        report.append("=" * 60)
        report.append(f"檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Episodes 表格檢查結果
        report.append(f"\n📋 Episodes 表格檢查:")
        report.append(f"   - 表格存在: {'✅' if episodes_result['table_exists'] else '❌'}")
        
        if episodes_result['table_exists']:
            report.append(f"   - 欄位數量: {len(episodes_result['columns'])}")
            report.append(f"   - 約束數量: {len(episodes_result['constraints'])}")
            
            if episodes_result['missing_constraints']:
                report.append(f"   - 缺少約束: {len(episodes_result['missing_constraints'])}")
                for constraint in episodes_result['missing_constraints']:
                    report.append(f"     ❌ {constraint}")
            else:
                report.append("   - 約束完整: ✅")
            
            if episodes_result['issues']:
                report.append(f"   - 問題數量: {len(episodes_result['issues'])}")
                for issue in episodes_result['issues']:
                    report.append(f"     ⚠️ {issue}")
        
        # Podcasts 表格檢查結果
        report.append(f"\n📋 Podcasts 表格檢查:")
        report.append(f"   - 表格存在: {'✅' if podcasts_result['table_exists'] else '❌'}")
        
        if podcasts_result['table_exists']:
            report.append(f"   - 欄位數量: {len(podcasts_result['columns'])}")
            report.append(f"   - 約束數量: {len(podcasts_result['constraints'])}")
        
        # 欄位詳細資訊
        if episodes_result['table_exists'] and episodes_result['columns']:
            report.append(f"\n📝 Episodes 欄位詳情:")
            for col in episodes_result['columns']:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                report.append(f"   - {col['column_name']}: {col['data_type']} ({nullable})")
        
        if podcasts_result['table_exists'] and podcasts_result['columns']:
            report.append(f"\n📝 Podcasts 欄位詳情:")
            for col in podcasts_result['columns']:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                report.append(f"   - {col['column_name']}: {col['data_type']} ({nullable})")
        
        report.append("\n" + "=" * 60)
        return "\n".join(report)
    
    def close(self):
        """關閉資料庫連接"""
        if self.conn:
            self.conn.close()
            logger.info("資料庫連接已關閉")

def main():
    """主程式"""
    logger.info("=== 資料庫結構檢查和修復 ===")
    
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
        checker = DatabaseStructureChecker(config)
        
        # 檢查表格結構
        episodes_result = checker.check_episodes_table_structure()
        podcasts_result = checker.check_podcasts_table_structure()
        
        # 生成檢查報告
        report = checker.generate_structure_report(episodes_result, podcasts_result)
        print(report)
        
        # 儲存報告
        report_file = os.path.join(os.path.dirname(__file__), '..', 'db_structure_report.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"結構檢查報告已儲存到: {report_file}")
        
        # 如果有問題，詢問是否修復
        if episodes_result['missing_constraints'] or episodes_result['issues']:
            print("\n🔧 發現結構問題，是否要修復？(y/n): ", end="")
            response = input().strip().lower()
            
            if response in ['y', 'yes', '是']:
                logger.info("開始修復表格結構...")
                fix_result = checker.fix_episodes_table_structure()
                
                if fix_result['success']:
                    logger.info("✅ 表格結構修復成功")
                    for action in fix_result['actions']:
                        logger.info(f"   - {action}")
                else:
                    logger.error("❌ 表格結構修復失敗")
                    for error in fix_result['errors']:
                        logger.error(f"   - {error}")
                
                # 重新檢查
                logger.info("重新檢查表格結構...")
                episodes_result_after = checker.check_episodes_table_structure()
                report_after = checker.generate_structure_report(episodes_result_after, podcasts_result)
                
                # 儲存修復後報告
                report_file_after = os.path.join(os.path.dirname(__file__), '..', 'db_structure_report_after_fix.txt')
                with open(report_file_after, 'w', encoding='utf-8') as f:
                    f.write(report_after)
                
                logger.info(f"修復後報告已儲存到: {report_file_after}")
            else:
                logger.info("跳過結構修復")
        
        # 關閉連接
        checker.close()
        
        # 如果結構正確，提示可以進行上傳
        if episodes_result['table_exists'] and not episodes_result['missing_constraints']:
            logger.info("✅ 資料庫結構檢查完成，可以進行批次上傳")
        else:
            logger.warning("⚠️ 資料庫結構有問題，請先修復再進行上傳")
        
    except Exception as e:
        logger.error(f"結構檢查失敗: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 