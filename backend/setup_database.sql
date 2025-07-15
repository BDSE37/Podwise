-- Podwise 四步驟功能資料庫設置腳本

-- 創建用戶偏好表
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id),
    category VARCHAR(50) NOT NULL,
    preference_score FLOAT DEFAULT 0.8,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, category)
);

-- 為現有的 users 表添加 user_code 欄位（如果不存在）
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'user_code') THEN
        ALTER TABLE users ADD COLUMN user_code VARCHAR(50) UNIQUE;
    END IF;
END $$;

-- 創建索引
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_category ON user_preferences(category);
CREATE INDEX IF NOT EXISTS idx_users_user_code ON users(user_code);

-- 插入一些測試數據
INSERT INTO users (user_id, user_code, is_active, created_at, updated_at) 
VALUES 
    ('test_user_1', 'Podwise_0001', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('test_user_2', 'Podwise_0002', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (user_id) DO NOTHING;

-- 顯示表結構
\d users
\d user_preferences
\d user_feedback 