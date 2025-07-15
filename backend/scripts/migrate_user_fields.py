#!/usr/bin/env python3
"""
用戶欄位遷移腳本
將 users 表的 user_code 複製到 user_id，並將 user_id 類型從 integer 改為 varchar
"""

import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

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

def backup_table(cursor, table_name):
    """備份表"""
    backup_name = f"{table_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"📋 備份 {table_name} 表為 {backup_name}...")
    
    cursor.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM {table_name}")
    print(f"✅ 備份完成: {backup_name}")
    return backup_name

def get_foreign_key_constraints(cursor, table_name, column_name):
    """獲取外鍵約束"""
    cursor.execute("""
        SELECT 
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            tc.constraint_name
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' 
          AND ccu.table_name = %s 
          AND ccu.column_name = %s
    """, (table_name, column_name))
    
    return cursor.fetchall()

def migrate_user_fields():
    """執行用戶欄位遷移"""
    config = get_db_config()
    
    try:
        print("🔗 正在連接資料庫...")
        conn = psycopg2.connect(**config)
        conn.autocommit = False  # 啟用事務
        cursor = conn.cursor()
        print("✅ 成功連接到 PostgreSQL 資料庫\n")
        
        # 1. 備份 users 和 user_feedback 表
        users_backup = backup_table(cursor, "users")
        user_feedback_backup = backup_table(cursor, "user_feedback")
        
        # 2. 檢查外鍵約束
        print("\n🔍 檢查外鍵約束...")
        fk_constraints = get_foreign_key_constraints(cursor, "users", "user_id")
        
        if fk_constraints:
            print("⚠️  發現以下外鍵約束，需要先刪除：")
            for constraint in fk_constraints:
                print(f"   - {constraint[0]}.{constraint[1]} -> users.user_id")
            
            # 刪除外鍵約束
            for constraint in fk_constraints:
                print(f"🗑️  刪除外鍵約束: {constraint[4]}")
                cursor.execute(f"ALTER TABLE {constraint[0]} DROP CONSTRAINT {constraint[4]}")
        
        # 3. 處理 users 表
        print("\n🔄 開始處理 users 表...")
        
        # 3.1 新增臨時欄位
        print("➕ 新增臨時欄位 user_id_new...")
        cursor.execute("ALTER TABLE users ADD COLUMN user_id_new VARCHAR(50)")
        
        # 3.2 複製 user_code 到 user_id_new
        print("📋 複製 user_code 到 user_id_new...")
        cursor.execute("""
            UPDATE users 
            SET user_id_new = user_code 
            WHERE user_code IS NOT NULL
        """)
        
        # 3.3 檢查複製結果
        cursor.execute("SELECT COUNT(*) FROM users WHERE user_id_new IS NOT NULL")
        updated_count = cursor.fetchone()[0]
        print(f"✅ users 表已更新 {updated_count} 筆記錄")
        
        # 3.4 檢查並處理 user_id 的依賴關係
        print("🔍 檢查 user_id 欄位的依賴關係...")
        cursor.execute("""
            SELECT 
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'users' 
                AND kcu.column_name = 'user_id'
        """)
        
        constraints = cursor.fetchall()
        if constraints:
            print("⚠️  發現以下依賴於 user_id 的約束：")
            for constraint in constraints:
                print(f"   - {constraint[0]} ({constraint[1]})")
                cursor.execute(f"ALTER TABLE users DROP CONSTRAINT {constraint[0]} CASCADE")
                print(f"   ✅ 已刪除約束: {constraint[0]}")
        
        # 3.5 刪除舊的 user_id 欄位
        print("🗑️  刪除舊的 user_id 欄位...")
        cursor.execute("ALTER TABLE users DROP COLUMN user_id CASCADE")
        
        # 3.6 重新命名 user_id_new 為 user_id
        print("🔄 重新命名 user_id_new 為 user_id...")
        cursor.execute("ALTER TABLE users RENAME COLUMN user_id_new TO user_id")
        
        # 3.7 設定 user_id 為 NOT NULL
        print("🔒 設定 user_id 為 NOT NULL...")
        cursor.execute("ALTER TABLE users ALTER COLUMN user_id SET NOT NULL")
        
        # 3.8 重新建立主鍵約束
        print("🔑 重新建立主鍵約束...")
        cursor.execute("ALTER TABLE users ADD PRIMARY KEY (user_id)")
        
        # 4. 處理 user_feedback 表
        print("\n🔄 開始處理 user_feedback 表...")
        
        # 4.1 新增臨時欄位
        print("➕ 新增臨時欄位 user_id_new...")
        cursor.execute("ALTER TABLE user_feedback ADD COLUMN user_id_new VARCHAR(50)")
        
        # 4.2 複製 user_id 到 user_id_new（先轉換為字串）
        print("📋 複製 user_id 到 user_id_new...")
        cursor.execute("""
            UPDATE user_feedback 
            SET user_id_new = user_id::VARCHAR(50)
        """)
        
        # 4.2.1 更新 user_id_new 為對應的 user_code（使用最新備份表）
        print("🔄 更新 user_id_new 為對應的 user_code（使用 users 備份表）...")
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name LIKE 'users_backup_%' 
            ORDER BY table_name DESC LIMIT 1
        """)
        users_backup_table = cursor.fetchone()[0]
        cursor.execute(f'''
            UPDATE user_feedback
            SET user_id_new = u.user_code
            FROM {users_backup_table} u
            WHERE user_feedback.user_id_new = u.user_id::varchar
        ''')
        print(f"✅ user_feedback 表 user_id_new 已依據 {users_backup_table} 完成對應更新")
        # 檢查更新結果
        cursor.execute("SELECT COUNT(*) FROM user_feedback WHERE user_id_new IS NOT NULL")
        updated_feedback_count = cursor.fetchone()[0]
        print(f"✅ user_feedback 表已更新 {updated_feedback_count} 筆記錄")
        # 4.3 檢查複製結果（已在上一步完成）
        
        # 4.4 刪除舊的 user_id 欄位
        print("🗑️  刪除舊的 user_id 欄位...")
        cursor.execute("ALTER TABLE user_feedback DROP COLUMN user_id CASCADE")
        
        # 4.5 重新命名 user_id_new 為 user_id
        print("🔄 重新命名 user_id_new 為 user_id...")
        cursor.execute("ALTER TABLE user_feedback RENAME COLUMN user_id_new TO user_id")
        
        # 4.6 設定 user_id 為 NOT NULL
        print("🔒 設定 user_id 為 NOT NULL...")
        cursor.execute("ALTER TABLE user_feedback ALTER COLUMN user_id SET NOT NULL")
        
        # 5. 重新建立外鍵約束
        if fk_constraints:
            print("\n🔗 重新建立外鍵約束...")
            for constraint in fk_constraints:
                print(f"   - 重建 {constraint[0]}.{constraint[1]} -> users.user_id")
                # 先更新相關表的 user_id 欄位類型
                cursor.execute(f"ALTER TABLE {constraint[0]} ALTER COLUMN {constraint[1]} TYPE VARCHAR(50)")
                # 重新建立外鍵約束
                cursor.execute(f"""
                    ALTER TABLE {constraint[0]} 
                    ADD CONSTRAINT {constraint[4]} 
                    FOREIGN KEY ({constraint[1]}) 
                    REFERENCES users(user_id)
                """)
        
        # 6. 驗證遷移結果
        print("\n🔍 驗證遷移結果...")
        
        # 6.1 檢查 users 表
        cursor.execute("""
            SELECT user_id, username 
            FROM users 
            LIMIT 5
        """)
        users_results = cursor.fetchall()
        print("=== 遷移後的 users 表資料樣本 ===")
        for row in users_results:
            print(f"user_id: {row[0]} (type: {type(row[0])}), username: {row[1]}")

        # 6.2 檢查 user_feedback 表
        cursor.execute("""
            SELECT user_id, episode_id, bookmark, preview_played 
            FROM user_feedback 
            LIMIT 5
        """)
        feedback_results = cursor.fetchall()
        print("\n=== 遷移後的 user_feedback 表資料樣本 ===")
        for row in feedback_results:
            print(f"user_id: {row[0]} (type: {type(row[0])}), episode_id: {row[1]}, bookmark: {row[2]}, preview_played: {row[3]}")
        
        # 7. 提交事務
        conn.commit()
        print("\n✅ 遷移完成！")
        print(f"📋 users 備份表: {users_backup}")
        print(f"📋 user_feedback 備份表: {user_feedback_backup}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise

if __name__ == "__main__":
    print("🚀 開始執行用戶欄位遷移...")
    print("⚠️  此操作將修改資料庫結構，請確保已備份重要資料！")
    
    confirm = input("是否繼續執行遷移？(y/N): ")
    if confirm.lower() == 'y':
        migrate_user_fields()
    else:
        print("❌ 遷移已取消") 