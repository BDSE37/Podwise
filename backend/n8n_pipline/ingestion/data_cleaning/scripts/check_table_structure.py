#!/usr/bin/env python3
"""
檢查 PostgreSQL 表格結構
"""

import psycopg2

def check_table_structure():
    """檢查表格結構"""
    try:
        conn = psycopg2.connect(
            host='postgres.podwise.svc.cluster.local',
            port=5432,
            database='podcast',
            user='bdse37',
            password='111111'
        )
        cursor = conn.cursor()
        
        # 檢查 episodes 表格結構
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'episodes' 
            ORDER BY ordinal_position
        """)
        print('=== Episodes 表格結構 ===')
        for row in cursor.fetchall():
            print(f'{row[0]}: {row[1]} ({row[2]})')
        
        # 檢查 podcasts 表格結構
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'podcasts' 
            ORDER BY ordinal_position
        """)
        print('\n=== Podcasts 表格結構 ===')
        for row in cursor.fetchall():
            print(f'{row[0]}: {row[1]} ({row[2]})')
        
        conn.close()
        print('\n✅ 表格結構檢查完成')
        
    except Exception as e:
        print(f'❌ 查詢失敗: {e}')

if __name__ == "__main__":
    check_table_structure() 