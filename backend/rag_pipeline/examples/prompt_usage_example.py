#!/usr/bin/env python3
"""
Podwise RAG 問答機器人提示詞使用範例

展示如何使用提示詞模板進行：
1. 問題分類
2. 語意檢索（整合 text2vec-base-chinese 和 TAG_info.csv）
3. 專家評估
4. 領導者決策
5. 回答生成
6. Langfuse 雲端監控 LLM 思考過程

作者: Podwise Team
版本: 1.0.0
"""

import json
import sys
import os
import time
import uuid
from datetime import datetime

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.prompt_templates import PodwisePromptTemplates, format_prompt, get_prompt_template
from config.integrated_config import get_config
from utils.langfuse_integration import get_langfuse_monitor


def demonstrate_langfuse_monitoring():
    """展示 Langfuse 監控功能"""
    print("=" * 60)
    print("📊 Langfuse 雲端監控展示")
    print("=" * 60)
    
    # 獲取 Langfuse 監控器
    monitor = get_langfuse_monitor()
    
    if not monitor.is_enabled():
        print("⚠️ Langfuse 監控未啟用")
        print("   請設定環境變數：")
        print("   - LANGFUSE_PUBLIC_KEY")
        print("   - LANGFUSE_SECRET_KEY")
        print("   - LANGFUSE_HOST (可選，預設為 https://cloud.langfuse.com)")
        return
    
    print("✅ Langfuse 監控已啟用")
    
    # 創建追蹤
    trace_id = monitor.create_trace(
        name="RAG Pipeline 完整流程演示",
        user_id="demo_user_001",
        metadata={
            "demo_type": "prompt_usage_example",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
    )
    
    if trace_id:
        print(f"📈 追蹤 ID: {trace_id}")
        print(f"🌐 追蹤 URL: {monitor.get_trace_url(trace_id)}")
        
        # 模擬思考過程追蹤
        thinking_steps = [
            {
                "type": "query_analysis",
                "input": {"query": "我想學習投資理財"},
                "output": {"keywords": ["學習", "投資", "理財"], "intent": "educational"},
                "confidence": 0.9
            },
            {
                "type": "category_classification",
                "input": {"keywords": ["學習", "投資", "理財"]},
                "output": {"category": "商業", "confidence": 0.85},
                "confidence": 0.85
            },
            {
                "type": "semantic_retrieval",
                "input": {"query": "我想學習投資理財", "category": "商業"},
                "output": {"results_count": 5, "avg_confidence": 0.78},
                "confidence": 0.78
            }
        ]
        
        monitor.trace_thinking_process(
            trace_id=trace_id,
            query="我想學習投資理財，有什麼推薦的 Podcast 嗎？",
            thinking_steps=thinking_steps,
            final_decision="推薦商業類投資理財節目"
        )
        
        # 模擬模型選擇追蹤
        monitor.trace_model_selection(
            trace_id=trace_id,
            available_models=["qwen2.5-7b", "qwen2.5-14b", "qwen2.5-32b"],
            selected_model="qwen2.5-14b",
            selection_reason="平衡效能和準確性",
            performance_metrics={
                "response_time": 2.5,
                "accuracy": 0.92,
                "cost": "medium"
            }
        )
        
        # 模擬代理互動追蹤
        monitor.trace_agent_interactions(
            trace_id=trace_id,
            agent_name="BusinessExpert",
            agent_role="商業專家",
            input_data={"query": "我想學習投資理財", "category": "商業"},
            output_data={"recommendations": 3, "confidence": 0.85},
            confidence=0.85,
            processing_time=1.2
        )
        
        # 模擬語意檢索追蹤
        monitor.trace_semantic_retrieval(
            trace_id=trace_id,
            query="我想學習投資理財",
            semantic_score=0.82,
            tag_matches=[
                {"tag": "投資", "score": 0.9, "matched_words": ["投資"]},
                {"tag": "理財", "score": 0.85, "matched_words": ["理財"]}
            ],
            hybrid_score=0.835,
            final_results=[
                {"title": "股癌 EP123_投資新手必聽", "confidence": 0.85},
                {"title": "人生實用商學院 EP45_理財規劃", "confidence": 0.75}
            ]
        )
        
        # 模擬完整 RAG Pipeline 追蹤
        monitor.trace_rag_pipeline(
            trace_id=trace_id,
            query="我想學習投資理財，有什麼推薦的 Podcast 嗎？",
            category="商業",
            rag_results={
                "category_result": {"category": "商業", "confidence": 0.85},
                "rag_result": [
                    {"title": "股癌 EP123_投資新手必聽", "confidence": 0.85},
                    {"title": "人生實用商學院 EP45_理財規劃", "confidence": 0.75}
                ]
            },
            final_response="根據您的投資理財需求，我推薦以下節目：1. 股癌 EP123_投資新手必聽 2. 人生實用商學院 EP45_理財規劃",
            confidence=0.85,
            processing_time=3.2
        )
        
        # 結束追蹤
        monitor.end_trace(trace_id, "success")
        print("✅ 追蹤完成")
        
    else:
        print("❌ 創建追蹤失敗")


def demonstrate_semantic_retrieval():
    """展示語意檢索和標籤比對功能"""
    print("=" * 60)
    print("🔍 語意檢索和標籤比對功能展示")
    print("=" * 60)
    
    # 獲取語意檢索配置
    config_manager = get_config()
    
    # 顯示配置資訊
    print("\n📋 語意檢索配置：")
    model_config = config_manager.get_model_config()
    print(f"  模型：{model_config['model_name']}")
    print(f"  路徑：{model_config['model_path']}")
    print(f"  最大長度：{model_config['max_length']}")
    
    retrieval_config = config_manager.get_retrieval_config()
    print(f"  語意權重：{retrieval_config['semantic_weight_factor']}")
    print(f"  標籤權重：{retrieval_config['tag_weight_factor']}")
    print(f"  信心度閾值：0.7")
    
    # 顯示標籤統計
    tag_stats = config_manager.get_tag_statistics()
    print(f"\n📊 標籤統計：")
    if "error" not in tag_stats:
        print(f"  總標籤數：{tag_stats['total_tags']}")
        for category, count in tag_stats['categories'].items():
            print(f"  {category}：{count} 個標籤")
    else:
        print(f"  標籤載入狀態：{tag_stats['error']}")
    
    # 測試標籤匹配
    test_queries = [
        "我想學習投資理財，有什麼推薦的 Podcast 嗎？",
        "最近想了解 AI 技術發展趨勢",
        "通勤時想聽一些輕鬆的節目",
        "想學習職涯規劃和個人成長"
    ]
    
    print(f"\n🧪 標籤匹配測試：")
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. 查詢：{query}")
        matches = config_manager.match_query_tags(query)
        
        if matches:
            print("   匹配標籤：")
            for tag, score, matched_words in matches[:3]:
                print(f"     {tag}: {score:.2f} ({', '.join(matched_words)})")
        else:
            print("   無匹配標籤")
    
    # 測試混合分數計算
    print(f"\n📈 混合分數計算範例：")
    test_cases = [
        (0.8, 0.6, "高語意 + 中標籤"),
        (0.6, 0.8, "中語意 + 高標籤"),
        (0.9, 0.9, "高語意 + 高標籤"),
        (0.4, 0.3, "低語意 + 低標籤")
    ]
    
    for semantic_score, tag_score, description in test_cases:
        hybrid_score = config_manager.calculate_hybrid_score(semantic_score, tag_score)
        confidence = "✅ 通過" if hybrid_score >= 0.7 else "❌ 不通過"
        print(f"  {description}: 語意={semantic_score:.1f}, 標籤={tag_score:.1f}, 混合={hybrid_score:.3f} {confidence}")


def demonstrate_prompt_usage():
    """展示提示詞模板使用"""
    print("\n" + "=" * 60)
    print("🎯 提示詞模板使用展示")
    print("=" * 60)
    
    # 測試用戶問題
    user_question = "我想學習投資理財，有什麼推薦的 Podcast 嗎？"
    print(f"\n👤 用戶問題：{user_question}")
    
    # 1. 問題分類
    print(f"\n📊 1. 問題分類")
    classifier_prompt = get_prompt_template("category_classifier")
    formatted_classifier = format_prompt(classifier_prompt, user_question=user_question)
    print(f"分類提示詞長度：{len(formatted_classifier)} 字元")
    
    # 模擬分類結果
    category_result = {
        "categories": [
            {
                "category": "商業",
                "confidence": 0.85,
                "keywords": ["投資", "理財"],
                "reasoning": "用戶明確提到投資理財，屬於商業類別"
            },
            {
                "category": "教育",
                "confidence": 0.45,
                "keywords": ["學習"],
                "reasoning": "提到學習，但主要內容是投資理財"
            }
        ],
        "primary_category": "商業",
        "is_multi_category": False,
        "cross_category_keywords": []
    }
    
    # 2. 語意檢索
    print(f"\n🔍 2. 語意檢索")
    retrieval_prompt = get_prompt_template("semantic_retrieval")
    formatted_retrieval = format_prompt(
        retrieval_prompt, 
        user_query=user_question,
        category_result=json.dumps(category_result, ensure_ascii=False, indent=2)
    )
    print(f"檢索提示詞長度：{len(formatted_retrieval)} 字元")
    
    # 模擬檢索結果
    search_results = [
        {
            "title": "股癌 EP123_投資新手必聽",
            "episode": "EP123",
            "rss_id": "stock_cancer_123",
            "category": "商業",
            "similarity_score": 0.85,
            "tag_score": 0.7,
            "hybrid_score": 0.805,
            "updated_at": "2024-01-15",
            "summary": "專門為投資新手設計的理財觀念分享"
        },
        {
            "title": "人生實用商學院 EP45_理財規劃",
            "episode": "EP45",
            "rss_id": "business_school_45",
            "category": "商業",
            "similarity_score": 0.75,
            "tag_score": 0.8,
            "hybrid_score": 0.765,
            "updated_at": "2024-01-10",
            "summary": "實用的理財規劃建議和策略"
        }
    ]
    
    # 3. 專家評估
    print(f"\n🎓 3. 專家評估")
    expert_prompt = get_prompt_template("business_expert")
    formatted_expert = format_prompt(
        expert_prompt,
        search_results=json.dumps(search_results, ensure_ascii=False, indent=2),
        user_question=user_question
    )
    print(f"專家評估提示詞長度：{len(formatted_expert)} 字元")
    
    # 模擬專家評估結果
    expert_results = {
        "category": "商業",
        "recommendations": [
            {
                "title": "股癌 EP123_投資新手必聽",
                "episode": "EP123",
                "rss_id": "stock_cancer_123",
                "confidence": 0.85,
                "updated_at": "2024-01-15",
                "reason": "專門為投資新手設計，內容實用易懂"
            },
            {
                "title": "人生實用商學院 EP45_理財規劃",
                "episode": "EP45",
                "rss_id": "business_school_45",
                "confidence": 0.75,
                "updated_at": "2024-01-10",
                "reason": "提供實用的理財規劃建議"
            }
        ],
        "status": "success",
        "high_confidence_count": 2
    }
    
    # 4. 領導者決策
    print(f"\n👑 4. 領導者決策")
    leader_prompt = get_prompt_template("leader_decision")
    formatted_leader = format_prompt(
        leader_prompt,
        expert_results=json.dumps(expert_results, ensure_ascii=False, indent=2),
        user_question=user_question
    )
    print(f"領導者決策提示詞長度：{len(formatted_leader)} 字元")
    
    # 5. 回答生成
    print(f"\n💬 5. 回答生成")
    answer_prompt = get_prompt_template("answer_generation")
    formatted_answer = format_prompt(
        answer_prompt,
        user_question=user_question,
        final_recommendations=json.dumps(expert_results["recommendations"], ensure_ascii=False, indent=2),
        explanation="根據您的投資理財需求，推薦了兩個高品質的商業類節目"
    )
    print(f"回答生成提示詞長度：{len(formatted_answer)} 字元")


def demonstrate_web_search_fallback():
    """展示 Web Search 備援機制"""
    print("\n" + "=" * 60)
    print("🌐 Web Search 備援機制展示")
    print("=" * 60)
    
    # 模擬信心度不足的情況
    low_confidence_results = {
        "category": "其他",
        "recommendations": [
            {
                "title": "某節目",
                "episode": "EP1",
                "rss_id": "test_1",
                "confidence": 0.45,  # 低於 0.7
                "updated_at": "2024-01-01",
                "reason": "相關性較低"
            }
        ],
        "status": "no_result",
        "high_confidence_count": 0
    }
    
    print(f"\n⚠️ 低信心度情況：")
    print(f"  高信心度結果數量：{low_confidence_results['high_confidence_count']}")
    print(f"  觸發條件：高信心度結果 < 1")
    print(f"  建議動作：執行 Web Search")
    
    # Web Search 提示詞
    web_search_prompt = get_prompt_template("web_search")
    formatted_web_search = format_prompt(
        web_search_prompt,
        user_question="我想學習投資理財，有什麼推薦的 Podcast 嗎？",
        category="商業",
        fallback_reason="本地檢索結果信心度不足"
    )
    print(f"\n🌐 Web Search 提示詞長度：{len(formatted_web_search)} 字元")


def demonstrate_cross_category_handling():
    """展示跨類別處理"""
    print("\n" + "=" * 60)
    print("🔄 跨類別處理展示")
    print("=" * 60)
    
    # 模擬跨類別問題
    cross_category_question = "我想學習職涯發展和投資理財"
    print(f"\n👤 跨類別問題：{cross_category_question}")
    
    # 模擬分類結果
    cross_category_result = {
        "categories": [
            {
                "category": "商業",
                "confidence": 0.75,
                "keywords": ["投資", "理財"],
                "reasoning": "提到投資理財"
            },
            {
                "category": "教育",
                "confidence": 0.8,
                "keywords": ["學習", "職涯發展"],
                "reasoning": "提到學習和職涯發展"
            }
        ],
        "primary_category": "教育",
        "is_multi_category": True,
        "cross_category_keywords": ["學習", "發展"]
    }
    
    print(f"\n📊 分類結果：")
    for cat in cross_category_result["categories"]:
        print(f"  {cat['category']}: 信心度 {cat['confidence']:.2f}")
    
    print(f"\n🎯 處理策略：")
    print(f"  1. 分別檢索各類別內容")
    print(f"  2. 按信心度排序（教育 > 商業）")
    print(f"  3. 可能混合推薦兩個類別")
    print(f"  4. 確保推薦多樣性")


def main():
    """主函數"""
    print("🚀 Podwise RAG 問答機器人提示詞使用範例")
    print("整合 text2vec-base-chinese 語意檢索、TAG_info.csv 標籤比對和 Langfuse 監控")
    
    try:
        # 展示 Langfuse 監控功能
        demonstrate_langfuse_monitoring()
        
        # 展示語意檢索功能
        demonstrate_semantic_retrieval()
        
        # 展示提示詞使用
        demonstrate_prompt_usage()
        
        # 展示 Web Search 備援
        demonstrate_web_search_fallback()
        
        # 展示跨類別處理
        demonstrate_cross_category_handling()
        
        print("\n" + "=" * 60)
        print("✅ 範例展示完成")
        print("=" * 60)
        
        print(f"\n📝 使用說明：")
        print(f"1. 語意檢索：使用 text2vec-base-chinese 模型 + TAG_info.csv 標籤匹配")
        print(f"2. 混合分數：語意權重 70% + 標籤權重 30%")
        print(f"3. 信心度控制：只有 >= 0.7 的結果才被推薦")
        print(f"4. 跨類別處理：按信心度排序，支援混合推薦")
        print(f"5. Web Search 備援：信心度不足時自動觸發")
        print(f"6. Langfuse 監控：追蹤 LLM 思考過程和效能指標")
        
        print(f"\n🔧 環境設定：")
        print(f"1. 設定 Langfuse 環境變數以啟用監控")
        print(f"2. 確保 TAG_info.csv 檔案存在")
        print(f"3. 下載 text2vec-base-chinese 模型")
        
    except Exception as e:
        print(f"❌ 執行錯誤：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 