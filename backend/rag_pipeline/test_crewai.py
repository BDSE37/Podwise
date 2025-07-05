#!/usr/bin/env python3
"""
測試三層 CrewAI 架構的核心功能
"""

import asyncio
import logging
from typing import List, Dict, Any

# 導入核心組件
from tools.keyword_mapper import KeywordMapper, CategoryResult
from tools.knn_recommender import KNNRecommender, PodcastItem
from core.crew_agents import AgentManager, UserQuery

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_keyword_mapper():
    """測試 Keyword Mapper"""
    print("\n=== 測試 Keyword Mapper ===")
    
    mapper = KeywordMapper()
    
    test_queries = [
        "我想了解股票投資和理財規劃",
        "如何提升職場技能和溝通能力", 
        "台積電的股價走勢如何",
        "學習新技能的方法有哪些",
        "創業和職涯發展的建議"
    ]
    
    for query in test_queries:
        result = mapper.categorize_query(query)
        print(f"\n查詢: {query}")
        print(f"類別: {result.category}")
        print(f"信心值: {result.confidence:.2f}")
        print(f"商業分數: {result.business_score:.2f}")
        print(f"教育分數: {result.education_score:.2f}")
        print(f"找到關鍵詞: {result.keywords_found[:3]}")

async def test_knn_recommender():
    """測試 KNN 推薦器"""
    print("\n=== 測試 KNN 推薦器 ===")
    
    import numpy as np
    
    # 創建測試數據
    test_items = [
        PodcastItem(
            rss_id="rss_001",
            title="股癌 EP310",
            description="台股投資分析與市場趨勢",
            category="商業",
            tags=["股票", "投資", "台股", "財經"],
            vector=np.array([0.8, 0.6, 0.9, 0.7, 0.8, 0.6, 0.9, 0.7]),
            confidence=0.9
        ),
        PodcastItem(
            rss_id="rss_002", 
            title="大人學 EP110",
            description="職涯發展與個人成長指南",
            category="教育",
            tags=["職涯", "成長", "技能", "學習"],
            vector=np.array([0.3, 0.8, 0.4, 0.9, 0.3, 0.8, 0.4, 0.9]),
            confidence=0.85
        ),
        PodcastItem(
            rss_id="rss_003",
            title="財報狗 Podcast",
            description="財報分析與投資策略",
            category="商業",
            tags=["財報", "投資", "分析", "策略"],
            vector=np.array([0.9, 0.5, 0.8, 0.6, 0.9, 0.5, 0.8, 0.6]),
            confidence=0.88
        )
    ]
    
    # 初始化推薦器
    recommender = KNNRecommender(k=3, metric="cosine")
    recommender.add_podcast_items(test_items)
    
    # 測試推薦
    query_vector = np.array([0.7, 0.6, 0.8, 0.7, 0.7, 0.6, 0.8, 0.7])
    
    # 商業類別推薦
    business_result = recommender.recommend(query_vector, category_filter="商業", top_k=2)
    print(f"\n商業類別推薦:")
    print(f"信心值: {business_result.confidence:.3f}")
    print(f"處理時間: {business_result.processing_time:.3f}秒")
    for i, item in enumerate(business_result.recommendations, 1):
        print(f"{i}. {item.title} (相似度: {business_result.similarity_scores[i-1]:.3f})")
    
    # 教育類別推薦
    education_result = recommender.recommend(query_vector, category_filter="教育", top_k=2)
    print(f"\n教育類別推薦:")
    print(f"信心值: {education_result.confidence:.3f}")
    print(f"處理時間: {education_result.processing_time:.3f}秒")
    for i, item in enumerate(education_result.recommendations, 1):
        print(f"{i}. {item.title} (相似度: {education_result.similarity_scores[i-1]:.3f})")

async def test_agent_manager():
    """測試代理人管理器"""
    print("\n=== 測試代理人管理器 ===")
    
    # 配置
    config = {
        "confidence_threshold": 0.7,
        "business_expert": {"confidence_threshold": 0.7},
        "education_expert": {"confidence_threshold": 0.7},
        "rag_expert": {"confidence_threshold": 0.7},
        "summary_expert": {"confidence_threshold": 0.7},
        "rating_expert": {"confidence_threshold": 0.7},
        "tts_expert": {"confidence_threshold": 0.7},
        "user_manager": {"confidence_threshold": 0.7}
    }
    
    agent_manager = AgentManager(config)
    
    # 測試查詢
    test_queries = [
        ("user_001", "我想了解股票投資", "商業"),
        ("user_002", "如何提升職場技能", "教育"),
        ("user_003", "創業和理財規劃", "雙類別")
    ]
    
    for user_id, query, expected_category in test_queries:
        print(f"\n用戶: {user_id}")
        print(f"查詢: {query}")
        print(f"預期類別: {expected_category}")
        
        try:
            response = await agent_manager.process_query(query, user_id)
            print(f"回應: {response.content[:100]}...")
            print(f"信心值: {response.confidence:.2f}")
            print(f"處理時間: {response.processing_time:.3f}秒")
        except Exception as e:
            print(f"錯誤: {str(e)}")

async def test_integrated_flow():
    """測試整合流程"""
    print("\n=== 測試整合流程 ===")
    
    # 初始化組件
    mapper = KeywordMapper()
    import numpy as np
    
    test_items = [
        PodcastItem(
            rss_id="rss_001",
            title="股癌 EP310", 
            description="台股投資分析與市場趨勢",
            category="商業",
            tags=["股票", "投資", "台股", "財經"],
            vector=np.array([0.8, 0.6, 0.9, 0.7, 0.8, 0.6, 0.9, 0.7]),
            confidence=0.9
        ),
        PodcastItem(
            rss_id="rss_002",
            title="大人學 EP110",
            description="職涯發展與個人成長指南", 
            category="教育",
            tags=["職涯", "成長", "技能", "學習"],
            vector=np.array([0.3, 0.8, 0.4, 0.9, 0.3, 0.8, 0.4, 0.9]),
            confidence=0.85
        )
    ]
    
    recommender = KNNRecommender(k=3, metric="cosine")
    recommender.add_podcast_items(test_items)
    
    # 測試完整流程
    test_cases = [
        {
            "user_id": "user_001",
            "query": "我想了解股票投資和理財規劃",
            "description": "商業類查詢"
        },
        {
            "user_id": "user_002", 
            "query": "如何提升職場技能和溝通能力",
            "description": "教育類查詢"
        },
        {
            "user_id": "user_003",
            "query": "創業和職涯發展的建議",
            "description": "跨類別查詢"
        }
    ]
    
    for case in test_cases:
        print(f"\n--- {case['description']} ---")
        print(f"用戶: {case['user_id']}")
        print(f"查詢: {case['query']}")
        
        # 步驟 1: Keyword Mapper 分類
        category_result = mapper.categorize_query(case['query'])
        print(f"分類結果: {category_result.category} (信心值: {category_result.confidence:.2f})")
        
        # 步驟 2: KNN 推薦
        query_vector = np.array([0.7, 0.6, 0.8, 0.7, 0.7, 0.6, 0.8, 0.7])
        knn_result = recommender.recommend(
            query_vector=query_vector,
            category_filter=category_result.category if category_result.category != "雙類別" else None,
            top_k=2
        )
        
        print(f"推薦結果:")
        for i, item in enumerate(knn_result.recommendations, 1):
            print(f"  {i}. {item.title} (相似度: {knn_result.similarity_scores[i-1]:.3f})")
        
        print(f"整體信心值: {knn_result.confidence:.3f}")

async def main():
    """主測試函數"""
    print("🚀 開始測試三層 CrewAI 架構")
    
    try:
        # 測試各個組件
        await test_keyword_mapper()
        await test_knn_recommender()
        await test_agent_manager()
        await test_integrated_flow()
        
        print("\n✅ 所有測試完成")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 