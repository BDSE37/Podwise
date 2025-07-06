"""
本機 PostgreSQL 測試資料清理腳本

專門用於清理本機 PostgreSQL 資料庫中的測試資料
"""

import argparse
import logging
import json
import sys
import os
from datetime import datetime
from cleanup_service import PostgresCleanupService
from config import config


def setup_logging(verbose: bool = False) -> None:
    """設定日誌配置"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'local_cleanup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )


def print_summary(results: dict) -> None:
    """印出清理結果摘要"""
    print("\n" + "="*60)
    print("本機 PostgreSQL 測試資料清理結果摘要")
    print("="*60)
    
    total_deleted = 0
    total_space_saved = 0
    
    for table_name, result in results.items():
        if table_name.startswith('_'):
            continue  # 跳過內部統計資料
            
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


def cleanup_test_data(cleanup_service: PostgresCleanupService, table_name: str = None) -> dict:
    """清理測試資料"""
    results = {}
    
    if not cleanup_service.connect():
        return results
    
    try:
        # 取得清理前的資料庫統計
        initial_stats = cleanup_service.get_database_stats()
        print(f"清理前資料庫統計: {initial_stats}")
        
        if table_name:
            # 清理單一表格
            print(f"開始清理表格: {table_name}")
            
            # 檢查表格是否存在
            table_info = cleanup_service.get_table_info(table_name)
            if not table_info:
                print(f"表格不存在: {table_name}")
                return results
            
            # 取得清理前的表格大小
            initial_size = cleanup_service.get_table_size(table_name)
            
            # 清理測試資料 (更激進的清理策略)
            deleted_count = cleanup_service.cleanup_old_records(table_name, 1)  # 清理 1 天前的資料
            
            # 清理所有測試狀態的資料
            test_statuses = ['test', 'testing', 'draft', 'temp', 'temporary', 'demo', 'sample']
            status_deleted = cleanup_service.cleanup_by_status(table_name, test_statuses)
            
            # 執行 VACUUM
            cleanup_service.vacuum_table(table_name)
            
            # 取得清理後的表格大小
            final_size = cleanup_service.get_table_size(table_name)
            
            results[table_name] = {
                'deleted_by_age': deleted_count,
                'deleted_by_status': status_deleted,
                'total_deleted': deleted_count + status_deleted,
                'initial_size_mb': initial_size / (1024 * 1024) if initial_size else 0,
                'final_size_mb': final_size / (1024 * 1024) if final_size else 0,
                'space_saved_mb': (initial_size - final_size) / (1024 * 1024) if initial_size and final_size else 0
            }
            
        else:
            # 清理所有目標表格
            for table_name in config.target_tables:
                print(f"開始清理表格: {table_name}")
                
                # 檢查表格是否存在
                table_info = cleanup_service.get_table_info(table_name)
                if not table_info:
                    print(f"表格不存在: {table_name}")
                    continue
                
                # 取得清理前的表格大小
                initial_size = cleanup_service.get_table_size(table_name)
                
                # 清理測試資料 (更激進的清理策略)
                deleted_count = cleanup_service.cleanup_old_records(table_name, 1)  # 清理 1 天前的資料
                
                # 清理所有測試狀態的資料
                test_statuses = ['test', 'testing', 'draft', 'temp', 'temporary', 'demo', 'sample']
                status_deleted = cleanup_service.cleanup_by_status(table_name, test_statuses)
                
                # 執行 VACUUM
                cleanup_service.vacuum_table(table_name)
                
                # 取得清理後的表格大小
                final_size = cleanup_service.get_table_size(table_name)
                
                results[table_name] = {
                    'deleted_by_age': deleted_count,
                    'deleted_by_status': status_deleted,
                    'total_deleted': deleted_count + status_deleted,
                    'initial_size_mb': initial_size / (1024 * 1024) if initial_size else 0,
                    'final_size_mb': final_size / (1024 * 1024) if final_size else 0,
                    'space_saved_mb': (initial_size - final_size) / (1024 * 1024) if initial_size and final_size else 0
                }
        
        # 取得清理後的資料庫統計
        final_stats = cleanup_service.get_database_stats()
        print(f"清理後資料庫統計: {final_stats}")
        
        # 添加整體統計
        results['_database_stats'] = {
            'initial': initial_stats,
            'final': final_stats,
            'total_space_saved_mb': sum(r['space_saved_mb'] for r in results.values() if isinstance(r, dict) and 'space_saved_mb' in r)
        }
                
    finally:
        cleanup_service.disconnect()
    
    return results


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='本機 PostgreSQL 測試資料清理工具')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細輸出')
    parser.add_argument('--dry-run', action='store_true', help='試運行模式，不實際刪除資料')
    parser.add_argument('--table', type=str, help='指定要清理的表格名稱')
    parser.add_argument('--output', type=str, help='將結果輸出到 JSON 檔案')
    parser.add_argument('--host', type=str, default='localhost', help='PostgreSQL 主機 (預設: localhost)')
    parser.add_argument('--port', type=int, default=5432, help='PostgreSQL 埠號 (預設: 5432)')
    
    args = parser.parse_args()
    
    # 設定日誌
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # 更新配置為本機環境
    config.db_config['host'] = args.host
    config.db_config['port'] = args.port
    config.db_config['database'] = 'podcast'
    config.db_config['user'] = 'bdse37'
    config.db_config['password'] = '111111'
    
    # 驗證配置
    if not config.validate_config():
        logger.error("配置驗證失敗")
        sys.exit(1)
    
    # 更新配置
    if args.dry_run:
        config.cleanup_config['dry_run'] = True
    
    logger.info("開始本機 PostgreSQL 測試資料清理程序")
    logger.info(f"資料庫連線: {config.db_config['host']}:{config.db_config['port']}/{config.db_config['database']}")
    logger.info(f"使用者: {config.db_config['user']}")
    
    # 建立清理服務
    cleanup_service = PostgresCleanupService()
    
    try:
        # 執行清理
        results = cleanup_test_data(cleanup_service, args.table)
        
        # 印出結果
        print_summary(results)
        
        # 輸出到檔案
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"結果已儲存到: {args.output}")
        
        logger.info("本機清理程序完成")
        
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