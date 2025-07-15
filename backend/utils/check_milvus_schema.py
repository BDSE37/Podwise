#!/usr/bin/env python3
"""
檢查 Milvus 資料庫 schema
"""

import os
from pymilvus import connections, Collection, utility
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_milvus_schema():
    """檢查 Milvus schema"""
    try:
        # 連線設定
        host = "192.168.32.86"
        user = "bdse37"
        password = "111111"
        collection_name = "podcast_chunks"
        
        # 嘗試連線
        ports = [19530, 9091, 9000]
        connected = False
        
        for port in ports:
            try:
                logger.info(f"嘗試連線 Milvus: {host}:{port}")
                connections.connect(
                    alias="default",
                    host=host,
                    port=port,
                    user=user,
                    password=password
                )
                
                # 測試連線
                utility.list_collections()
                logger.info(f"✅ 成功連線 Milvus: {host}:{port}")
                connected = True
                break
                
            except Exception as e:
                logger.warning(f"Port {port} 連線失敗: {str(e)}")
                continue
        
        if not connected:
            logger.error("❌ 無法連線 Milvus")
            return None
        
        # 檢查 collection 是否存在
        if not utility.has_collection(collection_name):
            logger.error(f"❌ Collection '{collection_name}' 不存在")
            return None
        
        # 載入 collection
        collection = Collection(collection_name)
        collection.load()
        
        # 取得 schema
        schema = collection.schema
        
        logger.info("="*80)
        logger.info("📋 Milvus Collection Schema 詳細資訊")
        logger.info("="*80)
        
        # 顯示 collection 資訊
        logger.info(f"Collection 名稱: {collection.name}")
        logger.info(f"Collection 描述: {collection.description}")
        logger.info(f"Collection 實體數量: {collection.num_entities}")
        
        # 顯示所有欄位定義
        logger.info("\n📊 欄位定義:")
        logger.info("-" * 80)
        
        for field in schema.fields:
            logger.info(f"欄位名稱: {field.name}")
            logger.info(f"  資料型態: {field.dtype}")
            logger.info(f"  是否為主鍵: {field.is_primary}")
            logger.info(f"  是否為自動 ID: {field.auto_id}")
            logger.info(f"  描述: {field.description}")
            
            # 如果是 VARCHAR 型態，顯示最大長度
            if hasattr(field, 'params') and field.params:
                for param_name, param_value in field.params.items():
                    logger.info(f"  參數 {param_name}: {param_value}")
            
            logger.info("-" * 40)
        
        # 顯示索引資訊
        logger.info("\n🔍 索引資訊:")
        logger.info("-" * 80)
        
        try:
            index_info = collection.index()
            logger.info(f"索引類型: {index_info.params}")
        except Exception as e:
            logger.warning(f"無法取得索引資訊: {str(e)}")
        
        # 顯示分區資訊
        logger.info("\n📦 分區資訊:")
        logger.info("-" * 80)
        
        try:
            partitions = collection.partitions
            for partition in partitions:
                logger.info(f"分區名稱: {partition.name}")
                logger.info(f"  描述: {partition.description}")
        except Exception as e:
            logger.warning(f"無法取得分區資訊: {str(e)}")
        
        # 建立完整的 schema 字典
        schema_dict = {
            'collection_name': collection.name,
            'description': collection.description,
            'num_entities': collection.num_entities,
            'fields': []
        }
        
        for field in schema.fields:
            field_info = {
                'name': field.name,
                'dtype': str(field.dtype),
                'is_primary': field.is_primary,
                'auto_id': field.auto_id,
                'description': field.description,
                'params': {}
            }
            
            if hasattr(field, 'params') and field.params:
                field_info['params'] = dict(field.params)
            
            schema_dict['fields'].append(field_info)
        
        logger.info("\n" + "="*80)
        logger.info("✅ Schema 檢查完成")
        logger.info("="*80)
        
        return schema_dict
        
    except Exception as e:
        logger.error(f"❌ 檢查 schema 失敗: {str(e)}")
        return None

def save_schema_to_file(schema_dict, filename="milvus_schema.json"):
    """儲存 schema 到檔案"""
    try:
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(schema_dict, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Schema 已儲存至: {filename}")
    except Exception as e:
        logger.error(f"❌ 儲存 schema 失敗: {str(e)}")

if __name__ == "__main__":
    schema = check_milvus_schema()
    if schema:
        save_schema_to_file(schema) 