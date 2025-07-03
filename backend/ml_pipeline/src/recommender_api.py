#!/usr/bin/env python3
"""
Podcast 推薦 API
提供每日推薦和過濾推薦功能
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import pandas as pd
import random
from datetime import datetime, timedelta
import logging

# 使用直接導入
try:
    from podcast_recommender import PodcastRecommender
except ImportError:
    # 如果直接導入失敗，嘗試相對導入
    from .podcast_recommender import PodcastRecommender

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建 FastAPI 應用
app = FastAPI(
    title="Podwise Podcast 推薦 API",
    description="專注於財經和自我成長的 Podcast 推薦系統",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模擬資料（實際應用中應該從資料庫載入）
def create_sample_data():
    """創建模擬的 Podcast 和使用者資料"""
    
    # Podcast 資料
    podcast_data = pd.DataFrame([
        {
            'id': 'p1', 'title': '財經早知道', 'category': '財經', 
            'description': '每日財經新聞解析，助您掌握投資先機',
            'tags': '投資,理財,股市,基金', 'popularity': 95
        },
        {
            'id': 'p2', 'title': '自我成長實驗室', 'category': '自我成長',
            'description': '探索個人潛能，實現自我突破',
            'tags': '心理學,成長,目標設定,習慣養成', 'popularity': 88
        },
        {
            'id': 'p3', 'title': '商業思維', 'category': '財經',
            'description': '深度解析商業模式與策略思維',
            'tags': '商業,策略,創業,管理', 'popularity': 92
        },
        {
            'id': 'p4', 'title': '心靈成長指南', 'category': '自我成長',
            'description': '心靈成長與心理健康指南',
            'tags': '心理學,冥想,情緒管理,正念', 'popularity': 85
        },
        {
            'id': 'p5', 'title': '投資理財學院', 'category': '財經',
            'description': '系統性學習投資理財知識',
            'tags': '投資,理財,資產配置,風險管理', 'popularity': 90
        },
        {
            'id': 'p6', 'title': '高效能人士的七個習慣', 'category': '自我成長',
            'description': '基於經典書籍的個人效能提升',
            'tags': '效能,習慣,時間管理,領導力', 'popularity': 87
        },
        {
            'id': 'p7', 'title': '全球財經透視', 'category': '財經',
            'description': '國際財經趨勢與市場分析',
            'tags': '國際,財經,趨勢,分析', 'popularity': 89
        },
        {
            'id': 'p8', 'title': '心理學與生活', 'category': '自我成長',
            'description': '心理學知識的實際應用',
            'tags': '心理學,應用,生活,認知', 'popularity': 83
        }
    ])
    
    # 使用者歷史資料
    user_history = pd.DataFrame([
        {'user_id': 'user1', 'podcast_id': 'p1', 'rating': 4.5, 'listen_time': 120},
        {'user_id': 'user1', 'podcast_id': 'p3', 'rating': 4.0, 'listen_time': 90},
        {'user_id': 'user1', 'podcast_id': 'p5', 'rating': 4.8, 'listen_time': 150},
        {'user_id': 'user2', 'podcast_id': 'p2', 'rating': 4.2, 'listen_time': 100},
        {'user_id': 'user2', 'podcast_id': 'p4', 'rating': 4.6, 'listen_time': 110},
        {'user_id': 'user2', 'podcast_id': 'p6', 'rating': 4.3, 'listen_time': 95},
        {'user_id': 'user3', 'podcast_id': 'p1', 'rating': 4.7, 'listen_time': 130},
        {'user_id': 'user3', 'podcast_id': 'p2', 'rating': 4.1, 'listen_time': 85},
        {'user_id': 'user3', 'podcast_id': 'p7', 'rating': 4.4, 'listen_time': 105},
        {'user_id': 'user4', 'podcast_id': 'p4', 'rating': 4.9, 'listen_time': 140},
        {'user_id': 'user4', 'podcast_id': 'p6', 'rating': 4.5, 'listen_time': 115},
        {'user_id': 'user4', 'podcast_id': 'p8', 'rating': 4.2, 'listen_time': 90}
    ])
    
    return podcast_data, user_history

# 初始化推薦系統
podcast_data, user_history = create_sample_data()
recommender = PodcastRecommender(podcast_data, user_history)

# 每日推薦快取
daily_recommendations = {}
last_update = None

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "service": "Podcast Recommender API",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/daily-recommendations")
async def get_daily_recommendations(
    user_id: Optional[str] = Query(None, description="使用者ID（可選）"),
    limit: int = Query(6, description="推薦數量", ge=1, le=20)
):
    """
    取得每日推薦清單
    
    Args:
        user_id: 使用者ID（可選，不提供則為匿名推薦）
        limit: 推薦數量
        
    Returns:
        每日推薦清單
    """
    global daily_recommendations, last_update
    
    try:
        today = datetime.now().date()
        
        # 檢查是否需要更新每日推薦
        if last_update != today:
            daily_recommendations = {}
            last_update = today
        
        # 生成快取鍵
        cache_key = f"{user_id or 'anonymous'}_{limit}"
        
        if cache_key not in daily_recommendations:
            # 生成新的每日推薦
            if user_id:
                # 有使用者ID，使用個人化推薦
                recommendations = recommender.get_recommendations(
                    user_id, limit * 2  # 多取一些以便隨機選擇
                )
            else:
                # 匿名使用者，使用熱門推薦
                recommendations = recommender._get_popular_recommendations(limit * 2)
                recommendations = recommender._enrich_recommendations([pid for pid, _ in recommendations])
            
            # 隨機選擇指定數量
            random.shuffle(recommendations)
            daily_recommendations[cache_key] = recommendations[:limit]
        
        return {
            "date": today.isoformat(),
            "user_id": user_id,
            "recommendations": daily_recommendations[cache_key],
            "total": len(daily_recommendations[cache_key])
        }
        
    except Exception as e:
        logger.error(f"每日推薦生成失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="推薦生成失敗")

@app.get("/filtered-recommendations")
async def get_filtered_recommendations(
    category: Optional[str] = Query(None, description="類別篩選（財經/自我成長/商業/教育）"),
    user_id: Optional[str] = Query(None, description="使用者ID（可選）"),
    limit: int = Query(10, description="推薦數量", ge=1, le=50),
    min_rating: Optional[float] = Query(None, description="最低評分", ge=1.0, le=5.0),
    max_rating: Optional[float] = Query(None, description="最高評分", ge=1.0, le=5.0),
    tags: Optional[str] = Query(None, description="標籤篩選（逗號分隔）"),
    min_listen_count: Optional[int] = Query(None, description="最低收聽次數", ge=0),
    sort_by: str = Query("recommendation_score", description="排序方式（recommendation_score/rating/listen_count/popularity）"),
    sort_order: str = Query("desc", description="排序順序（asc/desc）")
):
    """
    取得過濾後的推薦清單
    
    Args:
        category: 類別篩選（財經/自我成長/商業/教育）
        user_id: 使用者ID（可選）
        limit: 推薦數量
        min_rating: 最低評分
        max_rating: 最高評分
        tags: 標籤篩選（逗號分隔）
        min_listen_count: 最低收聽次數
        sort_by: 排序方式
        sort_order: 排序順序
        
    Returns:
        過濾後的推薦清單
    """
    try:
        # 驗證類別
        valid_categories = ['財經', '自我成長', '商業', '教育']
        if category and category not in valid_categories:
            raise HTTPException(
                status_code=400, 
                detail=f"無效的類別，請選擇: {', '.join(valid_categories)}"
            )
        
        # 驗證排序方式
        valid_sort_by = ['recommendation_score', 'rating', 'listen_count', 'popularity']
        if sort_by not in valid_sort_by:
            raise HTTPException(
                status_code=400,
                detail=f"無效的排序方式，請選擇: {', '.join(valid_sort_by)}"
            )
        
        # 驗證排序順序
        if sort_order not in ['asc', 'desc']:
            raise HTTPException(
                status_code=400,
                detail="無效的排序順序，請選擇: asc 或 desc"
            )
        
        # 生成推薦
        if user_id:
            # 有使用者ID，使用個人化推薦
            recommendations = recommender.get_recommendations(
                user_id, limit * 3, category  # 多取一些以便過濾
            )
        else:
            # 匿名使用者，使用熱門推薦
            recommendations = recommender._get_popular_recommendations(limit * 3, category)
            recommendations = recommender._enrich_recommendations([pid for pid, _ in recommendations])
        
        # 應用過濾條件
        filtered_recommendations = []
        
        for rec in recommendations:
            # 評分過濾
            if min_rating and rec['average_rating'] < min_rating:
                continue
            if max_rating and rec['average_rating'] > max_rating:
                continue
            
            # 收聽次數過濾
            if min_listen_count and rec['listen_count'] < min_listen_count:
                continue
            
            # 標籤過濾
            if tags:
                tag_list = [tag.strip() for tag in tags.split(',')]
                podcast_tags = [tag.strip() for tag in rec['tags'].split(',')]
                if not any(tag in podcast_tags for tag in tag_list):
                    continue
            
            filtered_recommendations.append(rec)
        
        # 排序
        reverse_order = sort_order == 'desc'
        
        if sort_by == 'recommendation_score':
            # 使用推薦分數排序（保持原有順序）
            pass
        elif sort_by == 'rating':
            filtered_recommendations.sort(key=lambda x: x['average_rating'], reverse=reverse_order)
        elif sort_by == 'listen_count':
            filtered_recommendations.sort(key=lambda x: x['listen_count'], reverse=reverse_order)
        elif sort_by == 'popularity':
            # 結合評分和收聽次數的熱門度
            for rec in filtered_recommendations:
                rec['popularity_score'] = (
                    0.6 * rec['average_rating'] + 
                    0.4 * (rec['listen_count'] / max(r['listen_count'] for r in filtered_recommendations))
                )
            filtered_recommendations.sort(key=lambda x: x['popularity_score'], reverse=reverse_order)
        
        # 限制數量
        final_recommendations = filtered_recommendations[:limit]
        
        return {
            "category": category,
            "user_id": user_id,
            "filters_applied": {
                "min_rating": min_rating,
                "max_rating": max_rating,
                "tags": tags,
                "min_listen_count": min_listen_count,
                "sort_by": sort_by,
                "sort_order": sort_order
            },
            "recommendations": final_recommendations,
            "total": len(final_recommendations),
            "total_filtered": len(filtered_recommendations)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"過濾推薦生成失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="推薦生成失敗")

@app.get("/advanced-filter")
async def get_advanced_filter_recommendations(
    user_id: Optional[str] = Query(None, description="使用者ID（可選）"),
    categories: Optional[str] = Query(None, description="多類別篩選（逗號分隔）"),
    exclude_categories: Optional[str] = Query(None, description="排除類別（逗號分隔）"),
    include_tags: Optional[str] = Query(None, description="必須包含標籤（逗號分隔）"),
    exclude_tags: Optional[str] = Query(None, description="排除標籤（逗號分隔）"),
    rating_range: Optional[str] = Query(None, description="評分範圍（格式：min-max，如：3.5-5.0）"),
    listen_time_range: Optional[str] = Query(None, description="收聽時間範圍（格式：min-max，分鐘）"),
    limit: int = Query(10, description="推薦數量", ge=1, le=50),
    algorithm: str = Query("hybrid", description="推薦算法（collaborative/content/hybrid/popular）")
):
    """
    進階過濾推薦
    
    Args:
        user_id: 使用者ID（可選）
        categories: 多類別篩選
        exclude_categories: 排除類別
        include_tags: 必須包含標籤
        exclude_tags: 排除標籤
        rating_range: 評分範圍
        listen_time_range: 收聽時間範圍
        limit: 推薦數量
        algorithm: 推薦算法
        
    Returns:
        進階過濾後的推薦清單
    """
    try:
        # 解析評分範圍
        min_rating, max_rating = None, None
        if rating_range:
            try:
                min_rating, max_rating = map(float, rating_range.split('-'))
            except ValueError:
                raise HTTPException(status_code=400, detail="評分範圍格式錯誤，請使用 min-max 格式")
        
        # 解析收聽時間範圍
        min_listen_time, max_listen_time = None, None
        if listen_time_range:
            try:
                min_listen_time, max_listen_time = map(int, listen_time_range.split('-'))
            except ValueError:
                raise HTTPException(status_code=400, detail="收聽時間範圍格式錯誤，請使用 min-max 格式")
        
        # 解析類別列表
        category_list = [cat.strip() for cat in categories.split(',')] if categories else []
        exclude_category_list = [cat.strip() for cat in exclude_categories.split(',')] if exclude_categories else []
        
        # 解析標籤列表
        include_tag_list = [tag.strip() for tag in include_tags.split(',')] if include_tags else []
        exclude_tag_list = [tag.strip() for tag in exclude_tags.split(',')] if exclude_tags else []
        
        # 驗證算法
        valid_algorithms = ['collaborative', 'content', 'hybrid', 'popular']
        if algorithm not in valid_algorithms:
            raise HTTPException(
                status_code=400,
                detail=f"無效的算法，請選擇: {', '.join(valid_algorithms)}"
            )
        
        # 生成推薦（根據算法）
        if algorithm == 'collaborative' and user_id:
            recommendations = recommender._collaborative_filtering_recommend(user_id, limit * 3)
            recommendations = recommender._enrich_recommendations([pid for pid, _ in recommendations])
        elif algorithm == 'content' and user_id:
            recommendations = recommender._content_based_recommend(user_id, limit * 3)
            recommendations = recommender._enrich_recommendations([pid for pid, _ in recommendations])
        elif algorithm == 'hybrid' and user_id:
            recommendations = recommender.get_recommendations(user_id, limit * 3)
        else:
            # 熱門推薦
            recommendations = recommender._get_popular_recommendations(limit * 3)
            recommendations = recommender._enrich_recommendations([pid for pid, _ in recommendations])
        
        # 應用進階過濾
        filtered_recommendations = []
        
        for rec in recommendations:
            # 類別過濾
            if category_list and rec['category'] not in category_list:
                continue
            if exclude_category_list and rec['category'] in exclude_category_list:
                continue
            
            # 評分過濾
            if min_rating and rec['average_rating'] < min_rating:
                continue
            if max_rating and rec['average_rating'] > max_rating:
                continue
            
            # 標籤過濾
            podcast_tags = [tag.strip() for tag in rec['tags'].split(',')]
            
            # 必須包含標籤
            if include_tag_list and not any(tag in podcast_tags for tag in include_tag_list):
                continue
            
            # 排除標籤
            if exclude_tag_list and any(tag in podcast_tags for tag in exclude_tag_list):
                continue
            
            filtered_recommendations.append(rec)
        
        # 限制數量
        final_recommendations = filtered_recommendations[:limit]
        
        return {
            "algorithm": algorithm,
            "user_id": user_id,
            "filters_applied": {
                "categories": category_list,
                "exclude_categories": exclude_category_list,
                "include_tags": include_tag_list,
                "exclude_tags": exclude_tag_list,
                "rating_range": rating_range,
                "listen_time_range": listen_time_range
            },
            "recommendations": final_recommendations,
            "total": len(final_recommendations),
            "total_filtered": len(filtered_recommendations)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"進階過濾推薦生成失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="推薦生成失敗")

@app.get("/categories")
async def get_categories():
    """取得所有可用的類別"""
    return {
        "categories": [
            {
                "id": "財經",
                "name": "財經",
                "description": "投資理財、商業思維、財經分析",
                "podcast_count": len(podcast_data[podcast_data['category'] == '財經'])
            },
            {
                "id": "自我成長",
                "name": "自我成長", 
                "description": "心理學、效能提升、心靈成長",
                "podcast_count": len(podcast_data[podcast_data['category'] == '自我成長'])
            }
        ]
    }

@app.post("/update-preference")
async def update_user_preference(
    user_id: str,
    podcast_id: str,
    rating: float = Query(..., ge=1, le=5, description="評分 1-5"),
    listen_time: int = Query(0, description="收聽時間（分鐘）")
):
    """
    更新使用者偏好
    
    Args:
        user_id: 使用者ID
        podcast_id: Podcast ID
        rating: 評分
        listen_time: 收聽時間
        
    Returns:
        更新結果
    """
    try:
        # 驗證 Podcast 是否存在
        if podcast_id not in podcast_data['id'].values:
            raise HTTPException(status_code=404, detail="Podcast 不存在")
        
        # 更新偏好
        recommender.update_user_preference(user_id, podcast_id, rating, listen_time)
        
        return {
            "status": "success",
            "message": "偏好更新成功",
            "user_id": user_id,
            "podcast_id": podcast_id
        }
        
    except Exception as e:
        logger.error(f"偏好更新失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="偏好更新失敗")

@app.get("/podcast/{podcast_id}")
async def get_podcast_details(podcast_id: str):
    """
    取得 Podcast 詳細資訊
    
    Args:
        podcast_id: Podcast ID
        
    Returns:
        Podcast 詳細資訊
    """
    try:
        podcast = podcast_data[podcast_data['id'] == podcast_id]
        
        if podcast.empty:
            raise HTTPException(status_code=404, detail="Podcast 不存在")
        
        podcast_info = podcast.iloc[0].to_dict()
        
        # 添加統計資訊
        podcast_history = user_history[user_history['podcast_id'] == podcast_id]
        if not podcast_history.empty:
            podcast_info['average_rating'] = round(podcast_history['rating'].mean(), 2)
            podcast_info['total_listeners'] = len(podcast_history['user_id'].unique())
            podcast_info['total_listen_time'] = podcast_history['listen_time'].sum()
        else:
            podcast_info['average_rating'] = 0.0
            podcast_info['total_listeners'] = 0
            podcast_info['total_listen_time'] = 0
        
        return podcast_info
        
    except Exception as e:
        logger.error(f"取得 Podcast 詳情失敗: {str(e)}")
        raise HTTPException(status_code=500, detail="取得 Podcast 詳情失敗")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 