import pandas as pd

# 讀取資料
df = pd.read_csv("podcast_user_interactions_fixed.csv", encoding="utf-8-sig")

# 1️⃣ 每個 episode_id 總共多少個 like_count
episode_likes = (
    df.groupby("Episode_id")["like_count"]
    .sum()
    .reset_index()
    .rename(columns={"like_count": "total_likes"})
)

# 儲存
episode_likes.to_csv("episode_likes.csv", index=False, encoding="utf-8-sig")
print("✅ 已輸出: episode_likes.csv")

# 2️⃣ 每個 episode_id 的 preview_play_count 總和
episode_plays = (
    df.groupby("Episode_id")["preview_play_count"]
    .sum()
    .reset_index()
    .rename(columns={"preview_play_count": "total_preview_play_count"})
)

# 儲存
episode_plays.to_csv("episode_plays.csv", index=False, encoding="utf-8-sig")
print("✅ 已輸出: episode_plays.csv")

# 3️⃣ 每個 user_id 看了多少不同的 episode_id
user_episode_counts = (
    df.groupby("User_id")["Episode_id"]
    .nunique()
    .reset_index()
    .rename(columns={"Episode_id": "unique_episodes"})
)

# 儲存
user_episode_counts.to_csv("user_episode_counts.csv", index=False, encoding="utf-8-sig")
print("✅ 已輸出: user_episode_counts.csv")
