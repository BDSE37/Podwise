#!/usr/bin/env python3
"""
自動化批次處理腳本
處理所有 MongoDB collections，切分為 chunks，貼標籤，向量化後存入 podcast_chunks
包含異常處理、重複資料檢查、進度記錄

遵循 Google Clean Code Style 和 OOP 原則
"""

import logging
import sys
import time
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from tqdm import tqdm
from abc import ABC, abstractmethod

# 添加父目錄到路徑
sys.path.append(str(Path(__file__).parent))

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_process.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    """處理統計資料"""
    collection_name: str
    total_documents: int
    processed_documents: int
    failed_documents: int
    total_chunks: int
    processed_chunks: int
    failed_chunks: int
    start_time: datetime
    end_time: Optional[datetime] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    @property
    def duration(self) -> float:
        """處理時間（秒）"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_documents == 0:
            return 0.0
        return (self.processed_documents / self.total_documents) * 100


class ProgressManager(ABC):
    """進度管理器抽象類別"""
    
    @abstractmethod
    def load_progress(self) -> Dict[str, Any]:
        """載入進度記錄"""
        pass
    
    @abstractmethod
    def save_progress(self, **kwargs) -> None:
        """儲存進度記錄"""
        pass
    
    @abstractmethod
    def mark_collection_completed(self, collection_name: str) -> None:
        """標記 collection 完成"""
        pass


class FileProgressManager(ProgressManager):
    """檔案型進度管理器"""
    
    def __init__(self, progress_file: str = "batch_progress.json"):
        self.progress_file = progress_file
        self.progress = self.load_progress()
    
    def load_progress(self) -> Dict[str, Any]:
        """載入進度記錄"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                    logger.info(f"📋 載入進度記錄: {progress}")
                    return progress
            except Exception as e:
                logger.warning(f"載入進度記錄失敗: {e}")
        
        # 預設進度
        return {
            "last_processed_collection": None,
            "last_processed_doc": None,
            "completed_collections": [],
            "total_processed_chunks": 0,
            "start_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
            "cycle_count": 0,
            "current_cycle": 0
        }
    
    def save_progress(self, **kwargs) -> None:
        """儲存進度記錄"""
        try:
            for key, value in kwargs.items():
                if key in self.progress:
                    self.progress[key] = value
            
            self.progress["last_update"] = datetime.now().isoformat()
            
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, ensure_ascii=False, indent=2)
                
            logger.debug(f"💾 進度已儲存: {self.progress}")
        except Exception as e:
            logger.error(f"儲存進度失敗: {e}")
    
    def mark_collection_completed(self, collection_name: str) -> None:
        """標記 collection 完成"""
        if collection_name not in self.progress["completed_collections"]:
            self.progress["completed_collections"].append(collection_name)
            self.save_progress()
            logger.info(f"✅ Collection {collection_name} 已標記為完成")
    
    def should_skip_collection(self, collection_name: str) -> bool:
        """檢查是否應該跳過 collection"""
        return collection_name in self.progress["completed_collections"]
    
    def get_current_cycle(self) -> int:
        """獲取當前循環數"""
        return self.progress.get("current_cycle", 0)
    
    def increment_cycle(self) -> None:
        """增加循環數"""
        self.progress["current_cycle"] = self.progress.get("current_cycle", 0) + 1
        self.progress["cycle_count"] = self.progress.get("cycle_count", 0) + 1
        self.save_progress()


class MetadataValidator:
    """Metadata 驗證器"""
    
    @staticmethod
    def is_metadata_complete(metadata) -> bool:
        """檢查 metadata 完整性"""
        try:
            # 檢查必需欄位（除了 tag 欄位外）
            required_fields = [
                'episode_id',
                'podcast_id', 
                'episode_title',
                'podcast_name',
                'author',
                'category'
            ]
            
            for field in required_fields:
                value = getattr(metadata, field, None)
                if value is None or (isinstance(value, str) and not value.strip()):
                    logger.warning(f"metadata 欄位 {field} 為空或 None")
                    return False
            
            # 檢查 episode_id 和 podcast_id 不為 0
            if metadata.episode_id == 0 or metadata.podcast_id == 0:
                logger.warning(f"episode_id 或 podcast_id 為 0")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"檢查 metadata 完整性失敗: {e}")
            return False


class CollectionProcessor:
    """Collection 處理器"""
    
    def __init__(self, orchestrator, progress_manager: ProgressManager):
        self.orchestrator = orchestrator
        self.progress_manager = progress_manager
        self.processed_chunks = set()
        self.metadata_validator = MetadataValidator()
    
    def process_collection(self, collection_name: str, limit: Optional[int] = None) -> ProcessingStats:
        """處理單個 collection"""
        logger.info(f"🔄 開始處理 collection: {collection_name}")
        
        # 檢查是否已完成
        if self.progress_manager.should_skip_collection(collection_name):
            logger.info(f"⏭️ 跳過已完成的 collection: {collection_name}")
            return ProcessingStats(
                collection_name=collection_name,
                total_documents=0,
                processed_documents=0,
                failed_documents=0,
                total_chunks=0,
                processed_chunks=0,
                failed_chunks=0,
                start_time=datetime.now()
            )
        
        # 獲取總文檔數
        total_docs = self.orchestrator.mongo_processor.get_document_count(collection_name)
        if limit:
            total_docs = min(total_docs, limit)
        
        logger.info(f"📊 Collection {collection_name} 總文檔數: {total_docs}")
        
        # 建立統計物件
        stats = ProcessingStats(
            collection_name=collection_name,
            total_documents=total_docs,
            processed_documents=0,
            failed_documents=0,
            total_chunks=0,
            processed_chunks=0,
            failed_chunks=0,
            start_time=datetime.now()
        )
        
        batch_size = 50  # 批次大小
        
        try:
            # 建立進度條
            with tqdm(total=total_docs, desc=f"處理 {collection_name}", unit="文檔") as pbar:
                for offset in range(0, total_docs, batch_size):
                    current_batch_size = min(batch_size, total_docs - offset)
                    
                    try:
                        # 獲取批次文檔
                        docs = self.orchestrator.mongo_processor.fetch_documents(
                            collection_name, 
                            limit=current_batch_size
                        )
                        
                        # 處理每個文檔
                        for doc in docs:
                            self._process_single_document(doc, stats, pbar)
                        
                        # 批次間隔
                        time.sleep(1)
                        
                    except Exception as e:
                        error_msg = f"批次處理異常: {str(e)}"
                        stats.errors.append(error_msg)
                        logger.error(f"❌ {error_msg}")
                        
                        # 儲存進度
                        self.progress_manager.save_progress(
                            last_processed_collection=collection_name
                        )
                        
                        # 如果是嚴重錯誤，中止處理
                        if "metadata" in str(e).lower():
                            raise e
            
            # 標記 collection 完成
            self.progress_manager.mark_collection_completed(collection_name)
            logger.info(f"✅ Collection {collection_name} 處理完成")
            
        except Exception as e:
            logger.error(f"❌ 處理 collection {collection_name} 時發生嚴重錯誤: {e}")
            # 儲存進度
            self.progress_manager.save_progress(
                last_processed_collection=collection_name
            )
            raise
        
        return stats
    
    def _process_single_document(self, doc, stats: ProcessingStats, pbar: tqdm) -> None:
        """處理單個文檔"""
        try:
            # 檢查是否已處理過
            if doc.file in self.processed_chunks:
                logger.debug(f"⏭️ 跳過已處理文檔: {doc.file}")
                pbar.update(1)
                return
            
            # 檢查是否有 metadata（沒有則中止程式）
            metadata = self.orchestrator._get_episode_metadata(doc)
            if not metadata:
                error_msg = f"❌ 文檔無 metadata，程式中止: {doc.file}"
                logger.error(error_msg)
                stats.errors.append(error_msg)
                raise Exception(error_msg)
            
            # 檢查 metadata 完整性（除了 tag 欄位外，其他欄位都要有值）
            if not self.metadata_validator.is_metadata_complete(metadata):
                error_msg = f"❌ metadata 不完整，程式中止: {doc.file}"
                logger.error(error_msg)
                stats.errors.append(error_msg)
                raise Exception(error_msg)
            
            # 處理文檔（切分、標籤、向量化、寫入）
            chunk_count = self.orchestrator.process_single_document(doc)
            
            if chunk_count > 0:
                # 更新統計
                stats.processed_documents += 1
                stats.processed_chunks += chunk_count
                
                # 標記文檔已處理
                self.processed_chunks.add(doc.file)
                
                # 儲存進度（每個文檔處理完後立即儲存）
                self.progress_manager.save_progress(
                    last_processed_collection=stats.collection_name,
                    last_processed_doc=doc.file,
                    total_processed_chunks=self.progress_manager.progress["total_processed_chunks"] + chunk_count
                )
                
                logger.info(f"✅ 文檔處理完成: {doc.file} -> {chunk_count} chunks")
            else:
                stats.failed_documents += 1
                error_msg = f"文檔處理失敗，無 chunks 產生: {doc.file}"
                stats.errors.append(error_msg)
                logger.warning(f"⚠️ {error_msg}")
            
            # 更新進度條
            pbar.set_postfix({
                '成功': stats.processed_documents,
                '失敗': stats.failed_documents,
                'chunks': stats.processed_chunks
            })
            pbar.update(1)
            
        except Exception as e:
            error_msg = f"處理文檔 {doc.file} 時發生錯誤: {str(e)}"
            stats.errors.append(error_msg)
            stats.failed_documents += 1
            logger.error(f"❌ {error_msg}")
            
            # 儲存進度（即使失敗也要儲存）
            self.progress_manager.save_progress(
                last_processed_collection=stats.collection_name,
                last_processed_doc=doc.file
            )
            
            pbar.set_postfix({
                '成功': stats.processed_documents,
                '失敗': stats.failed_documents,
                'chunks': stats.processed_chunks
            })
            pbar.update(1)
            
            # 如果是嚴重錯誤（如 metadata 問題），中止處理
            if "metadata" in str(e).lower():
                raise e


class BatchProcessor:
    """批次處理器 - 遵循 Google Clean Code Style"""
    
    def __init__(self, mongo_config: Dict[str, Any], 
                 postgres_config: Dict[str, Any], 
                 milvus_config: Dict[str, Any],
                 collections_per_cycle: int = 5):
        """
        初始化批次處理器
        
        Args:
            mongo_config: MongoDB 配置
            postgres_config: PostgreSQL 配置  
            milvus_config: Milvus 配置
            collections_per_cycle: 每個循環處理的 collections 數量
        """
        self.mongo_config = mongo_config
        self.postgres_config = postgres_config
        self.milvus_config = milvus_config
        self.collections_per_cycle = collections_per_cycle
        
        self.orchestrator = None
        self.progress_manager = FileProgressManager()
        self.collection_processor = None
        
    def initialize(self) -> bool:
        """初始化所有組件"""
        try:
            from vector_pipeline.pipeline_orchestrator import PipelineOrchestrator
            
            self.orchestrator = PipelineOrchestrator(
                mongo_config=self.mongo_config,
                postgres_config=self.postgres_config,
                milvus_config=self.milvus_config,
                max_chunk_size=500,
                batch_size=50
            )
            
            self.collection_processor = CollectionProcessor(
                self.orchestrator, 
                self.progress_manager
            )
            
            logger.info("✅ 批次處理器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 批次處理器初始化失敗: {e}")
            return False
    
    def process_collections_in_cycles(self, limit_per_collection: Optional[int] = None) -> List[ProcessingStats]:
        """按循環處理 collections"""
        if not self.initialize():
            return []
        
        try:
            # 獲取所有 collections
            collections = self.orchestrator.mongo_processor.get_collection_names()
            logger.info(f"📋 找到 {len(collections)} 個 collections: {collections}")
            
            all_stats = []
            current_cycle = self.progress_manager.get_current_cycle()
            
            # 計算當前循環應該處理的 collections
            start_index = current_cycle * self.collections_per_cycle
            end_index = min(start_index + self.collections_per_cycle, len(collections))
            
            current_collections = collections[start_index:end_index]
            
            logger.info(f"🔄 開始處理循環 {current_cycle + 1}")
            logger.info(f"📊 本循環處理 collections: {current_collections}")
            
            # 建立整體進度條
            with tqdm(total=len(current_collections), desc=f"循環 {current_cycle + 1}", unit="collection") as pbar:
                for i, collection_name in enumerate(current_collections, 1):
                    logger.info(f"🔄 處理進度: {i}/{len(current_collections)} - {collection_name}")
                    
                    stats = self.collection_processor.process_collection(collection_name, limit_per_collection)
                    all_stats.append(stats)
                    
                    # 輸出統計資訊
                    self.print_stats(stats)
                    
                    # 更新進度條
                    pbar.update(1)
                    pbar.set_postfix({
                        '當前': collection_name,
                        '成功文檔': sum(s.processed_documents for s in all_stats),
                        '總chunks': sum(s.processed_chunks for s in all_stats)
                    })
                    
                    # 集合間隔
                    if i < len(current_collections):
                        logger.info("⏳ 等待 3 秒後處理下一個 collection...")
                        time.sleep(3)
            
            # 增加循環計數
            self.progress_manager.increment_cycle()
            
            # 輸出總體統計
            self.print_cycle_stats(all_stats, current_cycle + 1)
            
            return all_stats
            
        except Exception as e:
            logger.error(f"❌ 批次處理失敗: {e}")
            return []
        
        finally:
            if self.orchestrator:
                self.orchestrator.close()
    
    def process_all_collections(self, limit_per_collection: Optional[int] = None) -> List[ProcessingStats]:
        """處理所有 collections（一次性處理）"""
        if not self.initialize():
            return []
        
        try:
            # 獲取所有 collections
            collections = self.orchestrator.mongo_processor.get_collection_names()
            logger.info(f"📋 找到 {len(collections)} 個 collections: {collections}")
            
            all_stats = []
            
            # 建立整體進度條
            with tqdm(total=len(collections), desc="處理 Collections", unit="collection") as pbar:
                for i, collection_name in enumerate(collections, 1):
                    logger.info(f"🔄 處理進度: {i}/{len(collections)} - {collection_name}")
                    
                    stats = self.collection_processor.process_collection(collection_name, limit_per_collection)
                    all_stats.append(stats)
                    
                    # 輸出統計資訊
                    self.print_stats(stats)
                    
                    # 更新進度條
                    pbar.update(1)
                    pbar.set_postfix({
                        '當前': collection_name,
                        '成功文檔': sum(s.processed_documents for s in all_stats),
                        '總chunks': sum(s.processed_chunks for s in all_stats)
                    })
                    
                    # 集合間隔
                    if i < len(collections):
                        logger.info("⏳ 等待 5 秒後處理下一個 collection...")
                        time.sleep(5)
            
            # 輸出總體統計
            self.print_overall_stats(all_stats)
            
            return all_stats
            
        except Exception as e:
            logger.error(f"❌ 批次處理失敗: {e}")
            return []
        
        finally:
            if self.orchestrator:
                self.orchestrator.close()
    
    def print_stats(self, stats: ProcessingStats) -> None:
        """輸出單個 collection 統計"""
        print(f"\n📊 Collection: {stats.collection_name}")
        print(f"  📄 文檔: {stats.processed_documents}/{stats.total_documents} ({stats.success_rate:.1f}%)")
        print(f"  🧩 Chunks: {stats.processed_chunks}/{stats.total_chunks}")
        print(f"  ⏱️ 時間: {stats.duration:.1f} 秒")
        if stats.errors:
            print(f"  ❌ 錯誤: {len(stats.errors)} 個")
    
    def print_cycle_stats(self, all_stats: List[ProcessingStats], cycle_number: int) -> None:
        """輸出循環統計"""
        print(f"\n" + "=" * 80)
        print(f"🎯 循環 {cycle_number} 統計")
        print("=" * 80)
        
        total_docs = sum(s.total_documents for s in all_stats)
        processed_docs = sum(s.processed_documents for s in all_stats)
        total_chunks = sum(s.total_chunks for s in all_stats)
        processed_chunks = sum(s.processed_chunks for s in all_stats)
        total_errors = sum(len(s.errors) for s in all_stats)
        total_time = sum(s.duration for s in all_stats)
        
        print(f"📋 Collections: {len(all_stats)}")
        print(f"📄 總文檔: {processed_docs}/{total_docs} ({(processed_docs/total_docs*100):.1f}%)")
        print(f"🧩 總 Chunks: {processed_chunks}/{total_chunks}")
        print(f"⏱️ 總時間: {total_time:.1f} 秒")
        print(f"❌ 總錯誤: {total_errors}")
        
        # 保存統計到檔案
        self.save_stats_to_file(all_stats, f"cycle_{cycle_number}")
    
    def print_overall_stats(self, all_stats: List[ProcessingStats]) -> None:
        """輸出總體統計"""
        print("\n" + "=" * 80)
        print("🎯 總體處理統計")
        print("=" * 80)
        
        total_docs = sum(s.total_documents for s in all_stats)
        processed_docs = sum(s.processed_documents for s in all_stats)
        total_chunks = sum(s.total_chunks for s in all_stats)
        processed_chunks = sum(s.processed_chunks for s in all_stats)
        total_errors = sum(len(s.errors) for s in all_stats)
        total_time = sum(s.duration for s in all_stats)
        
        print(f"📋 Collections: {len(all_stats)}")
        print(f"📄 總文檔: {processed_docs}/{total_docs} ({(processed_docs/total_docs*100):.1f}%)")
        print(f"🧩 總 Chunks: {processed_chunks}/{total_chunks}")
        print(f"⏱️ 總時間: {total_time:.1f} 秒")
        print(f"❌ 總錯誤: {total_errors}")
        
        # 保存統計到檔案
        self.save_stats_to_file(all_stats, "overall")
    
    def save_stats_to_file(self, all_stats: List[ProcessingStats], suffix: str = "") -> None:
        """保存統計到檔案"""
        try:
            stats_data = {
                "timestamp": datetime.now().isoformat(),
                "collections": [asdict(stats) for stats in all_stats]
            }
            
            filename = f"batch_process_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{suffix}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(stats_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"📁 統計已保存到: {filename}")
            
        except Exception as e:
            logger.error(f"❌ 保存統計失敗: {e}")


def main():
    """主函數"""
    print("🚀 開始自動化批次處理 MongoDB collections（循環模式 + 斷點續傳）")
    print("=" * 80)
    print("💡 提示：按 Ctrl+C 可隨時停止執行，下次會從中斷處繼續")
    print("💡 每 5 個 collections 為一個循環，自動儲存進度")
    print("=" * 80)
    
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
    
    # 創建批次處理器
    processor = BatchProcessor(mongo_config, postgres_config, milvus_config, collections_per_cycle=5)
    
    if processor.initialize():
        collections = processor.orchestrator.mongo_processor.get_collection_names()
        if collections:
            print(f"\n📋 總共有 {len(collections)} 個 collections")
            print(f"📋 Collections: {collections}")
            
            # 顯示進度資訊
            progress = processor.progress_manager.progress
            if progress["completed_collections"]:
                print(f"\n📊 進度資訊:")
                print(f"   ✅ 已完成 collections: {len(progress['completed_collections'])}")
                print(f"   📄 已處理 chunks: {progress['total_processed_chunks']:,}")
                print(f"   🔄 已完成循環: {progress.get('cycle_count', 0)}")
                print(f"   🕐 開始時間: {progress['start_time']}")
                print(f"   🔄 上次更新: {progress['last_update']}")
                
                if progress["last_processed_collection"]:
                    print(f"   📍 上次處理: {progress['last_processed_collection']}")
                
                # 詢問是否從頭開始
                print(f"\n❓ 是否要從頭開始重新處理？(y/N): ", end="")
                try:
                    choice = input().strip().lower()
                    if choice == 'y':
                        print("🧹 清空進度記錄，從頭開始...")
                        processor.progress_manager.progress = {
                            "last_processed_collection": None,
                            "last_processed_doc": None,
                            "completed_collections": [],
                            "total_processed_chunks": 0,
                            "start_time": datetime.now().isoformat(),
                            "last_update": datetime.now().isoformat(),
                            "cycle_count": 0,
                            "current_cycle": 0
                        }
                        processor.progress_manager.save_progress()
                        
                        # 清空 Milvus 集合
                        print(f"🧹 清空 Milvus 集合 podcast_chunks...")
                        try:
                            processor.orchestrator.milvus_writer.clear_collection("podcast_chunks")
                            print("✅ Milvus 集合已清空")
                        except Exception as e:
                            print(f"⚠️  清空集合失敗（可能集合不存在）: {e}")
                            try:
                                processor.orchestrator.milvus_writer.create_collection("podcast_chunks")
                                print("✅ 重新創建 Milvus 集合")
                            except Exception as e2:
                                print(f"❌ 創建集合失敗: {e2}")
                                return
                    else:
                        print("🔄 從上次中斷處繼續執行...")
                except KeyboardInterrupt:
                    print("\n⏹️  使用者取消")
                    return
            else:
                # 第一次執行，清空 Milvus 集合
                print(f"\n🧹 清空 Milvus 集合 podcast_chunks...")
                try:
                    processor.orchestrator.milvus_writer.clear_collection("podcast_chunks")
                    print("✅ Milvus 集合已清空")
                except Exception as e:
                    print(f"⚠️  清空集合失敗（可能集合不存在）: {e}")
                    try:
                        processor.orchestrator.milvus_writer.create_collection("podcast_chunks")
                        print("✅ 重新創建 Milvus 集合")
                    except Exception as e2:
                        print(f"❌ 創建集合失敗: {e2}")
                        return
            
            print(f"\n🚀 開始循環處理 collections...")
            
            try:
                # 詢問處理模式
                print(f"\n❓ 選擇處理模式:")
                print(f"   1. 循環模式（每 5 個 collections 一個循環）")
                print(f"   2. 一次性處理所有 collections")
                print(f"請選擇 (1/2): ", end="")
                
                choice = input().strip()
                
                if choice == "1":
                    print("🔄 使用循環模式...")
                    all_stats = processor.process_collections_in_cycles(limit=None)
                else:
                    print("🚀 使用一次性處理模式...")
                    all_stats = processor.process_all_collections(limit=None)
                
                # 輸出總體統計
                if all_stats:
                    processor.print_overall_stats(all_stats)
                    
            except KeyboardInterrupt:
                print(f"\n⏹️  使用者中斷執行")
                print(f"💾 進度已儲存，下次可從中斷處繼續")
        else:
            print("❌ 找不到任何 collection")
    else:
        print("❌ 批次處理器初始化失敗！")
    
    print("\n" + "=" * 80)
    print("🎉 批次處理完成！")


if __name__ == "__main__":
    main() 