-- Podwise PostgreSQL 初始化腳本
-- 帳號: bdse37
-- 密碼: 111111
-- 資料庫: podcast

-- 創建資料庫
CREATE DATABASE podcast;

-- 連接到 podcast 資料庫
\c podcast;

-- 1. users
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    given_name VARCHAR(64),
    family_name VARCHAR(64),
    username VARCHAR(64),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN,
    password VARCHAR(255) NOT NULL,
    locale VARCHAR(16),
    access_token VARCHAR(255),
    refresh_token VARCHAR(255),
    expires_in INTEGER
);

-- 2. podcasts
CREATE TABLE podcasts (
    podcast_id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    author VARCHAR(255),
    rss_link VARCHAR(512) UNIQUE,
    images_640 VARCHAR(512),
    images_300 VARCHAR(512),
    images_64 VARCHAR(512),
    languages VARCHAR(64),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    apple_podcasts_ranking INTEGER,
    apple_rating DECIMAL(3,2),
    category VARCHAR(64),
    update_frequency VARCHAR(64)
);

-- 3. episodes
CREATE TABLE episodes (
    episode_id SERIAL PRIMARY KEY,
    podcast_id INTEGER NOT NULL,
    episode_title VARCHAR(255) NOT NULL,
    published_date DATE,
    audio_url VARCHAR(512),
    duration INTEGER,
    description TEXT,
    audio_preview_url VARCHAR(512),
    languages VARCHAR(64),
    explicit BOOLEAN,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    apple_episodes_ranking INTEGER,
    FOREIGN KEY (podcast_id) REFERENCES podcasts(podcast_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 4. episode_topics
CREATE TABLE episode_topics (
    episode_id INTEGER NOT NULL,
    topic_tag VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (episode_id, topic_tag),
    FOREIGN KEY (episode_id) REFERENCES episodes(episode_id) ON DELETE CASCADE ON UPDATE CASCADE
);

COMMENT ON TABLE episode_topics IS '儲存每集人工/平台來源主題標籤（可信度高，明確定義）';
COMMENT ON COLUMN episode_topics.episode_id IS '節目集數ID，對應episodes';
COMMENT ON COLUMN episode_topics.topic_tag IS '人工標註或原始平台主題tag';

-- 5. transcripts
CREATE TABLE transcripts (
    transcript_path VARCHAR(512) PRIMARY KEY,
    episode_id INTEGER NOT NULL,
    transcript_length INTEGER,
    language VARCHAR(16),
    model_used VARCHAR(64),
    version VARCHAR(16),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(64),
    FOREIGN KEY (episode_id) REFERENCES episodes(episode_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 6. summaries
CREATE TABLE summaries (
    episode_id INTEGER PRIMARY KEY,
    summary_text TEXT,
    summary_path VARCHAR(512),
    topics JSON,
    summary_model VARCHAR(64),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (episode_id) REFERENCES episodes(episode_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 7. topics
CREATE TABLE topics (
    episode_id INTEGER NOT NULL,
    topic_tag VARCHAR(64) NOT NULL,
    source_type VARCHAR(64) NOT NULL,
    confidence_score DECIMAL(5,4),
    classified_by VARCHAR(64),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (episode_id, topic_tag, source_type),
    FOREIGN KEY (episode_id) REFERENCES episodes(episode_id) ON DELETE CASCADE ON UPDATE CASCADE
);

COMMENT ON TABLE topics IS '經由機器學習/自動分類產生的主題標註與來源，含信心分數';
COMMENT ON COLUMN topics.episode_id IS '節目集數ID，對應episodes';
COMMENT ON COLUMN topics.topic_tag IS '自動分類器預測之主題tag';
COMMENT ON COLUMN topics.source_type IS '標註來源型態，如ML、爬蟲等';
COMMENT ON COLUMN topics.confidence_score IS '分類模型預測信心分數';
COMMENT ON COLUMN topics.classified_by IS '使用之分類器/模型';

-- 8. user_feedback
CREATE TABLE user_feedback (
    user_id INTEGER NOT NULL,
    episode_id INTEGER NOT NULL,
    rating INTEGER,
    bookmark BOOLEAN,
    preview_played BOOLEAN,
    preview_listen_time INTEGER,
    preview_played_at TIMESTAMP,
    like_count INTEGER,
    dislike_count INTEGER,
    preview_play_count INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    PRIMARY KEY (user_id, episode_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (episode_id) REFERENCES episodes(episode_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 9. cf_matrix
CREATE TABLE cf_matrix (
    user_id INTEGER NOT NULL,
    episode_id INTEGER NOT NULL,
    cf_score DECIMAL(5,4),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, episode_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (episode_id) REFERENCES episodes(episode_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 10. query_log_summary
CREATE TABLE query_log_summary (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    query_type VARCHAR(64),
    date DATE,
    total_count INTEGER,
    avg_latency_ms INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- 11. hot_episode_daily
CREATE TABLE hot_episode_daily (
    date DATE NOT NULL,
    episode_id INTEGER NOT NULL,
    rank_score DECIMAL(8,2),
    category VARCHAR(64),
    rank_position INTEGER,
    PRIMARY KEY (date, episode_id),
    FOREIGN KEY (episode_id) REFERENCES episodes(episode_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 12. reco_log
CREATE TABLE reco_log (
    log_id SERIAL PRIMARY KEY,
    user_id INTEGER,
    strategy VARCHAR(64),
    recommended_ids TEXT,
    created_at TIMESTAMP NOT NULL,
    request_context TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 13. agent_trace_log
CREATE TABLE agent_trace_log (
    trace_id SERIAL PRIMARY KEY,
    user_id INTEGER,
    query_text TEXT,
    agent_name VARCHAR(64),
    response_text TEXT,
    latency_ms INTEGER,
    selected_flag BOOLEAN,
    timestamp TIMESTAMP NOT NULL,
    score DECIMAL(5,4),
    error_type VARCHAR(64),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 14. task_log
CREATE TABLE task_log (
    task_id VARCHAR(64) PRIMARY KEY,
    task_type VARCHAR(32),
    episode_id INTEGER,
    status VARCHAR(16),
    error_message TEXT,
    retry_count INTEGER,
    created_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    worker_id VARCHAR(64),
    input_path VARCHAR(255),
    output_path VARCHAR(255),
    triggered_by VARCHAR(64),
    duration_ms INTEGER,
    priority INTEGER,
    parent_task_id VARCHAR(64),
    retry_at TIMESTAMP,
    log_payload TEXT,
    FOREIGN KEY (episode_id) REFERENCES episodes(episode_id)
);

-- 15. embedding_log
CREATE TABLE embedding_log (
    log_id SERIAL PRIMARY KEY,
    episode_id INTEGER,
    vector_type VARCHAR(32),
    vector_version VARCHAR(64),
    generated_at TIMESTAMP,
    vector_dim INTEGER,
    worker_id VARCHAR(64),
    status VARCHAR(16),
    milvus_id VARCHAR(64),
    FOREIGN KEY (episode_id) REFERENCES episodes(episode_id)
);

-- 16. ingestion_log
CREATE TABLE ingestion_log (
    log_id SERIAL PRIMARY KEY,
    source_platform VARCHAR(32),
    rss_url VARCHAR(512),
    episode_id INTEGER,
    status VARCHAR(16),
    error_message TEXT,
    ingested_at TIMESTAMP,
    normalized_json JSON,
    FOREIGN KEY (episode_id) REFERENCES episodes(episode_id)
);

-- 17. alert_history_log
CREATE TABLE alert_history_log (
    alert_id SERIAL PRIMARY KEY,
    type VARCHAR(32),
    message TEXT,
    severity VARCHAR(16),
    raised_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    notified_by VARCHAR(32)
);

-- 18. system_event_log
CREATE TABLE system_event_log (
    event_id SERIAL PRIMARY KEY,
    user_id INTEGER,
    event_type VARCHAR(64) NOT NULL,
    source_service VARCHAR(64),
    event_detail TEXT,
    severity VARCHAR(16),
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- 19. comment_sources
CREATE TABLE comment_sources (
    id SERIAL PRIMARY KEY,
    source VARCHAR(255) NOT NULL,
    json_file VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 建立索引以提升查詢效能
CREATE INDEX idx_podcasts_category ON podcasts(category);
CREATE INDEX idx_episodes_podcast_id ON episodes(podcast_id);
CREATE INDEX idx_episodes_published_date ON episodes(published_date);
CREATE INDEX idx_transcripts_episode_id ON transcripts(episode_id);
CREATE INDEX idx_topics_episode_id ON topics(episode_id);
CREATE INDEX idx_user_feedback_user_id ON user_feedback(user_id);
CREATE INDEX idx_user_feedback_episode_id ON user_feedback(episode_id);
CREATE INDEX idx_cf_matrix_user_id ON cf_matrix(user_id);
CREATE INDEX idx_cf_matrix_episode_id ON cf_matrix(episode_id);
CREATE INDEX idx_hot_episode_daily_date ON hot_episode_daily(date);
CREATE INDEX idx_task_log_status ON task_log(status);
CREATE INDEX idx_embedding_log_episode_id ON embedding_log(episode_id);
CREATE INDEX idx_ingestion_log_status ON ingestion_log(status);

-- 插入測試資料
INSERT INTO users (email, given_name, family_name, username, is_active, password, locale) VALUES
('bdse37@podwise.com', 'BDSE', 'User', 'bdse37', true, '111111', 'zh-TW');

-- 插入範例 Podcast 資料
INSERT INTO podcasts (podcast_id, name, description, author, rss_link, category, languages) VALUES
(1, '矽谷輕鬆談', '科技產業深度分析與討論', '矽谷科技團隊', 'https://feeds.simplecast.com/siliconvalley', '科技', 'zh-TW'),
(2, '天下學習', '商業管理與職場技能分享', '天下雜誌', 'https://feeds.simplecast.com/learning', '商業', 'zh-TW'),
(3, '科技島讀', '台灣科技產業觀察與分析', '科技島讀團隊', 'https://feeds.simplecast.com/techisland', '科技', 'zh-TW');

-- 插入範例 Episode 資料
INSERT INTO episodes (podcast_id, episode_title, published_date, audio_url, duration, description, languages) VALUES
(1, '矽谷輕鬆談 第 1 集 - AI 發展趨勢', '2024-01-15', 'https://example.com/audio/1_1.mp3', 1800, '討論人工智慧的最新發展趨勢', 'zh-TW'),
(1, '矽谷輕鬆談 第 2 集 - 雲端運算', '2024-01-22', 'https://example.com/audio/1_2.mp3', 2100, '深入探討雲端運算技術', 'zh-TW'),
(2, '天下學習 第 1 集 - 領導力', '2024-01-16', 'https://example.com/audio/2_1.mp3', 2400, '如何培養有效的領導能力', 'zh-TW'),
(2, '天下學習 第 2 集 - 時間管理', '2024-01-23', 'https://example.com/audio/2_2.mp3', 1950, '提升工作效率的時間管理技巧', 'zh-TW'),
(3, '科技島讀 第 1 集 - 台灣半導體', '2024-01-17', 'https://example.com/audio/3_1.mp3', 2700, '台灣半導體產業的現況與未來', 'zh-TW'),
(3, '科技島讀 第 2 集 - 新創生態', '2024-01-24', 'https://example.com/audio/3_2.mp3', 2250, '台灣新創生態系統的發展', 'zh-TW');

-- 插入範例主題標籤
INSERT INTO episode_topics (episode_id, topic_tag) VALUES
(1, '人工智慧'),
(1, '科技趨勢'),
(2, '雲端運算'),
(2, '技術架構'),
(3, '領導力'),
(3, '管理技能'),
(4, '時間管理'),
(4, '工作效率'),
(5, '半導體'),
(5, '台灣產業'),
(6, '新創'),
(6, '創業');

-- 插入範例轉錄記錄
INSERT INTO transcripts (transcript_path, episode_id, transcript_length, language, model_used, version, created_by) VALUES
('podcast-transcripts/1_1.json', 1, 1800, 'zh', 'whisper-base', '1.0', 'auto_crawler'),
('podcast-transcripts/1_2.json', 2, 2100, 'zh', 'whisper-base', '1.0', 'auto_crawler'),
('podcast-transcripts/2_1.json', 3, 2400, 'zh', 'whisper-base', '1.0', 'auto_crawler'),
('podcast-transcripts/2_2.json', 4, 1950, 'zh', 'whisper-base', '1.0', 'auto_crawler'),
('podcast-transcripts/3_1.json', 5, 2700, 'zh', 'whisper-base', '1.0', 'auto_crawler'),
('podcast-transcripts/3_2.json', 6, 2250, 'zh', 'whisper-base', '1.0', 'auto_crawler');

-- 插入範例摘要
INSERT INTO summaries (episode_id, summary_text, summary_model, topics) VALUES
(1, '本集討論了人工智慧在2024年的主要發展趨勢，包括大型語言模型的進展、AI在企業中的應用，以及未來可能面臨的挑戰。', 'gpt-3.5-turbo', '["AI", "科技趨勢", "企業應用"]'),
(2, '深入探討雲端運算技術的演進，從基礎設施即服務到平台即服務，以及如何選擇適合的雲端解決方案。', 'gpt-3.5-turbo', '["雲端運算", "技術架構", "企業IT"]'),
(3, '分享有效的領導力培養方法，包括溝通技巧、決策制定、團隊管理等核心領導能力的建立。', 'gpt-3.5-turbo', '["領導力", "管理技能", "職場發展"]'),
(4, '提供實用的時間管理技巧，幫助聽眾提升工作效率，平衡工作與生活。', 'gpt-3.5-turbo', '["時間管理", "工作效率", "生活平衡"]'),
(5, '分析台灣半導體產業的現況，探討在全球供應鏈中的角色，以及未來發展機會。', 'gpt-3.5-turbo', '["半導體", "台灣產業", "全球供應鏈"]'),
(6, '介紹台灣新創生態系統的發展現況，分享成功案例和創業資源。', 'gpt-3.5-turbo', '["新創", "創業", "生態系統"]');

-- 插入範例機器學習主題分類
INSERT INTO topics (episode_id, topic_tag, source_type, confidence_score, classified_by) VALUES
(1, '人工智慧', 'ML', 0.95, 'bert-classifier'),
(1, '科技趨勢', 'ML', 0.88, 'bert-classifier'),
(2, '雲端運算', 'ML', 0.92, 'bert-classifier'),
(2, '技術架構', 'ML', 0.85, 'bert-classifier'),
(3, '領導力', 'ML', 0.90, 'bert-classifier'),
(3, '管理技能', 'ML', 0.87, 'bert-classifier'),
(4, '時間管理', 'ML', 0.93, 'bert-classifier'),
(4, '工作效率', 'ML', 0.89, 'bert-classifier'),
(5, '半導體', 'ML', 0.96, 'bert-classifier'),
(5, '台灣產業', 'ML', 0.91, 'bert-classifier'),
(6, '新創', 'ML', 0.94, 'bert-classifier'),
(6, '創業', 'ML', 0.86, 'bert-classifier');

-- 插入範例任務日誌
INSERT INTO task_log (task_id, task_type, episode_id, status, created_at, worker_id, triggered_by) VALUES
('task_001', 'transcription', 1, 'completed', '2024-01-15 10:00:00', 'worker_001', 'auto_crawler'),
('task_002', 'transcription', 2, 'completed', '2024-01-15 10:30:00', 'worker_001', 'auto_crawler'),
('task_003', 'transcription', 3, 'completed', '2024-01-15 11:00:00', 'worker_001', 'auto_crawler'),
('task_004', 'transcription', 4, 'completed', '2024-01-15 11:30:00', 'worker_001', 'auto_crawler'),
('task_005', 'transcription', 5, 'completed', '2024-01-15 12:00:00', 'worker_001', 'auto_crawler'),
('task_006', 'transcription', 6, 'completed', '2024-01-15 12:30:00', 'worker_001', 'auto_crawler');

-- 插入範例嵌入日誌
INSERT INTO embedding_log (episode_id, vector_type, vector_version, generated_at, vector_dim, worker_id, status) VALUES
(1, 'sentence', 'all-MiniLM-L6-v2', '2024-01-15 10:15:00', 384, 'worker_001', 'completed'),
(2, 'sentence', 'all-MiniLM-L6-v2', '2024-01-15 10:45:00', 384, 'worker_001', 'completed'),
(3, 'sentence', 'all-MiniLM-L6-v2', '2024-01-15 11:15:00', 384, 'worker_001', 'completed'),
(4, 'sentence', 'all-MiniLM-L6-v2', '2024-01-15 11:45:00', 384, 'worker_001', 'completed'),
(5, 'sentence', 'all-MiniLM-L6-v2', '2024-01-15 12:15:00', 384, 'worker_001', 'completed'),
(6, 'sentence', 'all-MiniLM-L6-v2', '2024-01-15 12:45:00', 384, 'worker_001', 'completed');

-- 插入範例攝取日誌
INSERT INTO ingestion_log (source_platform, rss_url, episode_id, status, ingested_at, normalized_json) VALUES
('apple_podcasts', 'https://feeds.simplecast.com/siliconvalley', 1, 'completed', '2024-01-15 09:00:00', '{"title": "矽谷輕鬆談 第 1 集", "duration": 1800}'),
('apple_podcasts', 'https://feeds.simplecast.com/siliconvalley', 2, 'completed', '2024-01-15 09:30:00', '{"title": "矽谷輕鬆談 第 2 集", "duration": 2100}'),
('apple_podcasts', 'https://feeds.simplecast.com/learning', 3, 'completed', '2024-01-15 10:00:00', '{"title": "天下學習 第 1 集", "duration": 2400}'),
('apple_podcasts', 'https://feeds.simplecast.com/learning', 4, 'completed', '2024-01-15 10:30:00', '{"title": "天下學習 第 2 集", "duration": 1950}'),
('apple_podcasts', 'https://feeds.simplecast.com/techisland', 5, 'completed', '2024-01-15 11:00:00', '{"title": "科技島讀 第 1 集", "duration": 2700}'),
('apple_podcasts', 'https://feeds.simplecast.com/techisland', 6, 'completed', '2024-01-15 11:30:00', '{"title": "科技島讀 第 2 集", "duration": 2250}');

-- 顯示建立的表格
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename; 