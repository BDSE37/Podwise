# Vector Pipeline

統一的向量化處理管道，整合所有核心功能，遵循 Google Clean Code 原則和 OOP 架構。

## 架構概覽

```
vector_pipeline/
├── main.py                    # 主程式入口
├── enhanced_tagging.py        # 增強版標籤處理器（主程式）
├── core/                      # 核心模組
│   ├── __init__.py
│   ├── tag_processor.py       # 統一標籤處理器
│   ├── batch_processor.py     # 批次處理器
│   ├── text_chunker.py        # 文本分塊器（以換行符分段）
│   ├── mongo_processor.py     # MongoDB 處理器
│   ├── milvus_writer.py       # Milvus 寫入器
│   ├── vector_processor.py    # 向量處理器
│   ├── pipeline_stages.py     # 管道階段處理器
│   └── error_logger.py        # 錯誤記錄器
├── utils/                     # 工具模組
│   ├── __init__.py
│   └── data_quality_checker.py # 資料品質檢查器
└── tests/                     # 測試模組
    ├── __init__.py
    └── test_enhanced_integration.py
```

## 核心功能

### 1. 統一標籤處理器 (`core/tag_processor.py`)
- **優先使用 TAG_info.csv**：首先查詢預定義標籤
- **智能標籤提取**：使用 `tag_processor.py` 的 SmartTagExtractor
- **增強版處理器**：整合 MoneyDJ 百科和專業術語
- **支援 1-3 個標籤**：根據內容類型自動調整

### 2. 文本分塊器 (`core/text_chunker.py`)
- **以換行符分段**：優先按換行符切分長文本
- **智能分塊**：處理超長段落
- **重疊設計**：確保上下文連續性

### 3. 批次處理器 (`core/batch_processor.py`)
- **多 RSS 資料夾處理**：並行處理多個資料夾
- **進度追蹤**：實時顯示處理進度
- **錯誤處理**：詳細的錯誤記錄和恢復

### 4. 資料品質檢查器 (`utils/data_quality_checker.py`)
- **Exclamation 檔案檢查**：識別問題檔案
- **STT 檔案檢查**：驗證語音轉文字品質
- **報告生成**：JSON 和 CSV 格式報告

## 使用方式

### 基本使用

```python
from vector_pipeline import VectorPipeline

# 初始化管道
pipeline = VectorPipeline()

# 處理所有 RSS 資料夾
results = pipeline.process_all_rss_folders()

# 處理單一 RSS 資料夾
stats = pipeline.process_single_rss_folder("RSS_1234567890")

# 測試標籤系統
pipeline.test_tagging_system()
```

### 命令列使用

```bash
# 顯示處理狀態
python main.py status

# 測試標籤系統
python main.py test

# 處理單一 RSS 資料夾
python main.py single RSS_1234567890

# 處理所有 RSS 資料夾
python main.py all
```

### 直接使用增強版標籤處理器

```python
from enhanced_tagging import EnhancedTagProcessor

# 初始化處理器
processor = EnhancedTagProcessor("path/to/TAG_info.csv")

# 提取標籤
text = "AI人工智慧技術正在改變世界"
tags = processor.extract_enhanced_tags(text)
print(f"標籤: {tags}")
```

### 資料品質檢查

```python
from utils.data_quality_checker import DataQualityChecker

# 初始化檢查器
checker = DataQualityChecker()

# 檢查 exclamation 檔案
stats = checker.check_exclamation_files()

# 生成報告
report_file = checker.generate_report(stats, "exclamation")
txt_file = checker.save_exclamation_list_to_txt(stats)

# 打印摘要
checker.print_report_summary(stats)
```

## 配置要求

### 環境變數
```bash
# MongoDB 配置
MONGO_HOST=192.168.32.86
MONGO_PORT=30017
MONGO_USERNAME=bdse37
MONGO_PASSWORD=111111
MONGO_DATABASE=podcast

# PostgreSQL 配置
POSTGRES_HOST=192.168.32.86
POSTGRES_PORT=5432
POSTGRES_USERNAME=bdse37
POSTGRES_PASSWORD=111111
POSTGRES_DATABASE=podcast

# Milvus 配置
MILVUS_HOST=192.168.32.86
MILVUS_PORT=19530
```

### 依賴套件
```bash
pip install pymongo psycopg2-binary pymilvus transformers torch numpy pandas
```

## 整合原則

### 1. 功能整合
- **每個功能只有一份**：避免重複實現
- **統一介面**：所有模組使用一致的 API
- **模組化設計**：易於維護和擴展

### 2. 架構一致性
- **與 backend 其他資料夾一致**：遵循相同的目錄結構
- **OOP 設計**：所有功能以類別形式實現
- **Google Clean Code**：遵循最佳實踐

### 3. 標籤處理策略
- **優先使用 TAG_info.csv**：確保標籤一致性
- **智能備援**：當 CSV 中沒有匹配時使用智能提取
- **增強版處理**：整合多個專業術語來源

### 4. 文本分塊策略
- **換行符優先**：保持語義完整性
- **長文本處理**：智能處理超長段落
- **重疊設計**：確保上下文連續性

## 錯誤處理

### 錯誤記錄
- **詳細記錄**：記錄所有處理階段的錯誤
- **分類統計**：按錯誤類型統計
- **恢復機制**：支援錯誤恢復和重試

### 資料品質
- **自動檢查**：識別問題檔案
- **報告生成**：詳細的問題報告
- **處理建議**：提供解決方案建議

## 測試

### 整合測試
```bash
# 執行整合測試
python tests/test_enhanced_integration.py
```

### 單元測試
```bash
# 測試標籤處理器
python -m pytest tests/ -v
```

## 維護說明

### 新增功能
1. 在適當的模組中添加功能
2. 更新 `__init__.py` 文件
3. 添加對應的測試
4. 更新 README 文檔

### 修改現有功能
1. 確保向後相容性
2. 更新相關測試
3. 更新文檔說明

### 錯誤修復
1. 在 `core/error_logger.py` 中記錄錯誤
2. 添加錯誤處理邏輯
3. 更新測試案例

## 版本歷史

### v2.0.0 (整合版本)
- 整合所有重複功能
- 統一架構設計
- 增強標籤處理
- 改進文本分塊
- 新增資料品質檢查

### v1.0.0 (初始版本)
- 基本向量化功能
- 標籤處理
- MongoDB 整合
- Milvus 寫入 