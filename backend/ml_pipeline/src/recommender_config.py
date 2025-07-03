"""
推薦系統配置文件
定義各種推薦策略的配置參數
"""

from typing import Dict, Any

# 推薦系統基本配置
RECOMMENDER_CONFIG = {
    "content_weight": 0.3,  # 基於內容的推薦權重
    "cf_weight": 0.3,      # 協同過濾推薦權重
    "time_weight": 0.1,    # 基於時間的推薦權重
    "topic_weight": 0.1,   # 基於主題的推薦權重
    "popularity_weight": 0.1,  # 基於流行度的推薦權重
    "behavior_weight": 0.1,    # 基於用戶行為的推薦權重
    "min_score": 0.1,          # 最小推薦分數閾值
    "max_recommendations": 10   # 最大推薦數量
}

# 基於內容的推薦配置
CONTENT_BASED_CONFIG = {
    "title_weight": 0.4,       # 標題權重
    "description_weight": 0.3,  # 描述權重
    "topic_weight": 0.2,       # 主題標籤權重
    "summary_weight": 0.1      # 摘要權重
}

# 協同過濾配置
COLLABORATIVE_FILTERING_CONFIG = {
    "rating_weight": 2.0,      # 評分權重
    "preview_weight": 1.0,     # 預覽播放權重
    "playtime_weight": 1.0,    # 播放時間權重
    "like_weight": 0.5,        # 喜歡權重
    "dislike_weight": -0.5,    # 不喜歡權重
    "play_count_weight": 1.0   # 播放次數權重
}

# 基於時間的推薦配置
TIME_BASED_CONFIG = {
    "recency_weight": 0.6,     # 最近性權重
    "frequency_weight": 0.4,   # 頻率權重
    "decay_factor": 0.1        # 時間衰減因子
}

# 基於主題的推薦配置
TOPIC_BASED_CONFIG = {
    "keyword_weight": 0.4,     # 關鍵詞權重
    "category_weight": 0.3,    # 分類權重
    "tag_weight": 0.3          # 標籤權重
}

# 基於流行度的推薦配置
POPULARITY_BASED_CONFIG = {
    "rating_weight": 0.4,      # 評分權重
    "ranking_weight": 0.3,     # 排名權重
    "play_count_weight": 0.3   # 播放次數權重
}

# 基於用戶行為的推薦配置
USER_BEHAVIOR_CONFIG = {
    "view_weight": 0.3,        # 瀏覽權重
    "play_weight": 0.4,        # 播放權重
    "share_weight": 0.2,       # 分享權重
    "comment_weight": 0.1      # 評論權重
}

def get_recommender_config() -> Dict[str, Any]:
    """
    獲取完整的推薦系統配置
    
    Returns:
        Dict[str, Any]: 推薦系統配置
    """
    return {
        "base": RECOMMENDER_CONFIG,
        "content": CONTENT_BASED_CONFIG,
        "collaborative": COLLABORATIVE_FILTERING_CONFIG,
        "time": TIME_BASED_CONFIG,
        "topic": TOPIC_BASED_CONFIG,
        "popularity": POPULARITY_BASED_CONFIG,
        "behavior": USER_BEHAVIOR_CONFIG
    } 