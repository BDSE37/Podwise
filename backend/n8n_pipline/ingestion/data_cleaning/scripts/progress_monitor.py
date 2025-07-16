#!/usr/bin/env python3
"""
批次上傳進度監控腳本
"""

import os
import time
import psycopg2
from pathlib import Path

def check_progress():
    """檢查批次上傳進度"""
    try:
        # 檢查腳本是否還在執行
        import subprocess
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'batch_upload_to_postgres.py' not in result.stdout:
            print("❌ 批次上傳腳本已結束")
            return
        
        # 檢查資料庫中的資料數量
        conn = psycopg2.connect(
            host='postgres.podwise.svc.cluster.local',
            port=5432,
            database='podcast',
            user='bdse37',
            password='111111'
        )
        cursor = conn.cursor()
        
        # 檢查 episodes 數量
        cursor.execute("SELECT COUNT(*) FROM episodes")
        episode_count = cursor.fetchone()[0]
        
        # 檢查 podcasts 數量
        cursor.execute("SELECT COUNT(*) FROM podcasts")
        podcast_count = cursor.fetchone()[0]
        
        # 檢查最近插入的資料
        cursor.execute("""
            SELECT episode_title, created_at 
            FROM episodes 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        recent_episodes = cursor.fetchall()
        
        cursor.execute("""
            SELECT name, created_at 
            FROM podcasts 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        recent_podcasts = cursor.fetchall()
        
        conn.close()
        
        print(f"📊 當前資料庫狀態:")
        print(f"   Episodes: {episode_count} 筆")
        print(f"   Podcasts: {podcast_count} 筆")
        
        print(f"\n📝 最近插入的 Episodes:")
        for title, created_at in recent_episodes:
            print(f"   - {title} ({created_at})")
        
        print(f"\n📝 最近插入的 Podcasts:")
        for name, created_at in recent_podcasts:
            print(f"   - {name} ({created_at})")
        
        # 檢查檔案處理進度
        batch_input_dir = Path(__file__).parent.parent / 'batch_input'
        json_files = list(batch_input_dir.glob('*.json'))
        total_files = len(json_files)
        
        print(f"\n📁 檔案處理進度:")
        print(f"   總檔案數: {total_files}")
        
        # 根據資料庫中的資料量估算進度
        if total_files > 0:
            # 假設每個檔案平均有 500 筆資料
            estimated_total = total_files * 500
            progress = min(100, (episode_count + podcast_count) / estimated_total * 100)
            print(f"   估算進度: {progress:.1f}%")
        
    except Exception as e:
        print(f"❌ 檢查進度失敗: {e}")

def main():
    """主程式"""
    print("=== 批次上傳進度監控 ===")
    while True:
        check_progress()
        print("\n" + "="*50)
        print("按 Ctrl+C 停止監控")
        time.sleep(10)  # 每 10 秒檢查一次

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 監控已停止") 