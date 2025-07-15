#!/usr/bin/env python3
"""
資料庫結構檢查腳本
檢查 PostgreSQL 資料庫中的表結構和欄位類型
"""

import psycopg2
import os
from dotenv import load_dotenv

def get_db_config():
    """從環境變數獲取資料庫配置"""
    load_dotenv()
    
    return {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'database': os.getenv('POSTGRES_DB', 'podwise'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
    }

def check_database_structure():
    """檢查資料庫結構"""
    config = get_db_config()
    
    try:
        print("正在連接資料庫...")
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        print("✅ 成功連接到 PostgreSQL 資料庫\n")
        
        # 列出所有表
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print("=== 資料庫中的所有表 ===")
        for table in tables:
            print(f"- {table[0]}")
        print()
        
        # 檢查 users 表結構
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("=== users 表結構 ===")
        for column in columns:
            col_name, data_type, is_nullable, default_val = column
            print(f"{col_name}: {data_type} (nullable: {is_nullable}, default: {default_val})")
        print()
        
        # 檢查 users 表的資料樣本
        cursor.execute("""
            SELECT user_id, user_code 
            FROM users 
            LIMIT 5;
        """)
        
        rows = cursor.fetchall()
        print("=== users 表資料樣本 ===")
        for row in rows:
            print(f"user_id: {row[0]} (type: {type(row[0])}), user_code: {row[1]} (type: {type(row[1])})")
        print()
        
        # 檢查 user_feedback 表結構
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'user_feedback' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("=== user_feedback 表結構 ===")
        for column in columns:
            col_name, data_type, is_nullable, default_val = column
            print(f"{col_name}: {data_type} (nullable: {is_nullable}, default: {default_val})")
        print()
        
        # 檢查 user_feedback 表的 user_id 欄位資料樣本
        cursor.execute("""
            SELECT user_id, episode_id, bookmark, preview_played 
            FROM user_feedback 
            LIMIT 5;
        """)
        
        rows = cursor.fetchall()
        print("=== user_feedback 表資料樣本 ===")
        for row in rows:
            print(f"user_id: {row[0]} (type: {type(row[0])}), episode_id: {row[1]}, bookmark: {row[2]}, preview_played: {row[3]}")
        print()
        
        # 檢查是否有其他包含 user 相關欄位的表
        cursor.execute("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND column_name LIKE '%user%'
            ORDER BY table_name, column_name;
        """)
        
        user_columns = cursor.fetchall()
        print("=== 包含 user 相關欄位的表 ===")
        for col in user_columns:
            print(f"表: {col[0]}, 欄位: {col[1]}, 類型: {col[2]}")
        print()
        
        cursor.close()
        conn.close()
        print("✅ 資料庫結構檢查完成")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")

if __name__ == "__main__":
    check_database_structure() 