#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MinIO 音檔分析腳本
分析 MinIO 中的音檔與 PostgreSQL 資料庫的對應關係
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd

# 添加後端路徑
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from config.db_config import POSTGRES_CONFIG, MINIO_CONFIG
from minio.api import Minio
import psycopg2
import psycopg2.extras

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MinIOEpisodeAnalyzer:
    """MinIO 音檔分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.minio_client = None
        self.db_connection = None
        self._init_connections()
        
        # 類別配置
        self.category_buckets = {
            "business": "business-one-min-audio",
            "education": "education-one-min-audio"
        }
    
    def _init_connections(self):
        """初始化資料庫和 MinIO 連接"""
        try:
            # 初始化 MinIO 客戶端
            self.minio_client = Minio(
                MINIO_CONFIG["endpoint"],
                access_key=MINIO_CONFIG["access_key"],
                secret_key=MINIO_CONFIG["secret_key"],
                secure=MINIO_CONFIG["secure"]
            )
            logger.info("✅ MinIO 連接成功")
            
        except Exception as e:
            logger.error(f"❌ MinIO 連接失敗: {e}")
            self.minio_client = None
    
    def get_db_connection(self):
        """獲取資料庫連接"""
        try:
            if not self.db_connection or self.db_connection.closed:
                self.db_connection = psycopg2.connect(**POSTGRES_CONFIG)
            return self.db_connection
        except Exception as e:
            logger.error(f"❌ 資料庫連接失敗: {e}")
            return None
    
    def get_podcast_name(self, podcast_id: int) -> str:
        """從資料庫獲取 podcast 名稱"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return f"Podcast_{podcast_id}"
            
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT podcast_name FROM podcasts WHERE podcast_id = %s", 
                    (podcast_id,)
                )
                result = cursor.fetchone()
                return result[0] if result else f"Podcast_{podcast_id}"
                
        except Exception as e:
            logger.error(f"獲取 podcast 名稱失敗: {e}")
            return f"Podcast_{podcast_id}"
    
    def analyze_minio_episodes(self) -> Dict[str, List[Dict]]:
        """分析 MinIO 中的所有音檔"""
        if not self.minio_client:
            logger.error("MinIO 客戶端未初始化")
            return {}
        
        analysis_results = {"business": [], "education": []}
        
        for category, bucket_name in self.category_buckets.items():
            logger.info(f"🔍 分析 {category} 類別，bucket: {bucket_name}")
            
            try:
                # 列出 bucket 中的所有音檔
                objects = list(self.minio_client.list_objects(bucket_name, recursive=True))
                audio_files = [obj.object_name for obj in objects if obj.object_name and obj.object_name.endswith('.mp3')]
                
                logger.info(f"在 {bucket_name} 中找到 {len(audio_files)} 個音檔")
                
                for audio_file in audio_files:
                    try:
                        # 解析音檔名稱：RSS_{podcast_id}_{episode_title}.mp3
                        # 但實際格式可能更複雜，需要更靈活的解析
                        if not audio_file.startswith('RSS_'):
                            logger.warning(f"⚠️ 音檔名稱格式不正確: {audio_file}")
                            continue
                        
                        # 移除 .mp3 後綴
                        filename_without_ext = audio_file.replace('.mp3', '')
                        
                        # 分割檔案名
                        parts = filename_without_ext.split('_')
                        
                        if len(parts) < 3:
                            logger.warning(f"⚠️ 無法解析音檔名稱: {audio_file}")
                            continue
                        
                        # 嘗試提取 podcast_id（第二部分）
                        try:
                            podcast_id = int(parts[1])
                        except ValueError:
                            logger.warning(f"⚠️ 無法解析 podcast_id: {parts[1]} in {audio_file}")
                            continue
                        
                        # 剩餘部分作為 episode_title
                        episode_title = '_'.join(parts[2:])
                        
                        # 從資料庫獲取 podcast_name
                        podcast_name = self.get_podcast_name(podcast_id)
                        
                        # 構建音檔 URL
                        audio_url = self.minio_client.presigned_get_object(
                            bucket_name, audio_file, expires=timedelta(hours=1)
                        )
                        
                        # 構建圖片 URL
                        image_filename = f"RSS_{podcast_id}_300.jpg"
                        image_url = f"http://192.168.32.66:30090/podcast-images/{image_filename}"
                        
                        episode_info = {
                            "podcast_id": podcast_id,
                            "podcast_name": podcast_name,
                            "episode_title": episode_title,
                            "audio_url": audio_url,
                            "image_url": image_url,
                            "minio_filename": audio_file,
                            "category": category,
                            "rss_id": f"RSS_{podcast_id}"
                        }
                        
                        analysis_results[category].append(episode_info)
                        logger.info(f"✅ 載入: {podcast_name} - {episode_title}")
                            
                    except Exception as e:
                        logger.error(f"❌ 處理音檔 {audio_file} 失敗: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"❌ 分析 {category} 類別失敗: {e}")
                continue
        
        return analysis_results
    
    def generate_analysis_report(self) -> str:
        """生成分析報告"""
        logger.info("📊 開始生成 MinIO 音檔分析報告...")
        
        analysis_results = self.analyze_minio_episodes()
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("MINIO 音檔分析報告")
        report_lines.append("=" * 80)
        report_lines.append(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        total_episodes = 0
        
        for category, episodes in analysis_results.items():
            report_lines.append(f"📁 {category.upper()} 類別 (Bucket: {self.category_buckets[category]})")
            report_lines.append("-" * 60)
            report_lines.append(f"音檔數量: {len(episodes)}")
            report_lines.append("")
            
            if episodes:
                # 建立詳細表格
                table_data = []
                for episode in episodes:
                    table_data.append({
                        "Podcast ID": episode['podcast_id'],
                        "Podcast Name": episode['podcast_name'],
                        "Episode Title": episode['episode_title'][:50] + "..." if len(episode['episode_title']) > 50 else episode['episode_title'],
                        "Audio URL": "✅" if episode['audio_url'] else "❌",
                        "Image URL": "✅" if episode['image_url'] else "❌",
                        "MinIO Filename": episode['minio_filename']
                    })
                
                # 轉換為 DataFrame 並格式化輸出
                df = pd.DataFrame(table_data)
                report_lines.append(df.to_string(index=False))
            else:
                report_lines.append("❌ 沒有找到音檔")
            
            report_lines.append("")
            total_episodes += len(episodes)
        
        report_lines.append("=" * 80)
        report_lines.append(f"📈 總計: {total_episodes} 個音檔")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def save_analysis_to_csv(self, output_dir: str = "analysis_output"):
        """將分析結果保存為 CSV 檔案"""
        import os
        
        # 建立輸出目錄
        os.makedirs(output_dir, exist_ok=True)
        
        analysis_results = self.analyze_minio_episodes()
        
        for category, episodes in analysis_results.items():
            if episodes:
                # 建立 DataFrame
                df = pd.DataFrame(episodes)
                
                # 保存為 CSV
                csv_filename = f"{output_dir}/{category}_episodes_analysis.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                logger.info(f"💾 已保存 {category} 類別分析結果到: {csv_filename}")
        
        # 合併所有類別
        all_episodes = []
        for category, episodes in analysis_results.items():
            all_episodes.extend(episodes)
        
        if all_episodes:
            all_df = pd.DataFrame(all_episodes)
            all_csv_filename = f"{output_dir}/all_episodes_analysis.csv"
            all_df.to_csv(all_csv_filename, index=False, encoding='utf-8-sig')
            logger.info(f"💾 已保存所有類別分析結果到: {all_csv_filename}")
    
    def close_connections(self):
        """關閉連接"""
        if self.db_connection:
            self.db_connection.close()

def main():
    """主函數"""
    analyzer = MinIOEpisodeAnalyzer()
    
    try:
        # 生成分析報告
        report = analyzer.generate_analysis_report()
        print(report)
        
        # 保存為 CSV
        analyzer.save_analysis_to_csv()
        
    except Exception as e:
        logger.error(f"分析失敗: {e}")
    finally:
        analyzer.close_connections()

if __name__ == "__main__":
    main() 