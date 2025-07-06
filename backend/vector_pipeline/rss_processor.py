#!/usr/bin/env python3
"""
RSS 處理器
專門處理 MongoDB RSS collections，包含 RSS_1500839292 的例外處理

功能：
1. 從 MongoDB 取得 RSS_XXXXXX collections
2. 使用 data_cleaning 模組進行資料清理
3. 內容以空白或換行切斷
4. 為每個 chunk 提供 1-3 個 TAG
5. 使用 bge-m3 進行 embedding
6. 存入 Milvus
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加父目錄到路徑
sys.path.append(str(Path(__file__).parent.parent))

from vector_pipeline.pipeline_orchestrator import PipelineOrchestrator
from vector_pipeline.core import UnifiedTagManager
from vector_pipeline.error_logger import ErrorLogger

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RSSProcessor:
    """RSS 處理器 - 整合 data_cleaning 清理功能"""
    
    def __init__(self, 
                 mongo_config: Dict[str, Any],
                 postgres_config: Dict[str, Any],
                 milvus_config: Dict[str, Any],
                 tag_csv_path: str = "../rag_pipeline/scripts/csv/TAG_info.csv"):
        """
        初始化 RSS 處理器
        
        Args:
            mongo_config: MongoDB 配置
            postgres_config: PostgreSQL 配置
            milvus_config: Milvus 配置
            tag_csv_path: TAG_info.csv 檔案路徑
        """
        self.mongo_config = mongo_config
        self.postgres_config = postgres_config
        self.milvus_config = milvus_config
        self.tag_csv_path = tag_csv_path
        
        # 初始化統一標籤管理器
        self.tag_manager = UnifiedTagManager(tag_csv_path)
        
        # 初始化 Pipeline Orchestrator
        self.orchestrator = PipelineOrchestrator(
            mongo_config=mongo_config,
            postgres_config=postgres_config,
            milvus_config=milvus_config,
            tag_csv_path=tag_csv_path,
            embedding_model="BAAI/bge-m3",
            max_chunk_size=1024,
            batch_size=50
        )
        
        logger.info("RSS 處理器初始化完成")
    
    def get_rss_collections(self) -> List[str]:
        """
        獲取所有 RSS collections
        
        Returns:
            RSS collections 列表
        """
        try:
            collections = self.orchestrator.mongo_processor.get_collections()
            rss_collections = [col for col in collections if col.startswith('RSS_')]
            
            logger.info(f"找到 {len(rss_collections)} 個 RSS collections: {rss_collections}")
            return rss_collections
            
        except Exception as e:
            logger.error(f"獲取 RSS collections 失敗: {e}")
            return []
    
    def process_rss_collection(self, collection_name: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        處理單個 RSS collection
        
        Args:
            collection_name: Collection 名稱
            limit: 限制處理文檔數量
            
        Returns:
            處理結果統計
        """
        try:
            logger.info(f"開始處理 RSS collection: {collection_name}")
            
            # 檢查是否為 RSS_1500839292（需要例外處理）
            is_special_collection = collection_name == "RSS_1500839292"
            
            if is_special_collection:
                logger.info("檢測到 RSS_1500839292，使用股癌專用清理器")
                return self._process_special_collection(collection_name, limit)
            else:
                logger.info(f"使用標準處理邏輯處理 {collection_name}")
                return self._process_standard_collection(collection_name, limit)
                
        except Exception as e:
            logger.error(f"處理 RSS collection {collection_name} 失敗: {e}")
            return {
                "collection_name": collection_name,
                "status": "failed",
                "error": str(e),
                "processed_documents": 0,
                "processed_chunks": 0
            }
    
    def _process_standard_collection(self, collection_name: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """處理標準 RSS collection"""
        try:
            # 使用標準的 Pipeline Orchestrator 處理
            # MongoDBProcessor 會自動使用適當的清理器
            stats = self.orchestrator.process_collection(
                mongo_collection=collection_name,
                milvus_collection="podcast_chunks",
                limit=limit
            )
            
            return {
                "collection_name": collection_name,
                "status": "success",
                "processed_documents": stats.get("processed_documents", 0),
                "processed_chunks": stats.get("processed_chunks", 0),
                "embedding_model": "BAAI/bge-m3",
                "processing_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"標準處理失敗: {e}")
            raise
    
    def _process_special_collection(self, collection_name: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """處理 RSS_1500839292 特殊 collection"""
        try:
            logger.info("開始特殊處理 RSS_1500839292")
            
            # 獲取文檔（MongoDBProcessor 會自動使用股癌清理器）
            documents = self.orchestrator.mongo_processor.process_collection(
                collection_name, 
                limit=limit
            )
            
            processed_documents = 0
            processed_chunks = 0
            
            for doc in documents:
                try:
                    # 處理文檔（清理已在 process_collection 中完成）
                    chunk_count = self.orchestrator.process_single_document(doc)
                    
                    if chunk_count > 0:
                        processed_documents += 1
                        processed_chunks += chunk_count
                        logger.info(f"處理文檔 {doc.episode_id}: {chunk_count} chunks")
                    
                except Exception as e:
                    logger.error(f"處理文檔 {doc.episode_id} 失敗: {e}")
                    continue
            
            return {
                "collection_name": collection_name,
                "status": "success",
                "processed_documents": processed_documents,
                "processed_chunks": processed_chunks,
                "embedding_model": "BAAI/bge-m3",
                "processing_time": datetime.now().isoformat(),
                "special_processing": True
            }
            
        except Exception as e:
            logger.error(f"特殊處理失敗: {e}")
            raise
    
    def process_all_rss_collections(self, limit_per_collection: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        處理所有 RSS collections
        
        Args:
            limit_per_collection: 每個 collection 的限制數量
            
        Returns:
            所有處理結果
        """
        try:
            rss_collections = self.get_rss_collections()
            
            if not rss_collections:
                logger.warning("沒有找到任何 RSS collections")
                return []
            
            all_results = []
            error_logger = ErrorLogger()
            
            for collection_name in rss_collections:
                try:
                    logger.info(f"開始處理 collection: {collection_name}")
                    result = self.process_rss_collection(collection_name, limit_per_collection)
                    all_results.append(result)
                    
                    logger.info(f"Collection {collection_name} 處理完成: {result}")
                    
                except Exception as e:
                    logger.error(f"處理 collection {collection_name} 失敗: {e}")
                    
                    # 提取 RSS ID
                    rss_id = self._extract_rss_id_from_collection(collection_name)
                    
                    # 記錄錯誤
                    error_logger.add_error(
                        collection_id=collection_name,
                        rss_id=rss_id,
                        title=f"Collection: {collection_name}",
                        error_type="collection_processing_error",
                        error_message=str(e),
                        error_details=f"Collection: {collection_name}, RSS_ID: {rss_id}",
                        processing_stage="collection_processing"
                    )
                    
                    # 添加失敗結果但繼續處理下一個
                    all_results.append({
                        "collection_name": collection_name,
                        "status": "failed",
                        "error": str(e),
                        "processed_documents": 0,
                        "processed_chunks": 0,
                        "rss_id": rss_id
                    })
            
            # 儲存錯誤報告
            if error_logger.errors:
                error_reports = error_logger.save_errors()
                csv_report = error_logger.save_csv_report()
                logger.warning(f"處理過程中發現 {len(error_logger.errors)} 個錯誤")
                logger.warning(f"JSON 錯誤報告: {error_reports}")
                logger.warning(f"CSV 錯誤報告: {csv_report}")
                
                # 輸出錯誤摘要
                self._print_error_summary(error_logger)
            
            return all_results
            
        except Exception as e:
            logger.error(f"處理所有 RSS collections 失敗: {e}")
            return []
    
    def _extract_rss_id_from_collection(self, collection_name: str) -> str:
        """從 collection 名稱提取 RSS ID"""
        import re
        match = re.search(r'RSS_(\d+)', collection_name)
        return match.group(1) if match else ""
    
    def _print_error_summary(self, error_logger: ErrorLogger) -> None:
        """輸出錯誤摘要"""
        try:
            summary = error_logger.get_error_summary()
            
            print("\n" + "="*80)
            print("🚨 錯誤處理摘要")
            print("="*80)
            print(f"📊 總錯誤數: {summary['total_errors']}")
            print(f"📁 受影響的 Collections: {summary['collections_affected']}")
            print(f"🔧 處理階段: {', '.join(summary['processing_stages'])}")
            
            if summary['error_types']:
                print("\n📋 錯誤類型統計:")
                for error_type, count in summary['error_types'].items():
                    print(f"   • {error_type}: {count} 個")
            
            # 顯示前 10 個錯誤的 RSS_ID 和標題
            if error_logger.errors:
                print("\n📝 錯誤檔案清單 (前 10 個):")
                for i, error in enumerate(error_logger.errors[:10]):
                    print(f"   {i+1}. RSS_{error.rss_id} - {error.title}")
                
                if len(error_logger.errors) > 10:
                    print(f"   ... 還有 {len(error_logger.errors) - 10} 個錯誤")
            
            print("="*80)
            
        except Exception as e:
            logger.error(f"輸出錯誤摘要失敗: {e}")
    
    def get_error_report(self) -> Dict[str, Any]:
        """獲取錯誤報告"""
        try:
            error_logger = ErrorLogger()
            summary = error_logger.get_error_summary()
            
            # 獲取錯誤檔案清單
            error_files = []
            for error in error_logger.errors:
                error_files.append({
                    "rss_id": error.rss_id,
                    "title": error.title,
                    "collection_id": error.collection_id,
                    "error_type": error.error_type,
                    "processing_stage": error.processing_stage,
                    "timestamp": error.timestamp
                })
            
            return {
                "summary": summary,
                "error_files": error_files,
                "total_error_files": len(error_files)
            }
            
        except Exception as e:
            logger.error(f"獲取錯誤報告失敗: {e}")
            return {}
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """獲取處理統計資訊"""
        try:
            rss_collections = self.get_rss_collections()
            
            stats = {
                "total_rss_collections": len(rss_collections),
                "rss_collections": rss_collections,
                "tag_manager_status": self.tag_manager.get_extractor_status(),
                "embedding_model": "BAAI/bge-m3",
                "max_chunk_size": 1024,
                "special_collections": ["RSS_1500839292"],
                "data_cleaning_integration": True
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"獲取統計資訊失敗: {e}")
            return {}
    
    def close(self) -> None:
        """關閉連接"""
        try:
            if self.orchestrator:
                self.orchestrator.close()
            logger.info("RSS 處理器已關閉")
        except Exception as e:
            logger.error(f"關閉 RSS 處理器失敗: {e}")


def main():
    """主函數"""
    # 配置
    mongo_config = {
        "host": "192.168.32.86",
        "port": 30017,
        "username": "bdse37",
        "password": "111111",
        "database": "podcast"
    }
    
    postgres_config = {
        "host": "192.168.32.56",
        "port": 32432,
        "database": "podcast",
        "user": "bdse37",
        "password": "111111"
    }
    
    milvus_config = {
        "host": "192.168.32.86",
        "port": "19530",
        "collection_name": "podcast_chunks",
        "dim": 1024,
        "index_type": "IVF_FLAT",
        "metric_type": "L2",
        "params": {"nlist": 1024}
    }
    
    try:
        # 創建 RSS 處理器
        processor = RSSProcessor(mongo_config, postgres_config, milvus_config)
        
        # 獲取統計資訊
        stats = processor.get_processing_statistics()
        logger.info(f"RSS 處理統計: {stats}")
        
        # 處理所有 RSS collections
        results = processor.process_all_rss_collections(limit_per_collection=None)
        
        # 輸出結果
        print("\n" + "="*80)
        print("RSS Collections 處理結果")
        print("="*80)
        
        total_processed = 0
        total_chunks = 0
        
        for result in results:
            print(f"\n📋 Collection: {result['collection_name']}")
            print(f"   Status: {result['status']}")
            
            if result['status'] == 'success':
                print(f"   📄 處理文檔: {result.get('processed_documents', 0)}")
                print(f"   🧩 處理 Chunks: {result.get('processed_chunks', 0)}")
                print(f"   🔧 特殊處理: {result.get('special_processing', False)}")
                
                total_processed += result.get('processed_documents', 0)
                total_chunks += result.get('processed_chunks', 0)
            else:
                print(f"   ❌ 錯誤: {result.get('error', 'Unknown error')}")
        
        print(f"\n📊 總計:")
        print(f"   📄 總處理文檔: {total_processed}")
        print(f"   🧩 總處理 Chunks: {total_chunks}")
        print(f"   🏗️  嵌入模型: BAAI/bge-m3")
        print(f"   🧹 資料清理: 整合 data_cleaning 模組")
        print("="*80)
        
    except Exception as e:
        logger.error(f"主程序執行失敗: {e}")
        raise
    finally:
        # 關閉處理器
        if 'processor' in locals():
            processor.close()


if __name__ == "__main__":
    main() 