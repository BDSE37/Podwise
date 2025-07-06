"""
PostgreSQL Meta Data Cleanup Main Script

主要的清理腳本，提供命令列介面來執行清理操作
"""

import argparse
import logging
import json
import sys
from datetime import datetime
from .cleanup_service import PostgresCleanupService
from .config import config


def setup_logging(verbose: bool = False) -> None:
    """設定日誌配置"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'postgresql_cleanup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )


def print_summary(results: dict) -> None:
    """印出清理結果摘要"""
    print("\n" + "="*60)
    print("PostgreSQL Meta Data 清理結果摘要")
    print("="*60)
    
    total_deleted = 0
    total_space_saved = 0
    
    for table_name, result in results.items():
        print(f"\n表格: {table_name}")
        print(f"  - 根據年齡刪除: {result['deleted_by_age']} 筆")
        print(f"  - 根據狀態刪除: {result['deleted_by_status']} 筆")
        print(f"  - 總刪除數量: {result['total_deleted']} 筆")
        print(f"  - 初始大小: {result['initial_size_mb']:.2f} MB")
        print(f"  - 最終大小: {result['final_size_mb']:.2f} MB")
        print(f"  - 節省空間: {result['space_saved_mb']:.2f} MB")
        
        total_deleted += result['total_deleted']
        total_space_saved += result['space_saved_mb']
    
    print(f"\n總計:")
    print(f"  - 總刪除記錄: {total_deleted} 筆")
    print(f"  - 總節省空間: {total_space_saved:.2f} MB")
    print("="*60)


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='PostgreSQL Meta Data 清理工具')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細輸出')
    parser.add_argument('--dry-run', action='store_true', help='試運行模式，不實際刪除資料')
    parser.add_argument('--table', type=str, help='指定要清理的表格名稱')
    parser.add_argument('--days', type=int, default=90, help='清理多少天前的資料 (預設: 90)')
    parser.add_argument('--status', type=str, help='要清理的狀態 (用逗號分隔)')
    parser.add_argument('--output', type=str, help='將結果輸出到 JSON 檔案')
    
    args = parser.parse_args()
    
    # 設定日誌
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # 驗證配置
    if not config.validate_config():
        logger.error("配置驗證失敗")
        sys.exit(1)
    
    # 更新配置
    if args.dry_run:
        config.cleanup_config['dry_run'] = True
    if args.days:
        config.cleanup_conditions['max_age_days'] = args.days
    if args.status:
        config.cleanup_conditions['status_filter'] = args.status
    
    logger.info("開始 PostgreSQL Meta Data 清理程序")
    logger.info(f"配置: {config.cleanup_config}")
    logger.info(f"清理條件: {config.cleanup_conditions}")
    
    # 建立清理服務
    cleanup_service = PostgresCleanupService()
    
    try:
        if args.table:
            # 清理單一表格
            logger.info(f"清理指定表格: {args.table}")
            if not cleanup_service.connect():
                sys.exit(1)
            
            # 檢查表格是否存在
            table_info = cleanup_service.get_table_info(args.table)
            if not table_info:
                logger.error(f"表格不存在: {args.table}")
                sys.exit(1)
            
            # 執行清理
            initial_size = cleanup_service.get_table_size(args.table)
            deleted_count = cleanup_service.cleanup_old_records(args.table, args.days)
            
            if args.status:
                status_list = args.status.split(',')
                status_deleted = cleanup_service.cleanup_by_status(args.table, status_list)
            else:
                status_deleted = 0
            
            cleanup_service.vacuum_table(args.table)
            final_size = cleanup_service.get_table_size(args.table)
            
            results = {
                args.table: {
                    'deleted_by_age': deleted_count,
                    'deleted_by_status': status_deleted,
                    'total_deleted': deleted_count + status_deleted,
                    'initial_size_mb': initial_size / (1024 * 1024) if initial_size else 0,
                    'final_size_mb': final_size / (1024 * 1024) if final_size else 0,
                    'space_saved_mb': (initial_size - final_size) / (1024 * 1024) if initial_size and final_size else 0
                }
            }
            
        else:
            # 清理所有表格
            logger.info("清理所有目標表格")
            results = cleanup_service.cleanup_all_tables()
        
        # 印出結果
        print_summary(results)
        
        # 輸出到檔案
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"結果已儲存到: {args.output}")
        
        logger.info("清理程序完成")
        
    except KeyboardInterrupt:
        logger.info("使用者中斷程序")
        sys.exit(1)
    except Exception as e:
        logger.error(f"清理程序發生錯誤: {e}")
        sys.exit(1)
    finally:
        cleanup_service.disconnect()


if __name__ == "__main__":
    main() 