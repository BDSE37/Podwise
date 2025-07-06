#!/usr/bin/env python3
"""
資料庫連線測試腳本
測試 PostgreSQL 連線並查詢 episodes 表格
"""

import psycopg2
import sys
from config import config


def test_connection():
    """測試資料庫連線"""
    print("=== 測試 PostgreSQL 連線 ===")
    
    try:
        # 取得連線參數
        conn_params = config.get_connection_params()
        print(f"連線參數: {conn_params}")
        
        # 建立連線
        conn = psycopg2.connect(**conn_params)
        print("✅ 資料庫連線成功！")
        
        # 建立游標
        cursor = conn.cursor()
        
        # 查詢 episodes 表格結構
        print("\n=== 查詢 episodes 表格結構 ===")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'episodes' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("episodes 表格欄位:")
        for col in columns:
            print(f"  {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
        
        # 查詢現有資料數量
        print("\n=== 查詢現有資料 ===")
        cursor.execute("SELECT COUNT(*) FROM episodes;")
        count = cursor.fetchone()[0]
        print(f"episodes 表格現有記錄數: {count}")
        
        # 查詢範例資料
        if count > 0:
            cursor.execute("SELECT episode_id, episode_title, published_date FROM episodes LIMIT 3;")
            samples = cursor.fetchall()
            print("範例資料:")
            for sample in samples:
                print(f"  ID: {sample[0]}, 標題: {sample[1]}, 日期: {sample[2]}")
        
        # 查詢 podcasts 表格（確認 podcast_id 對應）
        print("\n=== 查詢 podcasts 表格 ===")
        cursor.execute("SELECT podcast_id, title FROM podcasts LIMIT 5;")
        podcasts = cursor.fetchall()
        print("現有 podcasts:")
        for podcast in podcasts:
            print(f"  ID: {podcast[0]}, 標題: {podcast[1]}")
        
        cursor.close()
        conn.close()
        print("\n✅ 測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 連線失敗: {e}")
        return False


def test_episode_processing():
    """測試 episode 處理功能"""
    print("\n=== 測試 Episode 處理 ===")
    
    try:
        from episode_processor import EpisodeProcessor
        
        processor = EpisodeProcessor()
        
        # 測試資料
        test_episode = {
            "id": "test_001",
            "title": "EP001 | AI智慧工廠的天時地利人和即將到來？！🚀",
            "published": "Wed, 25 Jun 2025 04:32:47 GMT",
            "description": "<p>(01:40) Jeff與JJ的第一個交集：上市公司91-APP掛牌與投資小故事 <br /> <br />IG:final36x <br />Powered by <a href=\"https://firstory.me/zh\">Firstory Hosting</a></p>",
            "audio_url": "https://example.com/audio.mp3"
        }
        
        channel_info = {
            'channel_id': '1304',
            'channel_name': '商業頻道',
            'category': 'business'
        }
        
        # 處理測試資料
        processed = processor.process_episode_data(test_episode, channel_info)
        
        print("處理結果:")
        for key, value in processed.items():
            print(f"  {key}: {value}")
        
        print("✅ Episode 處理測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ Episode 處理測試失敗: {e}")
        return False


def main():
    """主函數"""
    print("PostgreSQL 資料庫連線與 Episode 處理測試")
    print("=" * 50)
    
    # 測試連線
    connection_ok = test_connection()
    
    if connection_ok:
        # 測試處理功能
        processing_ok = test_episode_processing()
        
        if processing_ok:
            print("\n🎉 所有測試通過！可以開始處理 episodes 資料。")
        else:
            print("\n⚠️ 處理功能測試失敗，請檢查程式碼。")
    else:
        print("\n❌ 資料庫連線失敗，請檢查連線設定。")
        sys.exit(1)


if __name__ == "__main__":
    main() 