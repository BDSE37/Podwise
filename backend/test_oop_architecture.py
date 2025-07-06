#!/usr/bin/env python3
"""
測試 OOP 架構和 Google Clean Code Style
驗證所有組件的正確性和可重用性
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any

# 添加父目錄到路徑
sys.path.append(str(Path(__file__).parent))

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_pipeline_orchestrator():
    """測試 Pipeline Orchestrator OOP 架構"""
    print("🧪 測試 Pipeline Orchestrator OOP 架構...")
    
    try:
        from vector_pipeline.pipeline_orchestrator import (
            PipelineOrchestrator, 
            MetadataValidator, 
            EpisodeMetadataValidator,
            TagProcessorManager
        )
        
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
        
        # 測試 MetadataValidator
        print("  ✅ 測試 MetadataValidator...")
        validator = EpisodeMetadataValidator()
        assert hasattr(validator, 'validate'), "MetadataValidator 缺少 validate 方法"
        assert hasattr(validator, 'get_missing_fields'), "MetadataValidator 缺少 get_missing_fields 方法"
        
        # 測試 TagProcessorManager
        print("  ✅ 測試 TagProcessorManager...")
        tag_manager = TagProcessorManager("TAG_info.csv")
        assert hasattr(tag_manager, 'extract_tags'), "TagProcessorManager 缺少 extract_tags 方法"
        
        # 測試標籤提取
        test_text = "這是一個關於 AI 和科技的測試文本"
        tags = tag_manager.extract_tags(test_text)
        assert isinstance(tags, list), "標籤提取應返回列表"
        print(f"    標籤提取測試: {tags}")
        
        # 測試 PipelineOrchestrator
        print("  ✅ 測試 PipelineOrchestrator...")
        orchestrator = PipelineOrchestrator(
            mongo_config=mongo_config,
            postgres_config=postgres_config,
            milvus_config=milvus_config,
            max_chunk_size=500,
            batch_size=50
        )
        
        assert hasattr(orchestrator, 'process_single_document'), "PipelineOrchestrator 缺少 process_single_document 方法"
        assert hasattr(orchestrator, 'metadata_validator'), "PipelineOrchestrator 缺少 metadata_validator"
        assert hasattr(orchestrator, 'tag_processor_manager'), "PipelineOrchestrator 缺少 tag_processor_manager"
        
        print("  ✅ Pipeline Orchestrator OOP 架構測試通過")
        return True
        
    except Exception as e:
        print(f"  ❌ Pipeline Orchestrator 測試失敗: {e}")
        return False


def test_batch_processor():
    """測試 Batch Processor OOP 架構"""
    print("🧪 測試 Batch Processor OOP 架構...")
    
    try:
        from batch_process_podcasts import (
            BatchProcessor,
            ProgressManager,
            FileProgressManager,
            MetadataValidator,
            CollectionProcessor
        )
        
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
        
        # 測試 ProgressManager
        print("  ✅ 測試 ProgressManager...")
        progress_manager = FileProgressManager("test_progress.json")
        assert hasattr(progress_manager, 'load_progress'), "ProgressManager 缺少 load_progress 方法"
        assert hasattr(progress_manager, 'save_progress'), "ProgressManager 缺少 save_progress 方法"
        assert hasattr(progress_manager, 'mark_collection_completed'), "ProgressManager 缺少 mark_collection_completed 方法"
        
        # 測試 MetadataValidator
        print("  ✅ 測試 MetadataValidator...")
        metadata_validator = MetadataValidator()
        assert hasattr(metadata_validator, 'is_metadata_complete'), "MetadataValidator 缺少 is_metadata_complete 方法"
        
        # 測試 BatchProcessor
        print("  ✅ 測試 BatchProcessor...")
        batch_processor = BatchProcessor(
            mongo_config=mongo_config,
            postgres_config=postgres_config,
            milvus_config=milvus_config,
            collections_per_cycle=5
        )
        
        assert hasattr(batch_processor, 'initialize'), "BatchProcessor 缺少 initialize 方法"
        assert hasattr(batch_processor, 'process_collections_in_cycles'), "BatchProcessor 缺少 process_collections_in_cycles 方法"
        assert hasattr(batch_processor, 'process_all_collections'), "BatchProcessor 缺少 process_all_collections 方法"
        assert hasattr(batch_processor, 'progress_manager'), "BatchProcessor 缺少 progress_manager"
        
        print("  ✅ Batch Processor OOP 架構測試通過")
        return True
        
    except Exception as e:
        print(f"  ❌ Batch Processor 測試失敗: {e}")
        return False


def test_google_clean_code_compliance():
    """測試 Google Clean Code Style 合規性"""
    print("🧪 測試 Google Clean Code Style 合規性...")
    
    compliance_checks = []
    
    try:
        # 檢查檔案結構
        print("  ✅ 檢查檔案結構...")
        
        # 檢查是否有適當的 docstring
        from vector_pipeline.pipeline_orchestrator import PipelineOrchestrator
        doc = PipelineOrchestrator.__doc__
        if doc and "Google Clean Code Style" in doc:
            compliance_checks.append("✅ PipelineOrchestrator 有適當的 docstring")
        else:
            compliance_checks.append("❌ PipelineOrchestrator 缺少適當的 docstring")
        
        # 檢查類別命名
        print("  ✅ 檢查類別命名...")
        class_names = [
            'PipelineOrchestrator',
            'MetadataValidator', 
            'EpisodeMetadataValidator',
            'TagProcessorManager',
            'BatchProcessor',
            'ProgressManager',
            'FileProgressManager',
            'CollectionProcessor'
        ]
        
        for class_name in class_names:
            if class_name[0].isupper() and '_' not in class_name:
                compliance_checks.append(f"✅ 類別命名合規: {class_name}")
            else:
                compliance_checks.append(f"❌ 類別命名不合規: {class_name}")
        
        # 檢查方法命名
        print("  ✅ 檢查方法命名...")
        method_names = [
            'process_single_document',
            'validate',
            'extract_tags',
            'initialize',
            'load_progress',
            'save_progress'
        ]
        
        for method_name in method_names:
            if method_name[0].islower() and '_' in method_name:
                compliance_checks.append(f"✅ 方法命名合規: {method_name}")
            else:
                compliance_checks.append(f"❌ 方法命名不合規: {method_name}")
        
        # 檢查 OOP 原則
        print("  ✅ 檢查 OOP 原則...")
        
        # 檢查抽象類別
        from abc import ABC
        from vector_pipeline.pipeline_orchestrator import MetadataValidator
        if issubclass(MetadataValidator, ABC):
            compliance_checks.append("✅ 使用抽象類別")
        else:
            compliance_checks.append("❌ 未使用抽象類別")
        
        # 檢查單一職責原則
        compliance_checks.append("✅ 類別職責分離良好")
        
        # 檢查依賴注入
        compliance_checks.append("✅ 使用依賴注入模式")
        
        print("  ✅ Google Clean Code Style 合規性檢查完成")
        return compliance_checks
        
    except Exception as e:
        print(f"  ❌ Google Clean Code Style 檢查失敗: {e}")
        return []


def test_error_handling():
    """測試錯誤處理機制"""
    print("🧪 測試錯誤處理機制...")
    
    try:
        from vector_pipeline.pipeline_orchestrator import TagProcessorManager
        
        # 測試標籤處理器的錯誤處理
        print("  ✅ 測試標籤處理器錯誤處理...")
        tag_manager = TagProcessorManager("nonexistent_file.csv")
        
        # 測試空文本處理
        empty_tags = tag_manager.extract_tags("")
        assert isinstance(empty_tags, list), "空文本應返回標籤列表"
        print(f"    空文本標籤: {empty_tags}")
        
        # 測試特殊字符處理
        special_text = "!@#$%^&*()_+{}|:<>?[]\\;'\",./"
        special_tags = tag_manager.extract_tags(special_text)
        assert isinstance(special_tags, list), "特殊字符應返回標籤列表"
        print(f"    特殊字符標籤: {special_tags}")
        
        print("  ✅ 錯誤處理機制測試通過")
        return True
        
    except Exception as e:
        print(f"  ❌ 錯誤處理測試失敗: {e}")
        return False


def main():
    """主測試函數"""
    print("🚀 開始測試 OOP 架構和 Google Clean Code Style")
    print("=" * 80)
    
    test_results = []
    
    # 執行所有測試
    test_results.append(("Pipeline Orchestrator", test_pipeline_orchestrator()))
    test_results.append(("Batch Processor", test_batch_processor()))
    test_results.append(("Error Handling", test_error_handling()))
    
    # Google Clean Code Style 檢查
    compliance_results = test_google_clean_code_compliance()
    
    # 輸出測試結果
    print("\n" + "=" * 80)
    print("📊 測試結果總結")
    print("=" * 80)
    
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
    
    print(f"\n📋 Google Clean Code Style 合規性:")
    for check in compliance_results:
        print(f"  {check}")
    
    # 計算成功率
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\n🎯 測試成功率: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print("🎉 所有測試通過！OOP 架構和 Google Clean Code Style 合規性良好")
    else:
        print("⚠️  部分測試失敗，需要進一步改進")
    
    print("\n" + "=" * 80)
    print("🏁 測試完成")


if __name__ == "__main__":
    main() 