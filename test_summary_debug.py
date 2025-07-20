#!/usr/bin/env python3
"""
測試摘要查詢流程的調試腳本
"""

import asyncio
import sys
import os

# 添加 backend 目錄到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_summary_flow():
    """測試摘要查詢流程"""
    try:
        from rag_pipeline.tools.cross_db_text_fetcher import get_cross_db_text_fetcher
        
        print("🚀 開始測試摘要查詢流程")
        print("=" * 50)
        
        # 獲取文本擷取器
        fetcher = get_cross_db_text_fetcher()
        
        # 連接資料庫
        print("📡 連接資料庫...")
        if not await fetcher.connect_databases():
            print("❌ 資料庫連接失敗")
            return
        
        print("✅ 資料庫連接成功")
        
        # 測試參數
        podcast_tag = "股癌"
        episode_tag = "EP117"
        
        print(f"🔍 測試參數: podcast_tag='{podcast_tag}', episode_tag='{episode_tag}'")
        print("=" * 50)
        
        # 執行查詢
        result = await fetcher.fetch_text(podcast_tag, episode_tag)
        
        print(f"📊 查詢結果:")
        print(f"   成功: {result.success}")
        print(f"   處理時間: {result.processing_time:.3f} 秒")
        
        if result.success:
            print(f"   Podcast ID: {result.podcast_id}")
            print(f"   Episode Title: {result.episode_title}")
            print(f"   文本長度: {len(result.text)} 字元")
            print(f"   文本預覽: {result.text[:200]}...")
        else:
            print(f"   ❌ 錯誤訊息: {result.error_message}")
        
        # 關閉連接
        fetcher.close_connections()
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_summary_flow()) 