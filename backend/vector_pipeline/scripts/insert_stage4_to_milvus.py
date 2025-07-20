#!/usr/bin/env python3
"""
Stage4 Embedding Prep 資料插入 Milvus 腳本

功能：
1. 將 stage4_embedding_prep 的 JSON 檔案資料插入到 Milvus 向量資料庫
2. 防止重複插入（檢查 chunk_id）
3. 記錄執行時間
4. 以每個 RSS 資料夾為一個批次單位
5. 錯誤處理和日誌記錄
"""

import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set
import sys

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.milvus_writer import MilvusWriter
from config.config import config
from pymilvus import connections, Collection, utility


class Stage4MilvusInserter:
    """Stage4 資料插入 Milvus 的處理器"""
    
    def __init__(self):
        """初始化插入器"""
        self.milvus_config = config.get_milvus_config()
        self.milvus_writer = MilvusWriter(self.milvus_config)
        self.collection_name = self.milvus_config['collection_name']
        self.stage4_data_path = Path(__file__).parent.parent / "data" / "stage4_embedding_prep"
        
        # 設定日誌
        self._setup_logging()
        
        # 連接到 Milvus
        self._connect_milvus()
        
        # 快取已存在的 chunk_id
        self.existing_chunk_ids = self._get_existing_chunk_ids()
        
    def _setup_logging(self):
        """設定日誌"""
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"stage4_insert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _connect_milvus(self):
        """連接到 Milvus"""
        try:
            self.milvus_writer.connect()
            self.logger.info(f"成功連接到 Milvus: {self.milvus_config['host']}:{self.milvus_config['port']}")
        except Exception as e:
            self.logger.error(f"Milvus 連接失敗: {e}")
            raise
            
    def _get_existing_chunk_ids(self) -> Set[str]:
        """獲取已存在的 chunk_id 集合"""
        try:
            if not utility.has_collection(self.collection_name):
                self.logger.info(f"集合 {self.collection_name} 不存在，將創建新集合")
                return set()
                
            collection = Collection(self.collection_name)
            collection.load()
            
            # 查詢所有 chunk_id
            results = collection.query(
                expr="chunk_id != ''",
                output_fields=["chunk_id"],
                limit=16384  # Milvus 最大查詢限制
            )
            
            existing_ids = {result['chunk_id'] for result in results}
            self.logger.info(f"發現 {len(existing_ids)} 個已存在的 chunk_id")
            return existing_ids
            
        except Exception as e:
            self.logger.warning(f"獲取已存在 chunk_id 失敗: {e}")
            return set()
            
    def _load_json_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """載入 JSON 檔案"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data if isinstance(data, list) else [data]
        except Exception as e:
            self.logger.error(f"載入檔案 {file_path} 失敗: {e}")
            return []
            
    def _validate_data_format(self, data: Dict[str, Any]) -> bool:
        """驗證資料格式是否符合 Milvus schema"""
        required_fields = [
            'chunk_id', 'chunk_index', 'episode_id', 'podcast_id',
            'podcast_name', 'author', 'category', 'episode_title',
            'duration', 'published_date', 'apple_rating', 'chunk_text', 'embedding'
        ]
        
        for field in required_fields:
            if field not in data:
                self.logger.warning(f"缺少必要欄位: {field}")
                return False
                
        # 檢查 embedding 是否為列表
        if not isinstance(data.get('embedding'), list):
            self.logger.warning(f"embedding 格式錯誤: {type(data.get('embedding'))}")
            return False
            
        return True
        
    def _prepare_data_for_insert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """準備資料格式以符合 Milvus 插入要求"""
        # 確保所有必要欄位都存在
        prepared_data = {
            'chunk_id': str(data.get('chunk_id', '')),
            'chunk_index': int(data.get('chunk_index', 0)),
            'episode_id': int(data.get('episode_id', 0)),
            'podcast_id': int(data.get('podcast_id', 0)),
            'podcast_name': str(data.get('podcast_name', '')),
            'author': str(data.get('author', '')),
            'category': str(data.get('category', '')),
            'episode_title': str(data.get('episode_title', '')),
            'duration': str(data.get('duration', '')),
            'published_date': str(data.get('published_date', '')),
            'apple_rating': float(data.get('apple_rating', 0.0)),
            'sentiment_rating': float(data.get('sentiment_rating', 0.0)),
            'total_rating': float(data.get('total_rating', 0.0)),
            'chunk_text': str(data.get('chunk_text', '')),
            'embedding': data.get('embedding', []),
            'language': str(data.get('language', 'zh-TW')),
            'created_at': str(data.get('created_at', datetime.now().isoformat())),
            'source_model': str(data.get('source_model', 'bge-m3')),
            'tags': str(data.get('tags', '[]'))
        }
        
        return prepared_data
        
    def _process_rss_folder(self, rss_folder: Path) -> Dict[str, Any]:
        """處理單個 RSS 資料夾"""
        rss_id = rss_folder.name
        self.logger.info(f"開始處理 RSS 資料夾: {rss_id}")
        
        start_time = time.time()
        total_files = 0
        total_chunks = 0
        inserted_chunks = 0
        skipped_chunks = 0
        error_chunks = 0
        
        # 獲取所有 JSON 檔案
        json_files = list(rss_folder.glob("*.json"))
        self.logger.info(f"發現 {len(json_files)} 個 JSON 檔案")
        
        all_data_to_insert = []
        
        for json_file in json_files:
            file_start_time = time.time()
            self.logger.info(f"處理檔案: {json_file.name}")
            
            # 載入 JSON 資料
            file_data = self._load_json_file(json_file)
            total_files += 1
            
            for chunk_data in file_data:
                total_chunks += 1
                
                try:
                    # 驗證資料格式
                    if not self._validate_data_format(chunk_data):
                        error_chunks += 1
                        continue
                        
                    chunk_id = str(chunk_data.get('chunk_id', ''))
                    
                    # 檢查是否已存在
                    if chunk_id in self.existing_chunk_ids:
                        skipped_chunks += 1
                        continue
                        
                    # 準備資料格式
                    prepared_data = self._prepare_data_for_insert(chunk_data)
                    all_data_to_insert.append(prepared_data)
                    
                except Exception as e:
                    self.logger.error(f"處理 chunk 失敗: {e}")
                    error_chunks += 1
                    
            file_time = time.time() - file_start_time
            self.logger.info(f"檔案 {json_file.name} 處理完成，耗時: {file_time:.2f}秒")
            
        # 批次插入資料
        if all_data_to_insert:
            try:
                insert_start_time = time.time()
                inserted_count = self.milvus_writer.batch_insert(
                    self.collection_name, 
                    all_data_to_insert, 
                    batch_size=100
                )
                inserted_chunks = inserted_count
                insert_time = time.time() - insert_start_time
                
                # 更新已存在的 chunk_id 快取
                for data in all_data_to_insert:
                    self.existing_chunk_ids.add(data['chunk_id'])
                    
                self.logger.info(f"批次插入完成，插入 {inserted_count} 筆資料，耗時: {insert_time:.2f}秒")
                
            except Exception as e:
                self.logger.error(f"批次插入失敗: {e}")
                error_chunks += len(all_data_to_insert)
                
        total_time = time.time() - start_time
        
        result = {
            'rss_id': rss_id,
            'total_files': total_files,
            'total_chunks': total_chunks,
            'inserted_chunks': inserted_chunks,
            'skipped_chunks': skipped_chunks,
            'error_chunks': error_chunks,
            'total_time': total_time
        }
        
        self.logger.info(f"RSS 資料夾 {rss_id} 處理完成:")
        self.logger.info(f"  總檔案數: {total_files}")
        self.logger.info(f"  總 chunk 數: {total_chunks}")
        self.logger.info(f"  插入 chunk 數: {inserted_chunks}")
        self.logger.info(f"  跳過 chunk 數: {skipped_chunks}")
        self.logger.info(f"  錯誤 chunk 數: {error_chunks}")
        self.logger.info(f"  總耗時: {total_time:.2f}秒")
        
        return result
        
    def process_all_stage4_data(self) -> Dict[str, Any]:
        """處理所有 stage4 資料"""
        self.logger.info("開始處理所有 stage4_embedding_prep 資料")
        
        if not self.stage4_data_path.exists():
            raise FileNotFoundError(f"Stage4 資料路徑不存在: {self.stage4_data_path}")
            
        # 獲取所有 RSS 資料夾
        rss_folders = [f for f in self.stage4_data_path.iterdir() if f.is_dir()]
        self.logger.info(f"發現 {len(rss_folders)} 個 RSS 資料夾")
        
        overall_start_time = time.time()
        total_results = []
        
        for rss_folder in rss_folders:
            try:
                result = self._process_rss_folder(rss_folder)
                total_results.append(result)
            except Exception as e:
                self.logger.error(f"處理 RSS 資料夾 {rss_folder.name} 失敗: {e}")
                total_results.append({
                    'rss_id': rss_folder.name,
                    'error': str(e),
                    'total_time': 0
                })
                
        overall_time = time.time() - overall_start_time
        
        # 統計總結果
        total_inserted = sum(r.get('inserted_chunks', 0) for r in total_results)
        total_skipped = sum(r.get('skipped_chunks', 0) for r in total_results)
        total_errors = sum(r.get('error_chunks', 0) for r in total_results)
        
        summary = {
            'total_rss_folders': len(rss_folders),
            'total_inserted_chunks': total_inserted,
            'total_skipped_chunks': total_skipped,
            'total_error_chunks': total_errors,
            'overall_time': overall_time,
            'results': total_results
        }
        
        self.logger.info("=" * 50)
        self.logger.info("整體處理完成:")
        self.logger.info(f"  總 RSS 資料夾數: {len(rss_folders)}")
        self.logger.info(f"  總插入 chunk 數: {total_inserted}")
        self.logger.info(f"  總跳過 chunk 數: {total_skipped}")
        self.logger.info(f"  總錯誤 chunk 數: {total_errors}")
        self.logger.info(f"  總耗時: {overall_time:.2f}秒")
        self.logger.info("=" * 50)
        
        return summary
        
    def close(self):
        """關閉連接"""
        try:
            self.milvus_writer.close()
            self.logger.info("Milvus 連接已關閉")
        except Exception as e:
            self.logger.error(f"關閉連接失敗: {e}")


def main():
    """主函數"""
    print("Stage4 Embedding Prep 資料插入 Milvus 腳本")
    print("=" * 50)
    
    inserter = None
    try:
        inserter = Stage4MilvusInserter()
        summary = inserter.process_all_stage4_data()
        
        # 輸出摘要到檔案
        summary_file = Path(__file__).parent.parent / "logs" / f"stage4_insert_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
            
        print(f"摘要已儲存到: {summary_file}")
        
    except Exception as e:
        print(f"執行失敗: {e}")
        logging.error(f"執行失敗: {e}")
        
    finally:
        if inserter:
            inserter.close()


if __name__ == "__main__":
    main() 