#!/usr/bin/env python3
"""
詳細資料庫結構檢查腳本
檢查所有表格的欄位、約束和索引設計
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

class DetailedDatabaseInspector:
    """詳細資料庫結構檢查類別"""
    
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
    
    def get_all_tables(self) -> List[str]:
        """獲取所有表格名稱"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public' 
                    ORDER BY tablename;
                """)
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"獲取表格列表失敗: {e}")
            return []
    
    def get_table_columns_detailed(self, table_name: str) -> List[Dict[str, Any]]:
        """獲取表格詳細欄位資訊"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale,
                        ordinal_position
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                    ORDER BY ordinal_position;
                """, (table_name,))
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"獲取表格 {table_name} 欄位失敗: {e}")
            return []
    
    def get_table_constraints_detailed(self, table_name: str) -> List[Dict[str, Any]]:
        """獲取表格詳細約束資訊"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        tc.constraint_name,
                        tc.constraint_type,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name,
                        rc.delete_rule,
                        rc.update_rule
                    FROM information_schema.table_constraints tc
                    LEFT JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    LEFT JOIN information_schema.constraint_column_usage ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    LEFT JOIN information_schema.referential_constraints rc
                        ON tc.constraint_name = rc.constraint_name
                        AND tc.table_schema = rc.constraint_schema
                    WHERE tc.table_schema = 'public'
                    AND tc.table_name = %s
                    ORDER BY tc.constraint_type, tc.constraint_name;
                """, (table_name,))
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"獲取表格 {table_name} 約束失敗: {e}")
            return []
    
    def get_table_indexes_detailed(self, table_name: str) -> List[Dict[str, Any]]:
        """獲取表格詳細索引資訊"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        indexname,
                        indexdef,
                        tablename
                    FROM pg_indexes 
                    WHERE tablename = %s
                    ORDER BY indexname;
                """, (table_name,))
                
                return cursor.fetchall()
                
        except Exception as e:
            logger.error(f"獲取表格 {table_name} 索引失敗: {e}")
            return []
    
    def get_table_row_count(self, table_name: str) -> int:
        """獲取表格行數"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                return cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"獲取表格 {table_name} 行數失敗: {e}")
            return 0
    
    def inspect_table_detailed(self, table_name: str) -> Dict[str, Any]:
        """詳細檢查單個表格"""
        logger.info(f"詳細檢查表格: {table_name}")
        
        result = {
            'table_name': table_name,
            'columns': [],
            'constraints': [],
            'indexes': [],
            'row_count': 0,
            'issues': [],
            'recommendations': []
        }
        
        # 獲取欄位資訊
        result['columns'] = self.get_table_columns_detailed(table_name)
        
        # 獲取約束資訊
        result['constraints'] = self.get_table_constraints_detailed(table_name)
        
        # 獲取索引資訊
        result['indexes'] = self.get_table_indexes_detailed(table_name)
        
        # 獲取行數
        result['row_count'] = self.get_table_row_count(table_name)
        
        # 分析問題和建議
        self._analyze_table_structure(result)
        
        return result
    
    def _analyze_table_structure(self, table_info: Dict[str, Any]):
        """分析表格結構並提供建議"""
        table_name = table_info['table_name']
        columns = table_info['columns']
        constraints = table_info['constraints']
        indexes = table_info['indexes']
        
        # 檢查主鍵
        has_primary_key = any(c['constraint_type'] == 'PRIMARY KEY' for c in constraints)
        if not has_primary_key:
            table_info['issues'].append("缺少主鍵約束")
            table_info['recommendations'].append("建議添加主鍵約束")
        
        # 檢查外鍵
        foreign_keys = [c for c in constraints if c['constraint_type'] == 'FOREIGN KEY']
        if not foreign_keys:
            table_info['recommendations'].append("沒有外鍵約束")
        
        # 檢查唯一約束
        unique_constraints = [c for c in constraints if c['constraint_type'] == 'UNIQUE']
        if not unique_constraints:
            table_info['recommendations'].append("沒有唯一約束")
        
        # 檢查索引
        index_names = [idx['indexname'] for idx in indexes]
        
        # 針對特定表格的檢查
        if table_name == 'episodes':
            # 檢查 episodes 表格的特殊需求
            if not any('podcast_id' in idx['indexdef'] for idx in indexes):
                table_info['recommendations'].append("建議為 podcast_id 添加索引")
            
            if not any('published_date' in idx['indexdef'] for idx in indexes):
                table_info['recommendations'].append("建議為 published_date 添加索引")
            
            if not any('episode_title' in idx['indexdef'] for idx in indexes):
                table_info['recommendations'].append("建議為 episode_title 添加索引")
            
            # 檢查是否有唯一約束用於避免重複
            if not any('podcast_id' in str(c) and 'episode_title' in str(c) for c in unique_constraints):
                table_info['recommendations'].append("建議添加 (podcast_id, episode_title) 唯一約束以避免重複")
        
        elif table_name == 'podcasts':
            # 檢查 podcasts 表格的特殊需求
            if not any('category' in idx['indexdef'] for idx in indexes):
                table_info['recommendations'].append("建議為 category 添加索引")
            
            if not any('rss_link' in idx['indexdef'] for idx in indexes):
                table_info['recommendations'].append("建議為 rss_link 添加索引")
    
    def generate_detailed_report(self, table_inspections: List[Dict[str, Any]]) -> str:
        """生成詳細檢查報告"""
        report = []
        report.append("=" * 80)
        report.append("詳細資料庫結構檢查報告")
        report.append("=" * 80)
        report.append(f"檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"資料庫: {self.config['database']}")
        report.append(f"主機: {self.config['host']}:{self.config['port']}")
        
        # 總覽
        report.append(f"\n📊 總覽:")
        report.append(f"   - 表格數量: {len(table_inspections)}")
        total_rows = sum(t['row_count'] for t in table_inspections)
        report.append(f"   - 總行數: {total_rows:,}")
        
        # 重點表格檢查
        focus_tables = ['episodes', 'podcasts', 'users', 'topics', 'transcripts']
        
        for table_info in table_inspections:
            if table_info['table_name'] in focus_tables:
                report.append(f"\n{'='*60}")
                report.append(f"📋 表格: {table_info['table_name']}")
                report.append(f"{'='*60}")
                
                # 基本資訊
                report.append(f"   📈 行數: {table_info['row_count']:,}")
                report.append(f"   📝 欄位數: {len(table_info['columns'])}")
                report.append(f"   🔗 約束數: {len(table_info['constraints'])}")
                report.append(f"   📍 索引數: {len(table_info['indexes'])}")
                
                # 欄位詳情
                report.append(f"\n   📝 欄位詳情:")
                for col in table_info['columns']:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                    length = f"({col['character_maximum_length']})" if col['character_maximum_length'] else ""
                    precision = ""
                    if col['numeric_precision']:
                        if col['numeric_scale']:
                            precision = f"({col['numeric_precision']},{col['numeric_scale']})"
                        else:
                            precision = f"({col['numeric_precision']})"
                    
                    report.append(f"     - {col['column_name']}: {col['data_type']}{length}{precision}{default} ({nullable})")
                
                # 約束詳情
                if table_info['constraints']:
                    report.append(f"\n   🔗 約束詳情:")
                    for constraint in table_info['constraints']:
                        if constraint['constraint_type'] == 'FOREIGN KEY':
                            report.append(f"     - {constraint['constraint_name']}: {constraint['constraint_type']} ({constraint['column_name']} -> {constraint['foreign_table_name']}.{constraint['foreign_column_name']})")
                        else:
                            report.append(f"     - {constraint['constraint_name']}: {constraint['constraint_type']} ({constraint['column_name']})")
                
                # 索引詳情
                if table_info['indexes']:
                    report.append(f"\n   📍 索引詳情:")
                    for index in table_info['indexes']:
                        report.append(f"     - {index['indexname']}: {index['indexdef']}")
                
                # 問題和建議
                if table_info['issues']:
                    report.append(f"\n   ⚠️ 發現問題:")
                    for issue in table_info['issues']:
                        report.append(f"     - {issue}")
                
                if table_info['recommendations']:
                    report.append(f"\n   💡 建議:")
                    for rec in table_info['recommendations']:
                        report.append(f"     - {rec}")
        
        # 其他表格簡要資訊
        other_tables = [t for t in table_inspections if t['table_name'] not in focus_tables]
        if other_tables:
            report.append(f"\n{'='*60}")
            report.append(f"📋 其他表格簡要資訊")
            report.append(f"{'='*60}")
            
            for table_info in other_tables:
                report.append(f"   - {table_info['table_name']}: {table_info['row_count']:,} 行, {len(table_info['columns'])} 欄位, {len(table_info['constraints'])} 約束, {len(table_info['indexes'])} 索引")
        
        # 總結
        report.append(f"\n{'='*80}")
        report.append("總結")
        report.append(f"{'='*80}")
        
        total_issues = sum(len(t['issues']) for t in table_inspections)
        total_recommendations = sum(len(t['recommendations']) for t in table_inspections)
        
        report.append(f"   - 發現問題: {total_issues} 個")
        report.append(f"   - 建議改進: {total_recommendations} 個")
        
        if total_issues == 0:
            report.append("   ✅ 資料庫結構檢查完成，沒有發現嚴重問題")
        else:
            report.append("   ⚠️ 建議先解決發現的問題再進行資料上傳")
        
        report.append(f"\n{'='*80}")
        return "\n".join(report)
    
    def close(self):
        """關閉資料庫連接"""
        if self.conn:
            self.conn.close()
            logger.info("資料庫連接已關閉")

def main():
    """主程式"""
    logger.info("=== 詳細資料庫結構檢查 ===")
    
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
        inspector = DetailedDatabaseInspector(config)
        
        # 獲取所有表格
        all_tables = inspector.get_all_tables()
        logger.info(f"發現 {len(all_tables)} 個表格")
        
        # 詳細檢查每個表格
        table_inspections = []
        for table_name in all_tables:
            table_info = inspector.inspect_table_detailed(table_name)
            table_inspections.append(table_info)
        
        # 生成詳細報告
        report = inspector.generate_detailed_report(table_inspections)
        print(report)
        
        # 儲存報告
        report_file = os.path.join(os.path.dirname(__file__), '..', 'detailed_db_inspection_report.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"詳細檢查報告已儲存到: {report_file}")
        
        # 關閉連接
        inspector.close()
        
        # 詢問是否要修復問題
        total_issues = sum(len(t['issues']) for t in table_inspections)
        if total_issues > 0:
            print(f"\n🔧 發現 {total_issues} 個問題，是否要修復？(y/n): ", end="")
            response = input().strip().lower()
            
            if response in ['y', 'yes', '是']:
                logger.info("請執行 check_and_fix_db_structure.py 來修復問題")
            else:
                logger.info("跳過修復，請手動處理問題")
        
    except Exception as e:
        logger.error(f"詳細檢查失敗: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 