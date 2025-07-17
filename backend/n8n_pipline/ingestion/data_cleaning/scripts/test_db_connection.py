#!/usr/bin/env python3
"""
測試 PostgreSQL 連接和表格結構
"""

import psycopg2
import json

def test_connection():
    """測試資料庫連接"""
    try:
        conn = psycopg2.connect(
            host='postgres.podwise.svc.cluster.local',
            port=5432,
            database='podcast',
            user='bdse37',
            password='111111'
        )
        print('✅ PostgreSQL 連接成功')
        
        cursor = conn.cursor()
        
        # 檢查表格是否存在
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('episodes', 'podcasts')
        """)
        
        tables = cursor.fetchall()
        print(f'📋 找到表格: {[table[0] for table in tables]}')
        
        # 檢查 episodes 表格結構
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'episodes' 
            ORDER BY ordinal_position
        """)
        
        print('\n📊 Episodes 表格結構:')
        for row in cursor.fetchall():
            print(f'  {row[0]}: {row[1]}')
        
        # 檢查 podcasts 表格結構
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'podcasts' 
            ORDER BY ordinal_position
        """)
        
        print('\n📊 Podcasts 表格結構:')
        for row in cursor.fetchall():
            print(f'  {row[0]}: {row[1]}')
        
        # 檢查現有資料數量
        cursor.execute("SELECT COUNT(*) FROM episodes")
        episode_count = cursor.fetchone()[0]
        print(f'\n📈 Episodes 數量: {episode_count}')
        
        cursor.execute("SELECT COUNT(*) FROM podcasts")
        podcast_count = cursor.fetchone()[0]
        print(f'📈 Podcasts 數量: {podcast_count}')
        
        conn.close()
        print('\n✅ 測試完成')
        
    except Exception as e:
        print(f'❌ 測試失敗: {e}')

if __name__ == "__main__":
    test_connection() 