-- Episode Metadata 表格建立腳本
-- 用於儲存處理後的 episodes 資料

CREATE TABLE IF NOT EXISTS episode_metadata (
    id SERIAL PRIMARY KEY,
    episode_id VARCHAR(255) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    audio_url TEXT,
    published_date VARCHAR(100),
    published_timestamp TIMESTAMP,
    published_year INTEGER,
    published_month INTEGER,
    published_day INTEGER,
    channel_id VARCHAR(50) NOT NULL,
    channel_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    episode_number VARCHAR(20),
    processed_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 建立索引以提升查詢效能
CREATE INDEX IF NOT EXISTS idx_episode_metadata_channel_id ON episode_metadata(channel_id);
CREATE INDEX IF NOT EXISTS idx_episode_metadata_category ON episode_metadata(category);
CREATE INDEX IF NOT EXISTS idx_episode_metadata_published_year ON episode_metadata(published_year);
CREATE INDEX IF NOT EXISTS idx_episode_metadata_episode_number ON episode_metadata(episode_number);
CREATE INDEX IF NOT EXISTS idx_episode_metadata_published_timestamp ON episode_metadata(published_timestamp);

-- 建立複合索引
CREATE INDEX IF NOT EXISTS idx_episode_metadata_channel_published ON episode_metadata(channel_id, published_timestamp);

-- 建立全文搜尋索引
CREATE INDEX IF NOT EXISTS idx_episode_metadata_title_gin ON episode_metadata USING gin(to_tsvector('chinese', title));
CREATE INDEX IF NOT EXISTS idx_episode_metadata_description_gin ON episode_metadata USING gin(to_tsvector('chinese', description));

-- 建立觸發器自動更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_episode_metadata_updated_at 
    BEFORE UPDATE ON episode_metadata 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 建立統計資訊表格
CREATE TABLE IF NOT EXISTS episode_statistics (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(50) NOT NULL,
    channel_name VARCHAR(100) NOT NULL,
    total_episodes INTEGER DEFAULT 0,
    latest_episode_date TIMESTAMP,
    earliest_episode_date TIMESTAMP,
    last_updated TIMESTAMP DEFAULT NOW()
);

-- 建立統計資訊更新函數
CREATE OR REPLACE FUNCTION update_episode_statistics()
RETURNS TRIGGER AS $$
BEGIN
    -- 更新統計資訊
    INSERT INTO episode_statistics (channel_id, channel_name, total_episodes, latest_episode_date, earliest_episode_date, last_updated)
    VALUES (
        NEW.channel_id,
        NEW.channel_name,
        (SELECT COUNT(*) FROM episode_metadata WHERE channel_id = NEW.channel_id),
        (SELECT MAX(published_timestamp) FROM episode_metadata WHERE channel_id = NEW.channel_id),
        (SELECT MIN(published_timestamp) FROM episode_metadata WHERE channel_id = NEW.channel_id),
        NOW()
    )
    ON CONFLICT (channel_id) DO UPDATE SET
        total_episodes = EXCLUDED.total_episodes,
        latest_episode_date = EXCLUDED.latest_episode_date,
        earliest_episode_date = EXCLUDED.earliest_episode_date,
        last_updated = NOW();
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 建立統計資訊觸發器
CREATE TRIGGER update_episode_statistics_trigger
    AFTER INSERT OR UPDATE ON episode_metadata
    FOR EACH ROW
    EXECUTE FUNCTION update_episode_statistics();

-- 建立查詢視圖
CREATE OR REPLACE VIEW episode_summary AS
SELECT 
    channel_id,
    channel_name,
    category,
    COUNT(*) as episode_count,
    MIN(published_timestamp) as first_episode,
    MAX(published_timestamp) as latest_episode,
    AVG(EXTRACT(EPOCH FROM (published_timestamp - LAG(published_timestamp) OVER (PARTITION BY channel_id ORDER BY published_timestamp)))) / 86400 as avg_days_between_episodes
FROM episode_metadata
WHERE published_timestamp IS NOT NULL
GROUP BY channel_id, channel_name, category;

-- 建立清理函數
CREATE OR REPLACE FUNCTION cleanup_episode_metadata(
    p_channel_id VARCHAR(50) DEFAULT NULL,
    p_days_old INTEGER DEFAULT 365
)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    IF p_channel_id IS NOT NULL THEN
        DELETE FROM episode_metadata 
        WHERE channel_id = p_channel_id 
        AND published_timestamp < NOW() - INTERVAL '1 day' * p_days_old;
    ELSE
        DELETE FROM episode_metadata 
        WHERE published_timestamp < NOW() - INTERVAL '1 day' * p_days_old;
    END IF;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 建立查詢函數
CREATE OR REPLACE FUNCTION search_episodes(
    p_search_term TEXT,
    p_channel_id VARCHAR(50) DEFAULT NULL,
    p_limit INTEGER DEFAULT 50
)
RETURNS TABLE (
    episode_id VARCHAR(255),
    title TEXT,
    description TEXT,
    channel_name VARCHAR(100),
    published_timestamp TIMESTAMP,
    episode_number VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        em.episode_id,
        em.title,
        em.description,
        em.channel_name,
        em.published_timestamp,
        em.episode_number
    FROM episode_metadata em
    WHERE (
        em.title ILIKE '%' || p_search_term || '%' OR
        em.description ILIKE '%' || p_search_term || '%'
    )
    AND (p_channel_id IS NULL OR em.channel_id = p_channel_id)
    ORDER BY em.published_timestamp DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql; 