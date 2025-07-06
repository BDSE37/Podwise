#!/bin/bash

# 快速清理腳本 - 用於本機清理測試資料

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="podcast"
DB_USER="bdse37"
DB_PASSWORD="111111"

# 函數：印出彩色訊息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 函數：檢查 PostgreSQL 連線
check_postgres_connection() {
    print_step "檢查 PostgreSQL 連線..."
    
    if command -v psql &> /dev/null; then
        if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" &> /dev/null; then
            print_info "PostgreSQL 連線正常"
            return 0
        else
            print_error "無法連線到 PostgreSQL"
            return 1
        fi
    else
        print_error "psql 命令未找到，請安裝 PostgreSQL 客戶端"
        return 1
    fi
}

# 函數：顯示資料庫統計
show_database_stats() {
    print_step "顯示資料庫統計..."
    
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME << EOF
\echo '=== 資料庫大小 ==='
SELECT pg_size_pretty(pg_database_size('$DB_NAME')) as database_size;

\echo '=== 表格列表 ==='
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size,
    (SELECT count(*) FROM information_schema.columns WHERE table_name = tablename) as column_count
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

\echo '=== 活躍連線數 ==='
SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active';
EOF
}

# 函數：清理測試資料
cleanup_test_data() {
    print_step "開始清理測試資料..."
    
    # 設定環境變數
    export POSTGRES_HOST=$DB_HOST
    export POSTGRES_PORT=$DB_PORT
    export POSTGRES_DB=$DB_NAME
    export POSTGRES_USER=$DB_USER
    export POSTGRES_PASSWORD=$DB_PASSWORD
    
    # 執行 Python 清理腳本
    cd "$(dirname "$0")"
    
    if [ "$1" = "--dry-run" ]; then
        print_warning "試運行模式 - 不會實際刪除資料"
        python local_cleanup.py --dry-run --verbose
    else
        print_warning "即將執行實際清理操作！"
        read -p "確定要繼續嗎？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python local_cleanup.py --verbose
        else
            print_info "操作已取消"
            exit 0
        fi
    fi
}

# 函數：顯示使用說明
show_usage() {
    echo "使用方法: $0 [選項]"
    echo ""
    echo "選項:"
    echo "  -h, --help          顯示此說明"
    echo "  --dry-run           試運行模式，不實際刪除資料"
    echo "  --check             僅檢查資料庫連線和統計"
    echo "  --cleanup           執行清理操作"
    echo ""
    echo "範例:"
    echo "  $0 --check           # 檢查資料庫狀態"
    echo "  $0 --dry-run         # 試運行清理"
    echo "  $0 --cleanup         # 執行實際清理"
    echo ""
    echo "配置:"
    echo "  主機: $DB_HOST"
    echo "  埠號: $DB_PORT"
    echo "  資料庫: $DB_NAME"
    echo "  使用者: $DB_USER"
}

# 主程式
main() {
    case "${1:-}" in
        -h|--help)
            show_usage
            exit 0
            ;;
        --check)
            check_postgres_connection
            show_database_stats
            ;;
        --dry-run)
            check_postgres_connection
            cleanup_test_data --dry-run
            ;;
        --cleanup)
            check_postgres_connection
            cleanup_test_data
            ;;
        "")
            print_info "未指定選項，顯示使用說明"
            show_usage
            ;;
        *)
            print_error "未知選項: $1"
            show_usage
            exit 1
            ;;
    esac
}

# 執行主程式
main "$@" 