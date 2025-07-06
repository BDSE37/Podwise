#!/bin/bash

# Episodes 處理自動化腳本
# 清理表情符號並將資料插入 PostgreSQL 資料庫

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 腳本目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查 Python 環境
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安裝"
        exit 1
    fi
    
    log_info "Python3 版本: $(python3 --version)"
}

# 檢查依賴套件
check_dependencies() {
    log_info "檢查依賴套件..."
    
    if ! python3 -c "import psycopg2" 2>/dev/null; then
        log_warning "psycopg2 未安裝，正在安裝..."
        pip3 install psycopg2-binary
    fi
    
    if ! python3 -c "import json" 2>/dev/null; then
        log_error "json 模組不可用"
        exit 1
    fi
    
    log_success "依賴套件檢查完成"
}

# 建立輸出目錄
create_output_dir() {
    OUTPUT_DIR="processed_episodes"
    mkdir -p "$OUTPUT_DIR"
    log_info "輸出目錄: $OUTPUT_DIR"
}

# 建立資料庫表格
create_database_tables() {
    log_info "建立資料庫表格..."
    
    if [ -f "create_episode_table.sql" ]; then
        # 使用 psql 執行 SQL 腳本
        if command -v psql &> /dev/null; then
            # 從 config.py 讀取資料庫連線資訊
            DB_HOST=$(python3 -c "from config import config; print(config['database']['host'])")
            DB_PORT=$(python3 -c "from config import config; print(config['database']['port'])")
            DB_NAME=$(python3 -c "from config import config; print(config['database']['name'])")
            DB_USER=$(python3 -c "from config import config; print(config['database']['user'])")
            DB_PASS=$(python3 -c "from config import config; print(config['database']['password'])")
            
            export PGPASSWORD="$DB_PASS"
            psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f create_episode_table.sql
            log_success "資料庫表格建立完成"
        else
            log_warning "psql 未安裝，跳過資料庫表格建立"
        fi
    else
        log_warning "create_episode_table.sql 不存在"
    fi
}

# 處理 episodes 資料
process_episodes() {
    local CHANNEL=${1:-"all"}
    local INSERT_DB=${2:-"false"}
    
    log_info "開始處理 episodes 資料..."
    log_info "頻道: $CHANNEL"
    log_info "插入資料庫: $INSERT_DB"
    
    # 檢查 episodes 目錄
    if [ ! -d "episodes" ]; then
        log_error "episodes 目錄不存在"
        exit 1
    fi
    
    # 執行 Python 處理腳本
    local PYTHON_CMD="python3 episode_processor.py --episodes-dir episodes --output-dir processed_episodes"
    
    if [ "$CHANNEL" != "all" ]; then
        PYTHON_CMD="$PYTHON_CMD --channel $CHANNEL"
    fi
    
    if [ "$INSERT_DB" = "true" ]; then
        PYTHON_CMD="$PYTHON_CMD --insert-db"
    fi
    
    log_info "執行命令: $PYTHON_CMD"
    
    if eval "$PYTHON_CMD"; then
        log_success "Episodes 處理完成"
    else
        log_error "Episodes 處理失敗"
        exit 1
    fi
}

# 顯示統計資訊
show_statistics() {
    log_info "顯示處理統計資訊..."
    
    if [ -d "processed_episodes" ]; then
        echo "=== 處理結果統計 ==="
        
        # 計算各頻道檔案數量
        if [ -f "processed_episodes/business_processed.json" ]; then
            BUSINESS_COUNT=$(python3 -c "import json; print(len(json.load(open('processed_episodes/business_processed.json'))))")
            echo "商業頻道: $BUSINESS_COUNT 筆"
        fi
        
        if [ -f "processed_episodes/evucation_processed.json" ]; then
            EVUCATION_COUNT=$(python3 -c "import json; print(len(json.load(open('processed_episodes/evucation_processed.json'))))")
            echo "教育頻道: $EVUCATION_COUNT 筆"
        fi
        
        if [ -f "processed_episodes/all_episodes_processed.json" ]; then
            TOTAL_COUNT=$(python3 -c "import json; print(len(json.load(open('processed_episodes/all_episodes_processed.json'))))")
            echo "總計: $TOTAL_COUNT 筆"
        fi
    fi
}

# 清理功能
cleanup_old_data() {
    log_info "清理舊資料..."
    
    # 清理超過 30 天的處理檔案
    find processed_episodes -name "*.json" -mtime +30 -delete 2>/dev/null || true
    
    log_success "清理完成"
}

# 顯示使用說明
show_usage() {
    echo "使用方法: $0 [選項]"
    echo ""
    echo "選項:"
    echo "  -c, --channel CHANNEL    指定頻道 (business|evucation|all) [預設: all]"
    echo "  -d, --database           插入資料庫"
    echo "  -s, --statistics         顯示統計資訊"
    echo "  -l, --cleanup            清理舊資料"
    echo "  -h, --help               顯示此說明"
    echo ""
    echo "範例:"
    echo "  $0                       處理所有頻道，僅輸出檔案"
    echo "  $0 -c business -d        處理商業頻道並插入資料庫"
    echo "  $0 -c evucation          處理教育頻道"
    echo "  $0 -s                    顯示統計資訊"
    echo "  $0 -l                    清理舊資料"
}

# 主函數
main() {
    local CHANNEL="all"
    local INSERT_DB="false"
    local SHOW_STATS="false"
    local CLEANUP="false"
    
    # 解析命令列參數
    while [[ $# -gt 0 ]]; do
        case $1 in
            -c|--channel)
                CHANNEL="$2"
                shift 2
                ;;
            -d|--database)
                INSERT_DB="true"
                shift
                ;;
            -s|--statistics)
                SHOW_STATS="true"
                shift
                ;;
            -l|--cleanup)
                CLEANUP="true"
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                log_error "未知參數: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # 顯示標題
    echo "=========================================="
    echo "    Episodes 資料處理工具"
    echo "=========================================="
    echo ""
    
    # 檢查環境
    check_python
    check_dependencies
    
    # 建立輸出目錄
    create_output_dir
    
    # 根據參數執行相應功能
    if [ "$CLEANUP" = "true" ]; then
        cleanup_old_data
    elif [ "$SHOW_STATS" = "true" ]; then
        show_statistics
    else
        # 建立資料庫表格
        create_database_tables
        
        # 處理 episodes
        process_episodes "$CHANNEL" "$INSERT_DB"
        
        # 顯示統計資訊
        show_statistics
    fi
    
    log_success "所有操作完成！"
}

# 執行主函數
main "$@" 