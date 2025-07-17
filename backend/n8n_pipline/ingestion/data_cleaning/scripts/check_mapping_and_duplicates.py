#!/usr/bin/env python3
"""
檢查 PostgreSQL 欄位 mapping 和重複插入問題
確保 JSON 資料正確對應到資料庫欄位，並避免重複插入
"""

import os
import sys
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import traceback

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MappingAndDuplicateChecker:
    """檢查欄位 mapping 和重複插入的類別"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化資料庫連接
        
        Args:
            config: 資料庫配置
        """
        self.config = config
        self.conn = None
        self._connect()
    
    def _connect(self):
        """建立資料庫連接"""
        try:
            self.conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            logger.info("PostgreSQL 連接成功")
            
        except Exception as e:
            logger.error(f"資料庫連接失敗: {e}")
            raise
    
    def get_table_columns(self, table_name: str) -> Dict[str, dict]:
        """獲取表格欄位資訊
        
        Args:
            table_name: 表格名稱
            
        Returns:
            欄位資訊字典
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    ORDER BY ordinal_position
                """, (table_name,))
                
                columns = {}
                for row in cursor.fetchall():
                    columns[row[0]] = {
                        'type': row[1],
                        'nullable': row[2] == 'YES',
                        'default': row[3]
                    }
                return columns
                
        except Exception as e:
            logger.error(f"獲取表格欄位失敗: {e}")
            raise
    
    def get_primary_keys(self, table_name: str) -> List[str]:
        """獲取表格主鍵
        
        Args:
            table_name: 表格名稱
            
        Returns:
            主鍵欄位列表
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.key_column_usage
                    WHERE table_name = %s AND constraint_name LIKE '%%_pkey'
                    ORDER BY ordinal_position
                """, (table_name,))
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"獲取主鍵失敗: {e}")
            raise
    
    def check_existing_records(self, table_name: str, key_field: str, key_values: List[Any]) -> Set[Any]:
        """檢查已存在的記錄
        
        Args:
            table_name: 表格名稱
            key_field: 主鍵欄位
            key_values: 要檢查的鍵值列表
            
        Returns:
            已存在的鍵值集合
        """
        try:
            with self.conn.cursor() as cursor:
                placeholders = ','.join(['%s'] * len(key_values))
                cursor.execute(f"""
                    SELECT {key_field}
                    FROM {table_name}
                    WHERE {key_field} IN ({placeholders})
                """, key_values)
                
                return {row[0] for row in cursor.fetchall()}
                
        except Exception as e:
            logger.error(f"檢查現有記錄失敗: {e}")
            raise
    
    def analyze_podcast_mapping(self, json_file_path: str) -> Dict[str, Any]:
        """分析 Podcast JSON 檔案的欄位 mapping
        
        Args:
            json_file_path: JSON 檔案路徑
            
        Returns:
            分析結果
        """
        try:
            logger.info(f"分析 Podcast 檔案: {json_file_path}")
            
            # 讀取 JSON 檔案
            with open(json_file_path, 'r', encoding='utf-8') as f:
                podcast_data = json.load(f)
            
            # 獲取資料庫欄位資訊
            db_columns = self.get_table_columns('podcasts')
            primary_keys = self.get_primary_keys('podcasts')
            
            # 分析欄位 mapping
            json_fields = set(podcast_data.keys())
            db_fields = set(db_columns.keys())
            
            # 計算對應關係
            mapped_fields = json_fields.intersection(db_fields)
            unmapped_json_fields = json_fields - db_fields
            missing_db_fields = db_fields - json_fields
            
            # 檢查主鍵
            podcast_id = podcast_data.get('id')
            if podcast_id:
                existing_ids = self.check_existing_records('podcasts', 'podcast_id', [int(podcast_id)])
                is_duplicate = int(podcast_id) in existing_ids
            else:
                is_duplicate = False
                existing_ids = set()
            
            return {
                'file_path': json_file_path,
                'podcast_id': podcast_id,
                'is_duplicate': is_duplicate,
                'existing_ids': list(existing_ids),
                'mapping_analysis': {
                    'total_json_fields': len(json_fields),
                    'total_db_fields': len(db_fields),
                    'mapped_fields': len(mapped_fields),
                    'unmapped_json_fields': list(unmapped_json_fields),
                    'missing_db_fields': list(missing_db_fields),
                    'field_mapping': {
                        'mapped': list(mapped_fields),
                        'unmapped': list(unmapped_json_fields)
                    }
                },
                'primary_keys': primary_keys,
                'sample_data': {
                    'title': podcast_data.get('title'),
                    'provider': podcast_data.get('provider'),
                    'rating': podcast_data.get('rating'),
                    'category': podcast_data.get('category')
                }
            }
            
        except Exception as e:
            logger.error(f"分析 Podcast 檔案失敗: {json_file_path} - {e}")
            return {
                'file_path': json_file_path,
                'error': str(e),
                'trace': traceback.format_exc()
            }
    
    def analyze_rss_mapping(self, json_file_path: str) -> Dict[str, Any]:
        """分析 RSS JSON 檔案的欄位 mapping
        
        Args:
            json_file_path: JSON 檔案路徑
            
        Returns:
            分析結果
        """
        try:
            logger.info(f"分析 RSS 檔案: {json_file_path}")
            
            # 讀取 JSON 檔案
            with open(json_file_path, 'r', encoding='utf-8') as f:
                episodes_data = json.load(f)
            
            if not isinstance(episodes_data, list):
                return {
                    'file_path': json_file_path,
                    'error': 'RSS 檔案格式錯誤，應該是陣列格式'
                }
            
            # 獲取資料庫欄位資訊
            db_columns = self.get_table_columns('episodes')
            primary_keys = self.get_primary_keys('episodes')
            
            # 分析第一個 episode 的欄位 mapping
            if episodes_data:
                first_episode = episodes_data[0]
                json_fields = set(first_episode.keys())
                db_fields = set(db_columns.keys())
                
                mapped_fields = json_fields.intersection(db_fields)
                unmapped_json_fields = json_fields - db_fields
                missing_db_fields = db_fields - json_fields
            else:
                mapped_fields = set()
                unmapped_json_fields = set()
                missing_db_fields = set()
                json_fields = set()
                db_fields = set(db_columns.keys())
            
            # 檢查重複的 episodes
            episode_titles = [ep.get('title', '') for ep in episodes_data if ep.get('title')]
            existing_titles = self.check_existing_records('episodes', 'episode_title', episode_titles)
            
            duplicate_titles = set(episode_titles).intersection(existing_titles)
            
            return {
                'file_path': json_file_path,
                'total_episodes': len(episodes_data),
                'duplicate_analysis': {
                    'total_titles': len(episode_titles),
                    'existing_titles': len(existing_titles),
                    'duplicate_titles': len(duplicate_titles),
                    'duplicate_list': list(duplicate_titles)[:10]  # 只顯示前10個
                },
                'mapping_analysis': {
                    'total_json_fields': len(json_fields),
                    'total_db_fields': len(db_fields),
                    'mapped_fields': len(mapped_fields),
                    'unmapped_json_fields': list(unmapped_json_fields),
                    'missing_db_fields': list(missing_db_fields),
                    'field_mapping': {
                        'mapped': list(mapped_fields),
                        'unmapped': list(unmapped_json_fields)
                    }
                },
                'primary_keys': primary_keys,
                'sample_episode': episodes_data[0] if episodes_data else None
            }
            
        except Exception as e:
            logger.error(f"分析 RSS 檔案失敗: {json_file_path} - {e}")
            return {
                'file_path': json_file_path,
                'error': str(e),
                'trace': traceback.format_exc()
            }
    
    def check_batch_input_folder(self, input_folder: str) -> Dict[str, Any]:
        """檢查整個 batch_input 資料夾
        
        Args:
            input_folder: 輸入資料夾路徑
            
        Returns:
            檢查結果摘要
        """
        logger.info(f"開始檢查資料夾: {input_folder}")
        
        if not os.path.exists(input_folder):
            return {"error": "資料夾不存在"}
        
        json_files = [f for f in os.listdir(input_folder) if f.endswith('.json')]
        logger.info(f"找到 {len(json_files)} 個 JSON 檔案")
        
        results = {
            'podcasts': [],
            'rss_files': [],
            'summary': {
                'total_files': len(json_files),
                'podcast_files': 0,
                'rss_files': 0,
                'duplicates_found': 0,
                'mapping_issues': 0
            }
        }
        
        for filename in json_files:
            file_path = os.path.join(input_folder, filename)
            
            if filename.startswith('podcast_'):
                result = self.analyze_podcast_mapping(file_path)
                results['podcasts'].append(result)
                results['summary']['podcast_files'] += 1
                
                if result.get('is_duplicate'):
                    results['summary']['duplicates_found'] += 1
                if result.get('mapping_analysis', {}).get('unmapped_json_fields'):
                    results['summary']['mapping_issues'] += 1
                    
            elif filename.startswith('RSS_') or filename.startswith('Spotify_RSS_'):
                result = self.analyze_rss_mapping(file_path)
                results['rss_files'].append(result)
                results['summary']['rss_files'] += 1
                
                if result.get('duplicate_analysis', {}).get('duplicate_titles'):
                    results['summary']['duplicates_found'] += 1
                if result.get('mapping_analysis', {}).get('unmapped_json_fields'):
                    results['summary']['mapping_issues'] += 1
            else:
                logger.warning(f"跳過未知格式檔案: {filename}")
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """生成檢查報告
        
        Args:
            results: 檢查結果
            
        Returns:
            報告文字
        """
        report = []
        report.append("=" * 60)
        report.append("PostgreSQL 欄位 Mapping 和重複檢查報告")
        report.append("=" * 60)
        
        # 摘要
        summary = results.get('summary', {})
        report.append(f"\n📊 摘要統計:")
        report.append(f"   - 總檔案數: {summary.get('total_files', 0)}")
        report.append(f"   - Podcast 檔案: {summary.get('podcast_files', 0)}")
        report.append(f"   - RSS 檔案: {summary.get('rss_files', 0)}")
        report.append(f"   - 發現重複: {summary.get('duplicates_found', 0)}")
        report.append(f"   - Mapping 問題: {summary.get('mapping_issues', 0)}")
        
        # Podcast 檔案分析
        if results.get('podcasts'):
            report.append(f"\n🎙️ Podcast 檔案分析:")
            for podcast in results['podcasts']:
                if 'error' in podcast:
                    report.append(f"   ❌ {Path(podcast['file_path']).name}: {podcast['error']}")
                    continue
                
                report.append(f"   📁 {Path(podcast['file_path']).name}:")
                report.append(f"      - Podcast ID: {podcast.get('podcast_id', 'N/A')}")
                report.append(f"      - 重複檢查: {'❌ 重複' if podcast.get('is_duplicate') else '✅ 新記錄'}")
                
                mapping = podcast.get('mapping_analysis', {})
                report.append(f"      - 欄位對應: {mapping.get('mapped_fields', 0)}/{mapping.get('total_json_fields', 0)}")
                
                if mapping.get('unmapped_json_fields'):
                    report.append(f"      - 未對應欄位: {', '.join(mapping['unmapped_json_fields'][:5])}")
                    if len(mapping['unmapped_json_fields']) > 5:
                        report.append(f"        ... 還有 {len(mapping['unmapped_json_fields']) - 5} 個欄位")
        
        # RSS 檔案分析
        if results.get('rss_files'):
            report.append(f"\n📻 RSS 檔案分析:")
            for rss in results['rss_files']:
                if 'error' in rss:
                    report.append(f"   ❌ {Path(rss['file_path']).name}: {rss['error']}")
                    continue
                
                report.append(f"   📁 {Path(rss['file_path']).name}:")
                report.append(f"      - Episode 數量: {rss.get('total_episodes', 0)}")
                
                duplicate_analysis = rss.get('duplicate_analysis', {})
                report.append(f"      - 重複標題: {duplicate_analysis.get('duplicate_titles', 0)}")
                
                mapping = rss.get('mapping_analysis', {})
                report.append(f"      - 欄位對應: {mapping.get('mapped_fields', 0)}/{mapping.get('total_json_fields', 0)}")
                
                if mapping.get('unmapped_json_fields'):
                    report.append(f"      - 未對應欄位: {', '.join(mapping['unmapped_json_fields'][:5])}")
                    if len(mapping['unmapped_json_fields']) > 5:
                        report.append(f"        ... 還有 {len(mapping['unmapped_json_fields']) - 5} 個欄位")
        
        # 建議
        report.append(f"\n💡 建議:")
        if summary.get('duplicates_found', 0) > 0:
            report.append("   - 發現重複記錄，建議使用 UPSERT 操作")
        if summary.get('mapping_issues', 0) > 0:
            report.append("   - 發現未對應欄位，請檢查欄位名稱是否正確")
        if summary.get('total_files', 0) == 0:
            report.append("   - 沒有找到 JSON 檔案，請檢查資料夾路徑")
        
        report.append("\n" + "=" * 60)
        return "\n".join(report)
    
    def close(self):
        """關閉資料庫連接"""
        if self.conn:
            self.conn.close()
            logger.info("資料庫連接已關閉")

def main():
    """主程式"""
    logger.info("=== PostgreSQL 欄位 Mapping 和重複檢查 ===")
    
    # 資料庫配置
    config = {
        'host': os.getenv('POSTGRES_HOST', 'postgres.podwise.svc.cluster.local'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'podcast'),
        'user': os.getenv('POSTGRES_USER', 'bdse37'),
        'password': os.getenv('POSTGRES_PASSWORD', '111111')
    }
    
    # 輸入資料夾路徑
    input_folder = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'batch_input'
    )
    
    try:
        # 建立檢查器
        checker = MappingAndDuplicateChecker(config)
        
        # 執行檢查
        results = checker.check_batch_input_folder(input_folder)
        
        # 生成報告
        report = checker.generate_report(results)
        print(report)
        
        # 儲存報告到檔案
        report_file = os.path.join(os.path.dirname(input_folder), 'mapping_check_report.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"檢查報告已儲存到: {report_file}")
        
        # 關閉連接
        checker.close()
        
    except Exception as e:
        logger.error(f"檢查失敗: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 