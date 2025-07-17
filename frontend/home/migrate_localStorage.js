// migrate_localStorage.js
// 用於處理 localStorage 遷移和用戶數據管理

(function() {
    'use strict';
    
    // 檢查並遷移舊版本的 localStorage 數據
    function migrateLocalStorage() {
        console.log('檢查 localStorage 遷移...');
        
        // 檢查是否有舊版本的用戶數據
        const oldUserId = localStorage.getItem('userId');
        if (oldUserId && !localStorage.getItem('currentUserId')) {
            localStorage.setItem('currentUserId', oldUserId);
            localStorage.removeItem('userId');
            console.log('已遷移舊版本用戶ID:', oldUserId);
        }
        
        // 檢查 onboarding 狀態
        if (!localStorage.getItem('onboardingCompleted')) {
            localStorage.setItem('onboardingCompleted', 'false');
        }
        
        // 檢查用戶偏好設定
        if (!localStorage.getItem('userPreferences')) {
            localStorage.setItem('userPreferences', JSON.stringify({
                mainCategory: 'business',
                preferredTags: [],
                ttsEnabled: true,
                voiceModel: 'podrina',
                speed: 1.0
            }));
        }
        
        console.log('localStorage 遷移完成');
    }
    
    // 用戶數據管理函數
    window.userDataManager = {
        // 獲取當前用戶ID
        getCurrentUserId: function() {
            return localStorage.getItem('currentUserId') || 'default_user';
        },
        
        // 設置當前用戶ID
        setCurrentUserId: function(userId) {
            localStorage.setItem('currentUserId', userId);
            console.log('設置用戶ID:', userId);
        },
        
        // 檢查是否完成 onboarding
        isOnboarded: function() {
            return localStorage.getItem('onboardingCompleted') === 'true';
        },
        
        // 設置 onboarding 完成
        setOnboarded: function() {
            localStorage.setItem('onboardingCompleted', 'true');
            console.log('設置 onboarding 完成');
        },
        
        // 獲取用戶偏好設定
        getPreferences: function() {
            try {
                return JSON.parse(localStorage.getItem('userPreferences') || '{}');
            } catch (e) {
                return {};
            }
        },
        
        // 設置用戶偏好設定
        setPreferences: function(preferences) {
            localStorage.setItem('userPreferences', JSON.stringify(preferences));
            console.log('更新用戶偏好設定:', preferences);
        },
        
        // 清除所有用戶數據
        clearAll: function() {
            localStorage.clear();
            console.log('已清除所有用戶數據');
        }
    };
    
    // 頁面載入時執行遷移
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', migrateLocalStorage);
    } else {
        migrateLocalStorage();
    }
    
})(); 