#!/usr/bin/env python3
"""
優化最終版本：
- 不 preload 全量 chunk_id，避免 offset+limit 限制
- 每次檔案處理時，僅針對該檔案的 chunk_id 用 query `in` 檢查
- 高效安全，適合大量檔案和大量資料
"""
import sys
import os
import json
import glob
import time
from typing import List, Dict, Any, Set
from pymilvus import connections, Collection
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BatchMilvusInserter:
    def __init__(self, base_path: str, batch_size: int = 100):
        self.base_path = base_path
        self.batch_size = batch_size
        self.exceptions_file = os.path.join(os.path.dirname(__file__), "exceptions.json")
        self.exceptions_data = []
        self.milvus_config = {
            "host": "192.168.32.86",
            "port": "19530"
        }
        self.collection = None

    def load_exceptions(self):
        if os.path.exists(self.exceptions_file):
            with open(self.exceptions_file, 'r', encoding='utf-8') as f:
                self.exceptions_data = json.load(f)
        else:
            self.exceptions_data = []

    def save_exceptions(self):
        with open(self.exceptions_file, 'w', encoding='utf-8') as f:
            json.dump(self.exceptions_data, f, ensure_ascii=False, indent=2)

    def add_exception(self, file_path: str, chunk_data: Dict[str, Any], reason: str):
        exception_record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "chunk_id": chunk_data.get("chunk_id", "N/A"),
            "file_path": file_path,
            "reason": reason,
            "chunk_text_length": len(chunk_data.get("chunk_text", "")),
            "data": chunk_data
        }
        self.exceptions_data.append(exception_record)
        self.save_exceptions()

    def connect(self):
        connections.connect(alias="default", host="192.168.32.86", port="19530")
        self.collection = Collection("podcast_chunks")
        self.collection.load()
        logger.info("成功連接並載入 Milvus collection")

    def find_json_files(self) -> List[str]:
        pattern = os.path.join(self.base_path, "**/*.json")
        files = [f for f in glob.glob(pattern, recursive=True) if not f.endswith('.backup')]
        logger.info(f"找到 {len(files)} 個 JSON 檔案於 {self.base_path}")
        return files

    def load_json_file(self, file_path: str) -> List[Dict[str, Any]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"載入檔案失敗 {file_path}: {e}")
            return []

    def chunk_ids_exist(self, chunk_ids: List[str]) -> Set[str]:
        if not chunk_ids:
            return set()
        ids_expr = ", ".join([f'\"{id_}\"' for id_ in chunk_ids])
        expr = f"chunk_id in [{ids_expr}]"
        try:
            res = self.collection.query(expr, output_fields=["chunk_id"])
            return set(r["chunk_id"] for r in res)
        except Exception as e:
            logger.error(f"Milvus query 出錯: {e}")
            return set()

    def insert_batch(self, file_path: str, batch: List[Dict[str, Any]]) -> int:
        chunk_ids = [d.get("chunk_id") for d in batch]
        existing_ids = self.chunk_ids_exist(chunk_ids)

        valid_batch = []
        for d in batch:
            chunk_id = d.get("chunk_id")
            chunk_text = d.get("chunk_text", "")
            if len(chunk_text) > 1024:
                self.add_exception(file_path, d, f"chunk_text 長度 {len(chunk_text)} 超過 1024")
                continue
            if chunk_id in existing_ids:
                self.add_exception(file_path, d, f"chunk_id {chunk_id} 已存在於 Milvus 中")
                continue
            valid_batch.append(d)

        if not valid_batch:
            return 0

        try:
            insert_data = [
                [d.get("chunk_id") for d in valid_batch],
                [d.get("chunk_index", 0) for d in valid_batch],
                [d.get("episode_id", 0) for d in valid_batch],
                [d.get("podcast_id", 0) for d in valid_batch],
                [d.get("podcast_name", "") for d in valid_batch],
                [d.get("author", "") for d in valid_batch],
                [d.get("category", "") for d in valid_batch],
                [d.get("episode_title", "") for d in valid_batch],
                [d.get("duration", "") for d in valid_batch],
                [d.get("published_date", "") for d in valid_batch],
                [d.get("apple_rating", 0) for d in valid_batch],
                [d.get("sentiment_rating", 0) for d in valid_batch],
                [d.get("total_rating", 0) for d in valid_batch],
                [d.get("chunk_text", "") for d in valid_batch],
                [d.get("embedding", [0.0] * 1024) for d in valid_batch],
                [d.get("language", "") for d in valid_batch],
                [d.get("created_at", "") for d in valid_batch],
                [d.get("source_model", "") for d in valid_batch],
                [d.get("tags", "") for d in valid_batch]
            ]
            self.collection.insert(insert_data)
            return len(valid_batch)
        except Exception as e:
            logger.error(f"批次 insert 失敗: {e}")
            for d in valid_batch:
                self.add_exception(file_path, d, f"批次 insert 失敗: {e}")
            return 0

    def run(self):
        self.load_exceptions()
        self.connect()
        json_files = self.find_json_files()
        for file_path in tqdm(json_files, desc="處理檔案"):
            records = self.load_json_file(file_path)
            if not records:
                continue
            inserted = 0
            for i in range(0, len(records), self.batch_size):
                batch = records[i:i + self.batch_size]
                inserted += self.insert_batch(file_path, batch)
            logger.info(f"檔案 {file_path} 插入 {inserted} 筆資料")
        logger.info("✅ 所有檔案處理完畢！")

if __name__ == "__main__":
    inserter = BatchMilvusInserter(base_path="backend/vector_pipeline/data/stage4_embedding_prep")
    inserter.run()