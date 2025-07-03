# embedding_data_loader.py
# 此模組用於連接 PostgreSQL 並擷取 transcripts 表中的資料

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict

def load_episode_transcripts(conn_str: str, min_length: int = 30) -> List[Dict]:
    """
    從 transcripts 表中載入滿足長度條件的節目資料。

    參數:
    - conn_str: PostgreSQL 的連線字串
    - min_length: 最小 transcript 長度過濾

    回傳:
    - List[Dict]：包含 episode_id、transcript_path、language 等欄位的列表
    """
    try:
        conn = psycopg2.connect(conn_str, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT episode_id, transcript_path, transcript_length, language
            FROM transcripts
            WHERE transcript_length > %s
        """, (min_length,))
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"PostgreSQL 查詢失敗：{e}")
        return []
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()