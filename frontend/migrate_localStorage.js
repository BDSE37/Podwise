/**
 * migrate_localStorage.js
 * 用於處理 localStorage 數據遷移和兼容性
 */

(function() {
    'use strict';
    
    // 檢查是否已經執行過遷移
    if (localStorage.getItem('migration_completed')) {
        return;
    }
    
    console.log('🔄 開始 localStorage 數據遷移...');
    
    // 遷移舊版本的用戶數據
    function migrateUserData() {
        const oldUserId = localStorage.getItem('userId');
        const oldUserPreferences = localStorage.getItem('userPreferences');
        
        if (oldUserId && !localStorage.getItem('currentUserId')) {
            localStorage.setItem('currentUserId', oldUserId);
            console.log('✅ 遷移用戶 ID:', oldUserId);
        }
        
        if (oldUserPreferences && !localStorage.getItem('userPreferences')) {
            try {
                const preferences = JSON.parse(oldUserPreferences);
                localStorage.setItem('userPreferences', oldUserPreferences);
                console.log('✅ 遷移用戶偏好設定');
            } catch (e) {
                console.warn('⚠️ 用戶偏好設定格式錯誤，跳過遷移');
            }
        }
    }
    
    // 遷移聊天歷史
    function migrateChatHistory() {
        const oldChatHistory = localStorage.getItem('chatHistory');
        
        if (oldChatHistory && !localStorage.getItem('chatHistory')) {
            try {
                const history = JSON.parse(oldChatHistory);
                localStorage.setItem('chatHistory', oldChatHistory);
                console.log('✅ 遷移聊天歷史');
            } catch (e) {
                console.warn('⚠️ 聊天歷史格式錯誤，跳過遷移');
            }
        }
    }
    
    // 遷移 TTS 設定
    function migrateTTSSettings() {
        const oldVoice = localStorage.getItem('selectedVoice');
        const oldSpeed = localStorage.getItem('voiceSpeed');
        const oldTTSEnabled = localStorage.getItem('ttsEnabled');
        
        if (oldVoice && !localStorage.getItem('selectedVoice')) {
            localStorage.setItem('selectedVoice', oldVoice);
            console.log('✅ 遷移語音設定:', oldVoice);
        }
        
        if (oldSpeed && !localStorage.getItem('voiceSpeed')) {
            localStorage.setItem('voiceSpeed', oldSpeed);
            console.log('✅ 遷移語速設定:', oldSpeed);
        }
        
        if (oldTTSEnabled && !localStorage.getItem('ttsEnabled')) {
            localStorage.setItem('ttsEnabled', oldTTSEnabled);
            console.log('✅ 遷移 TTS 開關設定:', oldTTSEnabled);
        }
    }
    
    // 清理過期的數據
    function cleanupOldData() {
        const keysToRemove = [
            'temp_audio_data',
            'temp_chat_data',
            'session_data'
        ];
        
        keysToRemove.forEach(key => {
            if (localStorage.getItem(key)) {
                localStorage.removeItem(key);
                console.log('🗑️ 清理過期數據:', key);
            }
        });
    }
    
    // 設置默認值
    function setDefaults() {
        const defaults = {
            'selectedVoice': 'podrina',
            'voiceSpeed': '1.0',
            'ttsEnabled': 'true',
            'theme': 'light',
            'language': 'zh-TW'
        };
        
        Object.entries(defaults).forEach(([key, value]) => {
            if (!localStorage.getItem(key)) {
                localStorage.setItem(key, value);
                console.log('📝 設置默認值:', key, '=', value);
            }
        });
    }
    
    // 執行遷移
    try {
        migrateUserData();
        migrateChatHistory();
        migrateTTSSettings();
        cleanupOldData();
        setDefaults();
        
        // 標記遷移完成
        localStorage.setItem('migration_completed', 'true');
        localStorage.setItem('migration_date', new Date().toISOString());
        
        console.log('✅ localStorage 數據遷移完成');
        
    } catch (error) {
        console.error('❌ 數據遷移失敗:', error);
    }
    
    // 提供全局函數供其他腳本使用
    window.PodwiseStorage = {
        // 獲取用戶 ID
        getUserId: function() {
            return localStorage.getItem('currentUserId') || localStorage.getItem('userId');
        },
        
        // 設置用戶 ID
        setUserId: function(userId) {
            localStorage.setItem('currentUserId', userId);
            localStorage.setItem('userId', userId); // 保持向後兼容
        },
        
        // 獲取用戶偏好設定
        getUserPreferences: function() {
            const prefs = localStorage.getItem('userPreferences');
            return prefs ? JSON.parse(prefs) : {};
        },
        
        // 設置用戶偏好設定
        setUserPreferences: function(preferences) {
            localStorage.setItem('userPreferences', JSON.stringify(preferences));
        },
        
        // 獲取聊天歷史
        getChatHistory: function() {
            const history = localStorage.getItem('chatHistory');
            return history ? JSON.parse(history) : [];
        },
        
        // 添加聊天記錄
        addChatMessage: function(message) {
            const history = this.getChatHistory();
            history.push({
                ...message,
                timestamp: new Date().toISOString()
            });
            
            // 只保留最近 100 條記錄
            if (history.length > 100) {
                history.splice(0, history.length - 100);
            }
            
            localStorage.setItem('chatHistory', JSON.stringify(history));
        },
        
        // 獲取 TTS 設定
        getTTSSettings: function() {
            return {
                voice: localStorage.getItem('selectedVoice') || 'podrina',
                speed: parseFloat(localStorage.getItem('voiceSpeed') || '1.0'),
                enabled: localStorage.getItem('ttsEnabled') !== 'false'
            };
        },
        
        // 設置 TTS 設定
        setTTSSettings: function(settings) {
            if (settings.voice) localStorage.setItem('selectedVoice', settings.voice);
            if (settings.speed) localStorage.setItem('voiceSpeed', settings.speed.toString());
            if (settings.enabled !== undefined) localStorage.setItem('ttsEnabled', settings.enabled.toString());
        },
        
        // 清除所有數據
        clearAll: function() {
            localStorage.clear();
            console.log('🗑️ 已清除所有 localStorage 數據');
        },
        
        // 導出數據
        exportData: function() {
            const data = {};
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                data[key] = localStorage.getItem(key);
            }
            return data;
        },
        
        // 導入數據
        importData: function(data) {
            Object.entries(data).forEach(([key, value]) => {
                localStorage.setItem(key, value);
            });
            console.log('📥 數據導入完成');
        }
    };
    
})(); 