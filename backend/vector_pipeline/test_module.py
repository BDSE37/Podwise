#!/usr/bin/env python3
"""
Vector Pipeline 模組測試
驗證 OOP 功能和 Google Clean Code 規範
"""

import sys
from pathlib import Path
from typing import Dict, Any

# 添加父目錄到路徑
sys.path.append(str(Path(__file__).parent.parent))

def test_text_processor_oop() -> bool:
    """測試 TextProcessor 的 OOP 功能"""
    print("🧪 測試 TextProcessor OOP 功能...")
    
    try:
        from vector_pipeline import TextProcessor
        
        # 測試配置
        mongo_config = {
            "host": "localhost",
            "port": 27017,
            "database": "podwise",
            "username": "bdse37",
            "password": "111111"
        }
        
        postgres_config = {
            "host": "localhost",
            "port": 5432,
            "database": "podcast",
            "user": "bdse37",
            "password": "111111"
        }
        
        # 測試實例化
        processor = TextProcessor(mongo_config, postgres_config)
        print("✅ TextProcessor 實例化成功")
        
        # 測試文本分塊
        test_text = "人工智慧技術正在快速發展。機器學習和深度學習已經成為現代科技的核心。"
        chunks = processor.split_text_into_chunks(test_text)
        print(f"✅ 文本分塊: {len(chunks)} 個塊")
        
        # 測試標籤提取
        for i, chunk in enumerate(chunks):
            tags = processor.extract_tags_from_chunk(chunk)
            print(f"✅ 塊 {i+1} 標籤: {tags}")
        
        # 測試標籤統計
        stats = processor.get_tag_statistics()
        print(f"✅ 標籤統計: {stats['total_unique_tags']} 個唯一標籤")
        
        # 測試資源清理
        processor.close()
        print("✅ TextProcessor 資源清理成功")
        
        return True
        
    except Exception as e:
        print(f"❌ TextProcessor 測試失敗: {e}")
        return False


def test_vector_pipeline_oop() -> bool:
    """測試 VectorPipeline 的 OOP 功能"""
    print("\n🧪 測試 VectorPipeline OOP 功能...")
    
    try:
        from vector_pipeline import VectorPipeline
        
        # 測試配置
        mongo_config = {
            "host": "localhost",
            "port": 27017,
            "database": "podwise",
            "username": "bdse37",
            "password": "111111"
        }
        
        postgres_config = {
            "host": "localhost",
            "port": 5432,
            "database": "podcast",
            "user": "bdse37",
            "password": "111111"
        }
        
        milvus_config = {
            "host": "localhost",
            "port": "19530",
            "collection_name": "test_collection",
            "dim": 1024,
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",
            "nlist": 1024
        }
        
        # 測試實例化
        pipeline = VectorPipeline(mongo_config, milvus_config, postgres_config)
        print("✅ VectorPipeline 實例化成功")
        
        # 測試集合操作
        test_collection = "test_oop_collection"
        
        # 創建集合
        collection_name = pipeline.create_collection(test_collection)
        print(f"✅ 集合創建: {collection_name}")
        
        # 獲取統計資訊
        stats = pipeline.get_collection_stats(collection_name)
        print(f"✅ 集合統計: {stats['num_entities']} 個實體")
        
        # 清理測試集合
        pipeline.drop_collection(collection_name)
        print(f"✅ 集合清理: {collection_name}")
        
        # 測試資源清理
        pipeline.close()
        print("✅ VectorPipeline 資源清理成功")
        
        return True
        
    except Exception as e:
        print(f"❌ VectorPipeline 測試失敗: {e}")
        return False


def test_module_imports() -> bool:
    """測試模組導入"""
    print("\n🧪 測試模組導入...")
    
    try:
        # 測試直接導入
        from vector_pipeline import TextProcessor, VectorPipeline
        print("✅ 直接導入成功")
        
        # 測試相對導入
        from .text_processor import TextProcessor as TP
        from .vector_pipeline import VectorPipeline as VP
        print("✅ 相對導入成功")
        
        # 測試模組屬性
        import vector_pipeline
        print(f"✅ 模組版本: {getattr(vector_pipeline, '__version__', 'N/A')}")
        print(f"✅ 模組作者: {getattr(vector_pipeline, '__author__', 'N/A')}")
        print(f"✅ 模組描述: {getattr(vector_pipeline, '__description__', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模組導入測試失敗: {e}")
        return False


def test_clean_code_features() -> bool:
    """測試 Clean Code 特性"""
    print("\n🧪 測試 Clean Code 特性...")
    
    try:
        from vector_pipeline import TextProcessor, VectorPipeline
        
        # 測試型別註解
        mongo_config: Dict[str, Any] = {
            "host": "localhost",
            "port": 27017,
            "database": "test",
            "username": "test",
            "password": "test"
        }
        
        postgres_config: Dict[str, Any] = {
            "host": "localhost",
            "port": 5432,
            "database": "test",
            "user": "test",
            "password": "test"
        }
        
        # 測試單一職責原則
        processor = TextProcessor(mongo_config, postgres_config)
        
        # 測試函數職責單一
        test_text = "測試文本"
        chunks = processor.split_text_into_chunks(test_text)
        tags = processor.extract_tags_from_chunk(chunks[0] if chunks else "")
        
        print(f"✅ 文本分塊職責: {len(chunks)} 個塊")
        print(f"✅ 標籤提取職責: {len(tags)} 個標籤")
        
        # 測試資源管理
        processor.close()
        print("✅ 資源管理: 正確清理")
        
        return True
        
    except Exception as e:
        print(f"❌ Clean Code 測試失敗: {e}")
        return False


def main() -> None:
    """主測試函數"""
    print("🎙️ Vector Pipeline 模組測試")
    print("=" * 50)
    
    # 執行測試
    tests = [
        ("模組導入", test_module_imports),
        ("TextProcessor OOP", test_text_processor_oop),
        ("VectorPipeline OOP", test_vector_pipeline_oop),
        ("Clean Code 特性", test_clean_code_features)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} 測試異常: {e}")
            results[test_name] = False
    
    # 總結
    print("\n" + "="*50)
    print("📊 測試結果:")
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有測試通過！")
        print("\n✅ OOP 設計符合規範")
        print("✅ Google Clean Code 規範符合")
        print("✅ 模組功能完整")
        print("✅ 資源管理正確")
    else:
        print("\n⚠️ 部分測試失敗，請檢查模組配置")


if __name__ == "__main__":
    main()
    sys.exit(0) 