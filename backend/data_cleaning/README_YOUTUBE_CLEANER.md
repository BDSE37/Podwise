# YouTube 清理器使用指南

## 概述

通用 YouTube 清理器 (`YouTubeCleaner`) 是一個專門處理任何 YouTube 頻道資料的清理工具，可以自動識別和清理 YouTube 格式的 JSON 資料。**支援自定義配置，可以靈活控制哪些欄位需要清理。**

## 功能特色

### 自動識別 YouTube 資料
- 檢查是否有 YouTube 特有欄位：`view_count`, `like_count`, `comment_count`, `comments`
- 檢查 URL 是否包含 YouTube 域名
- 檢查標題是否包含 YouTube 相關關鍵字

### 可配置的清理功能
1. **標題清理**
   - 移除表情符號和特殊符號
   - 移除 YouTube 特有標記（如【】、🔥、💡等）
   - 標準化標題格式

2. **作者清理**
   - 移除官方標記（如 "Official"、"官方唯一頻道"）
   - 清理特殊符號

3. **數據清理**
   - 觀看次數：移除 "觀看次數：" 前綴和 "次" 後綴
   - 按讚數：只保留數字
   - 評論數：標準化為整數
   - 評論內容：清理特殊符號和表情

4. **自定義欄位清理**
   - 支援添加任意欄位進行清理
   - 可選擇清理類型：`title`, `author`, `number`, `list`, `text`
   - 可啟用/停用特定欄位的清理

## 支援的資料格式

```json
{
  "url": "https://www.youtube.com/watch?v=xxx",
  "title": "影片標題",
  "author": "頻道名稱",
  "view_count": "觀看次數：1234次",
  "like_count": "56",
  "comment_count": 7,
  "comments": ["評論1", "評論2"],
  "description": "影片描述",
  "content": "影片內容",
  "tags": ["標籤1", "標籤2"],
  "category": "分類",
  "duration": "15分鐘"
}
```

## 使用方法

### 1. 使用預設配置

```python
from core.youtube_cleaner import YouTubeCleaner

# 建立清理器（使用預設配置）
cleaner = YouTubeCleaner()

# 清理單筆資料
cleaned_data = cleaner.clean(youtube_data)

# 批次清理
cleaned_list = cleaner.batch_clean_documents(youtube_data_list)
```

### 2. 使用自定義配置

```python
# 自定義配置
custom_config = {
    "fields_to_clean": {
        "title": {
            "enabled": True,
            "clean_type": "title",
            "description": "清理標題"
        },
        "author": {
            "enabled": True,
            "clean_type": "author",
            "description": "清理作者"
        },
        "view_count": {
            "enabled": False,  # 停用觀看次數清理
            "clean_type": "number"
        },
        "custom_field": {  # 添加自定義欄位
            "enabled": True,
            "clean_type": "text",
            "description": "自定義欄位清理"
        }
    }
}

# 使用自定義配置建立清理器
cleaner = YouTubeCleaner(custom_config)
cleaned_data = cleaner.clean(youtube_data)
```

### 3. 從檔案載入配置

```python
import json

# 載入配置檔案
with open("config/youtube_cleaner_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

# 使用檔案配置建立清理器
cleaner = YouTubeCleaner(config)
cleaned_data = cleaner.clean(youtube_data)
```

### 4. 動態配置管理

```python
cleaner = YouTubeCleaner()

# 添加自定義欄位
cleaner.add_custom_field("user_rating", {
    "enabled": True,
    "clean_type": "number",
    "description": "用戶評分"
})

# 更新配置
cleaner.update_config({
    "fields_to_clean": {
        "title": {"enabled": False}  # 停用標題清理
    }
})

# 移除欄位
cleaner.remove_field("user_rating")

# 取得當前配置
current_config = cleaner.get_config()
```

### 5. 使用批次清理腳本

```bash
# 清理指定資料夾中的所有 JSON 檔案
python batch_clean_folder.py --input-folder backend/data_cleaning/batch_input

# 指定輸出資料夾
python batch_clean_folder.py --input-folder backend/data_cleaning/batch_input --output-folder ../../data/cleaned_data
```

### 6. 使用清理協調器

```python
from services.cleaner_orchestrator import CleanerOrchestrator

# 建立協調器
orchestrator = CleanerOrchestrator()

# 自動偵測格式並清理
output_path = orchestrator.clean_file("youtube_data.json")
```

## 配置選項

### 欄位配置 (`fields_to_clean`)

每個欄位可以配置以下選項：

- `enabled`: 是否啟用清理（布林值）
- `clean_type`: 清理類型
  - `title`: 標題清理（移除表情符號和特殊標記）
  - `author`: 作者清理（移除官方標記）
  - `number`: 數字清理（標準化為數字）
  - `list`: 列表清理（清理列表中的每個項目）
  - `text`: 文本清理（一般文本清理）
- `description`: 欄位描述

### 清理規則配置

#### 標題清理規則 (`title_clean_rules`)
- `remove_emoji`: 是否移除表情符號
- `remove_special_symbols`: 是否移除特殊符號
- `remove_youtube_patterns`: 是否移除 YouTube 特有模式
- `normalize_format`: 是否標準化格式

#### 作者清理規則 (`author_clean_rules`)
- `remove_official_tags`: 是否移除官方標記
- `remove_special_symbols`: 是否移除特殊符號

#### 數字清理規則 (`number_clean_rules`)
- `remove_prefixes`: 要移除的前綴列表
- `remove_suffixes`: 要移除的後綴列表
- `extract_numbers_only`: 是否只保留數字

#### 評論清理規則 (`comment_clean_rules`)
- `remove_emoji`: 是否移除表情符號
- `remove_special_symbols`: 是否移除特殊符號
- `normalize_text`: 是否標準化文本

## 測試

### 運行基本測試

```bash
cd backend/data_cleaning
python test_youtube_cleaner.py
```

### 運行自定義配置測試

```bash
cd backend/data_cleaning
python test_custom_youtube_cleaner.py
```

### 測試批次清理

1. 將 YouTube JSON 檔案放入 `batch_input` 資料夾
2. 執行批次清理腳本
3. 檢查 `../../data/cleaned_data` 資料夾中的結果

## 清理範例

### 輸入資料
```json
{
  "url": "https://www.youtube.com/watch?v=zqL_-9_RY_I",
  "title": "🚩 【吳淡如Ｘ林香蘭】礦工女兒高商畢業如何成為執行長？",
  "author": "吳淡如人生實用商學院（Official官方唯一頻道）",
  "view_count": "觀看次數：3378次",
  "like_count": "75",
  "comment_count": 1,
  "comments": ["已訂購娘家產品，期待"],
  "description": "這是一個關於成功故事的影片 🎯",
  "tags": ["成功", "創業", "勵志 💪"]
}
```

### 輸出資料（預設配置）
```json
{
  "url": "https://www.youtube.com/watch?v=zqL_-9_RY_I",
  "title": "礦工女兒高商畢業如何成為執行長",
  "author": "吳淡如人生實用商學院",
  "view_count": "3378",
  "like_count": "75",
  "comment_count": 1,
  "comments": ["已訂購娘家產品，期待"],
  "description": "這是一個關於成功故事的影片",
  "tags": ["成功", "創業", "勵志"],
  "cleaned_at": "2024-01-01T12:00:00",
  "cleaning_status": "completed",
  "cleaner_type": "youtube_general_specialized",
  "cleaning_config": {
    "fields_cleaned": ["title", "author", "view_count", "like_count", "comment_count", "comments"],
    "config_version": "1.0"
  }
}
```

### 輸出資料（自定義配置 - 只清理標題和作者）
```json
{
  "url": "https://www.youtube.com/watch?v=zqL_-9_RY_I",
  "title": "礦工女兒高商畢業如何成為執行長",
  "author": "吳淡如人生實用商學院",
  "view_count": "觀看次數：3378次",
  "like_count": "75",
  "comment_count": 1,
  "comments": ["已訂購娘家產品，期待"],
  "description": "這是一個關於成功故事的影片 🎯",
  "tags": ["成功", "創業", "勵志 💪"],
  "cleaned_at": "2024-01-01T12:00:00",
  "cleaning_status": "completed",
  "cleaner_type": "youtube_general_specialized",
  "cleaning_config": {
    "fields_cleaned": ["title", "author"],
    "config_version": "1.0"
  }
}
```

## 整合到現有系統

YouTube 清理器已經整合到 `CleanerOrchestrator` 中，會自動偵測 YouTube 格式的資料並使用適當的清理器。

### 清理優先順序
1. 股癌資料（StockCancerCleaner）
2. YouTube 資料（YouTubeCleaner）
3. MongoDB 資料（MongoCleaner）
4. 一般資料（其他清理器）

## 進階用法

### 創建專用配置檔案

```json
{
  "fields_to_clean": {
    "title": {"enabled": true, "clean_type": "title"},
    "author": {"enabled": true, "clean_type": "author"},
    "description": {"enabled": true, "clean_type": "text"},
    "custom_rating": {"enabled": true, "clean_type": "number"},
    "user_tags": {"enabled": true, "clean_type": "list"}
  },
  "title_clean_rules": {
    "remove_emoji": true,
    "remove_youtube_patterns": true
  }
}
```

### 批量處理不同配置

```python
# 為不同類型的資料使用不同配置
configs = {
    "basic": {"fields_to_clean": {"title": {"enabled": True}, "author": {"enabled": True}}},
    "full": {"fields_to_clean": {"title": {"enabled": True}, "author": {"enabled": True}, "description": {"enabled": True}}}
}

for config_name, config in configs.items():
    cleaner = YouTubeCleaner(config)
    # 處理對應的資料...
```

## 注意事項

1. **資料格式**：確保 JSON 資料包含必要的 YouTube 欄位
2. **編碼**：使用 UTF-8 編碼以正確處理中文和表情符號
3. **批次處理**：大量資料建議使用批次清理功能
4. **備份**：清理前建議備份原始資料
5. **配置管理**：建議將常用配置保存為檔案，方便重複使用

## 擴展功能

如需支援其他特殊格式或清理規則，可以：
1. 繼承 `BaseCleaner` 類別
2. 實作 `clean()` 方法
3. 在 `CleanerOrchestrator` 中添加新的識別邏輯
4. 使用自定義配置來控制清理行為 