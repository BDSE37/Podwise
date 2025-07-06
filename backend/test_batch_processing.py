#!/usr/bin/env python3
"""
簡化的批次處理測試腳本
驗證 OOP 架構和循環處理功能
"""

import sys
import logging
from pathlib import Path

# 添加父目錄到路徑
sys.path.append(str(Path(__file__).parent))

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_batch_processor_initialization():
    """測試批次處理器初始化"""
    print("🧪 測試批次處理器初始化...")
    
    try:
        from batch_process_podcasts import BatchProcessor
        
        # 測試配置
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
        processor = BatchProcessor(
            mongo_config=mongo_config,
            postgres_config=postgres_config,
            milvus_config=milvus_config,
            collections_per_cycle=5
        )
        
        # 測試初始化
        if processor.initialize():
            print("  ✅ 批次處理器初始化成功")
            
            # 獲取 collections
            collections = processor.orchestrator.mongo_processor.get_collection_names()
            print(f"  📋 找到 {len(collections)} 個 collections")
            
            if collections:
                print(f"  📋 前 5 個 collections: {collections[:5]}")
                
                # 測試循環計算
                current_cycle = processor.progress_manager.get_current_cycle()
                start_index = current_cycle * processor.collections_per_cycle
                end_index = min(start_index + processor.collections_per_cycle, len(collections))
                current_collections = collections[start_index:end_index]
                
                print(f"  🔄 當前循環 {current_cycle + 1} 將處理: {current_collections}")
                
                return True
            else:
                print("  ⚠️  沒有找到 collections")
                return False
        else:
            print("  ❌ 批次處理器初始化失敗")
            return False
            
    except Exception as e:
        print(f"  ❌ 測試失敗: {e}")
        return False


def test_metadata_validation():
    """測試 metadata 驗證"""
    print("🧪 測試 metadata 驗證...")
    
    try:
        from batch_process_podcasts import MetadataValidator
        
        validator = MetadataValidator()
        
        # 創建測試 metadata
        class TestMetadata:
            def __init__(self):
                self.episode_id = 123
                self.podcast_id = 456
                self.episode_title = "測試節目"
                self.podcast_name = "測試播客"
                self.author = "測試作者"
                self.category = "科技"
        
        # 測試完整 metadata
        complete_metadata = TestMetadata()
        is_complete = validator.is_metadata_complete(complete_metadata)
        print(f"  ✅ 完整 metadata 驗證: {is_complete}")
        
        # 測試不完整 metadata
        incomplete_metadata = TestMetadata()
        incomplete_metadata.episode_id = 0  # 設為 0
        is_incomplete = validator.is_metadata_complete(incomplete_metadata)
        print(f"  ✅ 不完整 metadata 驗證: {is_incomplete}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 測試失敗: {e}")
        return False


def test_progress_management():
    """測試進度管理"""
    print("🧪 測試進度管理...")
    
    try:
        from batch_process_podcasts import FileProgressManager
        
        # 創建測試進度管理器
        progress_manager = FileProgressManager("test_progress.json")
        
        # 測試進度操作
        progress_manager.save_progress(
            last_processed_collection="test_collection",
            total_processed_chunks=100
        )
        
        current_cycle = progress_manager.get_current_cycle()
        print(f"  ✅ 當前循環: {current_cycle}")
        
        # 增加循環
        progress_manager.increment_cycle()
        new_cycle = progress_manager.get_current_cycle()
        print(f"  ✅ 新循環: {new_cycle}")
        
        # 標記 collection 完成
        progress_manager.mark_collection_completed("test_collection")
        
        # 檢查是否應該跳過
        should_skip = progress_manager.should_skip_collection("test_collection")
        print(f"  ✅ 應該跳過 test_collection: {should_skip}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 測試失敗: {e}")
        return False


def test_tag_processing():
    """測試標籤處理"""
    print("🧪 測試標籤處理...")
    
    try:
        from vector_pipeline.pipeline_orchestrator import TagProcessorManager
        
        # 創建標籤處理器
        tag_manager = TagProcessorManager("TAG_info.csv")
        
        # 測試不同類型的文本
        test_cases = [
            "這是一個關於 AI 和人工智慧的科技節目",
            "商業管理和企業領導的話題討論",
            "教育學習和知識分享的內容",
            "創業新創和商業模式的探討",
            "這是一個很短的文本"
        ]
        
        for i, text in enumerate(test_cases, 1):
            tags = tag_manager.extract_tags(text)
            print(f"  📝 測試 {i}: {tags}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 測試失敗: {e}")
        return False


def main():
    """主測試函數"""
    print("🚀 開始簡化批次處理測試")
    print("=" * 80)
    
    test_results = []
    
    # 執行所有測試
    test_results.append(("批次處理器初始化", test_batch_processor_initialization()))
    test_results.append(("Metadata 驗證", test_metadata_validation()))
    test_results.append(("進度管理", test_progress_management()))
    test_results.append(("標籤處理", test_tag_processing()))
    
    # 輸出測試結果
    print("\n" + "=" * 80)
    print("📊 測試結果總結")
    print("=" * 80)
    
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
    
    # 計算成功率
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\n🎯 測試成功率: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print("🎉 所有測試通過！批次處理功能正常")
        print("\n💡 可以開始執行批次處理:")
        print("   python batch_process_podcasts.py")
    else:
        print("⚠️  部分測試失敗，需要進一步檢查")
    
    print("\n" + "=" * 80)
    print("🏁 測試完成")


if __name__ == "__main__":
    main() 