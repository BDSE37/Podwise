"""
MongoDB 配置文件
"""

from typing import Dict

# MongoDB 配置
MONGO_CONFIG: Dict = {
    "host": "localhost",
    "port": 27017,
    "username": "bdse37",
    "password": "111111",
    "database": "podwise",
    "collections": {
        "transcripts": "transcripts",
        "summaries": "summaries",
        "topics": "topics"
    }
}

# MongoDB 連接字串
MONGO_URI = f"mongodb://{MONGO_CONFIG['username']}:{MONGO_CONFIG['password']}@{MONGO_CONFIG['host']}:{MONGO_CONFIG['port']}"

# MongoDB 索引配置
MONGO_INDEXES = {
    "transcripts": [
        {
            "keys": [("podcast_id", 1), ("episode_id", 1)],
            "unique": True
        },
        {
            "keys": [("created_at", -1)]
        }
    ],
    "summaries": [
        {
            "keys": [("podcast_id", 1), ("episode_id", 1)],
            "unique": True
        }
    ],
    "topics": [
        {
            "keys": [("podcast_id", 1), ("episode_id", 1), ("topic", 1)],
            "unique": True
        }
    ]
} 