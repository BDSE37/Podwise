// MongoDB 初始化腳本
// 建立 podcast 集合與範例資料

// 切換到 podcast 資料庫
db = db.getSiblingDB('podcast');

// 建立 podcast 集合
db.createCollection('podcasts');
db.createCollection('episodes');
db.createCollection('chunks');
db.createCollection('tags');
db.createCollection('analytics');

// 建立索引
db.podcasts.createIndex({ "name": 1 });
db.podcasts.createIndex({ "category": 1 });
db.podcasts.createIndex({ "language": 1 });
db.podcasts.createIndex({ "created_at": -1 });

db.episodes.createIndex({ "podcast_id": 1 });
db.episodes.createIndex({ "published_at": -1 });
db.episodes.createIndex({ "title": "text" });

db.chunks.createIndex({ "episode_id": 1 });
db.chunks.createIndex({ "podcast_id": 1 });
db.chunks.createIndex({ "language": 1 });
db.chunks.createIndex({ "created_at": -1 });

db.tags.createIndex({ "name": 1 });
db.tags.createIndex({ "category": 1 });

db.analytics.createIndex({ "date": -1 });
db.analytics.createIndex({ "podcast_id": 1 });

// 插入範例 podcast 資料
db.podcasts.insertMany([
    {
        _id: ObjectId(),
        name: "科技趨勢",
        author: "張小明",
        category: "科技",
        description: "探討最新科技發展趨勢",
        language: "zh",
        cover_image: "https://example.com/tech-trends.jpg",
        created_at: new Date(),
        updated_at: new Date(),
        stats: {
            total_episodes: 0,
            total_duration: 0,
            total_listens: 0
        }
    },
    {
        _id: ObjectId(),
        name: "商業洞察",
        author: "李大明",
        category: "商業",
        description: "深度分析商業案例",
        language: "zh",
        cover_image: "https://example.com/business-insights.jpg",
        created_at: new Date(),
        updated_at: new Date(),
        stats: {
            total_episodes: 0,
            total_duration: 0,
            total_listens: 0
        }
    },
    {
        _id: ObjectId(),
        name: "教育新知",
        author: "王小華",
        category: "教育",
        description: "分享教育理念與方法",
        language: "zh",
        cover_image: "https://example.com/education.jpg",
        created_at: new Date(),
        updated_at: new Date(),
        stats: {
            total_episodes: 0,
            total_duration: 0,
            total_listens: 0
        }
    }
]);

// 插入範例 episodes 資料
var techPodcast = db.podcasts.findOne({ name: "科技趨勢" });
var businessPodcast = db.podcasts.findOne({ name: "商業洞察" });

db.episodes.insertMany([
    {
        _id: ObjectId(),
        podcast_id: techPodcast._id,
        title: "AI 與未來工作",
        description: "探討人工智慧如何改變工作方式",
        duration: 1800, // 30分鐘
        published_at: new Date(),
        audio_url: "https://example.com/ai-future-work.mp3",
        transcript_url: "https://example.com/ai-future-work.txt",
        created_at: new Date(),
        updated_at: new Date(),
        tags: ["人工智慧", "工作", "未來", "科技"],
        stats: {
            listens: 0,
            likes: 0,
            shares: 0
        }
    },
    {
        _id: ObjectId(),
        podcast_id: techPodcast._id,
        title: "區塊鏈應用",
        description: "區塊鏈技術的實際應用案例",
        duration: 2100, // 35分鐘
        published_at: new Date(),
        audio_url: "https://example.com/blockchain-applications.mp3",
        transcript_url: "https://example.com/blockchain-applications.txt",
        created_at: new Date(),
        updated_at: new Date(),
        tags: ["區塊鏈", "應用", "技術", "創新"],
        stats: {
            listens: 0,
            likes: 0,
            shares: 0
        }
    },
    {
        _id: ObjectId(),
        podcast_id: businessPodcast._id,
        title: "創業成功要素",
        description: "成功創業的關鍵要素分析",
        duration: 2400, // 40分鐘
        published_at: new Date(),
        audio_url: "https://example.com/startup-success.mp3",
        transcript_url: "https://example.com/startup-success.txt",
        created_at: new Date(),
        updated_at: new Date(),
        tags: ["創業", "成功", "商業", "策略"],
        stats: {
            listens: 0,
            likes: 0,
            shares: 0
        }
    }
]);

// 插入範例 tags 資料
db.tags.insertMany([
    { name: "人工智慧", category: "科技", created_at: new Date() },
    { name: "工作", category: "生活", created_at: new Date() },
    { name: "自動化", category: "科技", created_at: new Date() },
    { name: "未來", category: "趨勢", created_at: new Date() },
    { name: "科技", category: "分類", created_at: new Date() },
    { name: "創業", category: "商業", created_at: new Date() },
    { name: "成功", category: "商業", created_at: new Date() },
    { name: "區塊鏈", category: "科技", created_at: new Date() },
    { name: "應用", category: "技術", created_at: new Date() },
    { name: "趨勢", category: "分析", created_at: new Date() }
]);

// 插入範例 analytics 資料
db.analytics.insertMany([
    {
        date: new Date(),
        podcast_id: techPodcast._id,
        episode_id: db.episodes.findOne({ title: "AI 與未來工作" })._id,
        listens: 150,
        likes: 25,
        shares: 8,
        duration_listened: 1200,
        created_at: new Date()
    },
    {
        date: new Date(),
        podcast_id: techPodcast._id,
        episode_id: db.episodes.findOne({ title: "區塊鏈應用" })._id,
        listens: 120,
        likes: 18,
        shares: 5,
        duration_listened: 1800,
        created_at: new Date()
    }
]);

// 建立聚合管道範例
db.createCollection("podcast_stats", {
    viewOn: "podcasts",
    pipeline: [
        {
            $lookup: {
                from: "episodes",
                localField: "_id",
                foreignField: "podcast_id",
                as: "episodes"
            }
        },
        {
            $addFields: {
                total_episodes: { $size: "$episodes" },
                total_duration: {
                    $sum: "$episodes.duration"
                },
                avg_duration: {
                    $avg: "$episodes.duration"
                }
            }
        },
        {
            $project: {
                name: 1,
                author: 1,
                category: 1,
                total_episodes: 1,
                total_duration: 1,
                avg_duration: 1,
                created_at: 1
            }
        }
    ]
});

print("MongoDB podcast 資料庫初始化完成！");
print("集合數量: " + db.getCollectionNames().length);
print("Podcasts: " + db.podcasts.countDocuments());
print("Episodes: " + db.episodes.countDocuments());
print("Tags: " + db.tags.countDocuments());
print("Analytics: " + db.analytics.countDocuments()); 