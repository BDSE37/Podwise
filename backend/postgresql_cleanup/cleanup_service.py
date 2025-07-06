"""
PostgreSQL Meta Data Cleanup Service

提供清理 PostgreSQL 資料庫中 meta_data 的核心功能
支援 Kubernetes 環境部署
"""

import os
import logging
import psycopg2
import psycopg2.extras
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from config import config


class PostgresCleanupService:
    """PostgreSQL 清理服務類別"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connection = None
        self.cursor = None
        self.retry_count = 0
    
    def connect(self) -> bool:
        """建立資料庫連線 (支援 Kubernetes 環境)"""
        max_retries = config.cleanup_config['max_retries']
        
        while self.retry_count < max_retries:
            try:
                # 使用配置的連線參數
                connection_params = config.get_connection_params()
                
                self.logger.info(f"嘗試連線到 PostgreSQL: {connection_params['host']}:{connection_params['port']}")
                
                self.connection = psycopg2.connect(**connection_params)
                self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # 測試連線
                self.cursor.execute("SELECT version()")
                version = self.cursor.fetchone()
                self.logger.info(f"成功連線到 PostgreSQL: {version['version']}")
                
                return True
                
            except Exception as e:
                self.retry_count += 1
                self.logger.warning(f"資料庫連線失敗 (嘗試 {self.retry_count}/{max_retries}): {e}")
                
                if self.retry_count < max_retries:
                    # 等待後重試
                    wait_time = config.cleanup_config['k8s_retry_interval']
                    self.logger.info(f"等待 {wait_time} 秒後重試...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"資料庫連線失敗，已達最大重試次數: {e}")
                    return False
        
        return False
    
    def disconnect(self):
        """關閉資料庫連線"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        self.logger.info("資料庫連線已關閉")
    
    def check_connection(self) -> bool:
        """檢查資料庫連線狀態"""
        try:
            if self.connection and not self.connection.closed:
                self.cursor.execute("SELECT 1")
                return True
            return False
        except Exception:
            return False
    
    def reconnect_if_needed(self) -> bool:
        """如果需要則重新連線"""
        if not self.check_connection():
            self.logger.info("資料庫連線已斷開，嘗試重新連線...")
            self.disconnect()
            return self.connect()
        return True
    
    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """取得表格資訊"""
        if not self.reconnect_if_needed():
            return None
            
        try:
            query = """
                SELECT 
                    schemaname,
                    tablename,
                    tableowner,
                    tablespace,
                    hasindexes,
                    hasrules,
                    hastriggers,
                    rowsecurity
                FROM pg_tables 
                WHERE tablename = %s
            """
            self.cursor.execute(query, (table_name,))
            result = self.cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            self.logger.error(f"取得表格資訊失敗 {table_name}: {e}")
            return None
    
    def get_table_size(self, table_name: str) -> Optional[int]:
        """取得表格大小 (bytes)"""
        if not self.reconnect_if_needed():
            return None
            
        try:
            query = """
                SELECT pg_total_relation_size(%s) as size
            """
            self.cursor.execute(query, (table_name,))
            result = self.cursor.fetchone()
            return result['size'] if result else None
        except Exception as e:
            self.logger.error(f"取得表格大小失敗 {table_name}: {e}")
            return None
    
    def get_old_records_count(self, table_name: str, days: int) -> int:
        """取得指定天數前的記錄數量"""
        if not self.reconnect_if_needed():
            return 0
            
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            query = f"""
                SELECT COUNT(*) as count
                FROM {table_name}
                WHERE created_at < %s OR updated_at < %s
            """
            self.cursor.execute(query, (cutoff_date, cutoff_date))
            result = self.cursor.fetchone()
            return result['count'] if result else 0
        except Exception as e:
            self.logger.error(f"計算舊記錄數量失敗 {table_name}: {e}")
            return 0
    
    def cleanup_old_records(self, table_name: str, days: int, batch_size: int = None) -> int:
        """清理指定天數前的記錄"""
        if batch_size is None:
            batch_size = config.cleanup_config['batch_size']
        
        if not self.reconnect_if_needed():
            return 0
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = 0
            
            while True:
                # 分批刪除舊記錄
                query = f"""
                    DELETE FROM {table_name}
                    WHERE id IN (
                        SELECT id FROM {table_name}
                        WHERE created_at < %s OR updated_at < %s
                        LIMIT %s
                    )
                """
                self.cursor.execute(query, (cutoff_date, cutoff_date, batch_size))
                deleted = self.cursor.rowcount
                deleted_count += deleted
                
                self.connection.commit()
                self.logger.info(f"已刪除 {table_name} 中的 {deleted} 筆記錄")
                
                if deleted < batch_size:
                    break
            
            self.logger.info(f"完成清理 {table_name}，總共刪除 {deleted_count} 筆記錄")
            return deleted_count
            
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"清理記錄失敗 {table_name}: {e}")
            return 0
    
    def cleanup_by_status(self, table_name: str, status_list: List[str], batch_size: int = None) -> int:
        """根據狀態清理記錄"""
        if batch_size is None:
            batch_size = config.cleanup_config['batch_size']
        
        if not self.reconnect_if_needed():
            return 0
        
        try:
            deleted_count = 0
            status_placeholders = ','.join(['%s'] * len(status_list))
            
            while True:
                query = f"""
                    DELETE FROM {table_name}
                    WHERE id IN (
                        SELECT id FROM {table_name}
                        WHERE status IN ({status_placeholders})
                        LIMIT %s
                    )
                """
                params = status_list + [batch_size]
                self.cursor.execute(query, params)
                deleted = self.cursor.rowcount
                deleted_count += deleted
                
                self.connection.commit()
                self.logger.info(f"已刪除 {table_name} 中狀態為 {status_list} 的 {deleted} 筆記錄")
                
                if deleted < batch_size:
                    break
            
            self.logger.info(f"完成根據狀態清理 {table_name}，總共刪除 {deleted_count} 筆記錄")
            return deleted_count
            
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"根據狀態清理記錄失敗 {table_name}: {e}")
            return 0
    
    def cleanup_test_data(self, table_name: str, batch_size: int = None) -> int:
        """清理測試資料 (更激進的清理策略)"""
        if batch_size is None:
            batch_size = config.cleanup_config['batch_size']
        
        if not self.reconnect_if_needed():
            return 0
        
        try:
            deleted_count = 0
            
            # 清理包含測試關鍵字的記錄
            test_keywords = ['test', 'testing', 'demo', 'sample', 'temp', 'temporary', 'draft']
            
            for keyword in test_keywords:
                while True:
                    query = f"""
                        DELETE FROM {table_name}
                        WHERE id IN (
                            SELECT id FROM {table_name}
                            WHERE (
                                title ILIKE %s OR 
                                description ILIKE %s OR 
                                content ILIKE %s OR
                                status ILIKE %s OR
                                name ILIKE %s
                            )
                            LIMIT %s
                        )
                    """
                    pattern = f'%{keyword}%'
                    self.cursor.execute(query, (pattern, pattern, pattern, pattern, pattern, batch_size))
                    deleted = self.cursor.rowcount
                    deleted_count += deleted
                    
                    self.connection.commit()
                    if deleted > 0:
                        self.logger.info(f"已刪除 {table_name} 中包含 '{keyword}' 的 {deleted} 筆記錄")
                    
                    if deleted < batch_size:
                        break
            
            self.logger.info(f"完成清理 {table_name} 測試資料，總共刪除 {deleted_count} 筆記錄")
            return deleted_count
            
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"清理測試資料失敗 {table_name}: {e}")
            return 0
    
    def cleanup_all_test_data(self, table_name: str, batch_size: int = None) -> int:
        """清理所有測試資料 (最激進的清理策略)"""
        if batch_size is None:
            batch_size = config.cleanup_config['batch_size']
        
        if not self.reconnect_if_needed():
            return 0
        
        try:
            deleted_count = 0
            
            # 清理所有測試相關的記錄
            test_conditions = [
                "title ILIKE '%test%'",
                "title ILIKE '%demo%'", 
                "title ILIKE '%sample%'",
                "title ILIKE '%temp%'",
                "title ILIKE '%draft%'",
                "description ILIKE '%test%'",
                "description ILIKE '%demo%'",
                "description ILIKE '%sample%'",
                "content ILIKE '%test%'",
                "content ILIKE '%demo%'",
                "content ILIKE '%sample%'",
                "status IN ('test', 'testing', 'demo', 'sample', 'temp', 'temporary', 'draft')",
                "created_at < NOW() - INTERVAL '1 day'",  # 清理 1 天前的資料
            ]
            
            for condition in test_conditions:
                while True:
                    query = f"""
                        DELETE FROM {table_name}
                        WHERE id IN (
                            SELECT id FROM {table_name}
                            WHERE {condition}
                            LIMIT %s
                        )
                    """
                    self.cursor.execute(query, (batch_size,))
                    deleted = self.cursor.rowcount
                    deleted_count += deleted
                    
                    self.connection.commit()
                    if deleted > 0:
                        self.logger.info(f"已刪除 {table_name} 中符合條件 '{condition}' 的 {deleted} 筆記錄")
                    
                    if deleted < batch_size:
                        break
            
            self.logger.info(f"完成清理 {table_name} 所有測試資料，總共刪除 {deleted_count} 筆記錄")
            return deleted_count
            
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"清理所有測試資料失敗 {table_name}: {e}")
            return 0
    
    def vacuum_table(self, table_name: str) -> bool:
        """對表格執行 VACUUM 操作"""
        if not self.reconnect_if_needed():
            return False
            
        try:
            query = f"VACUUM ANALYZE {table_name}"
            self.cursor.execute(query)
            self.logger.info(f"完成 VACUUM {table_name}")
            return True
        except Exception as e:
            self.logger.error(f"VACUUM 失敗 {table_name}: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """取得資料庫統計資訊"""
        if not self.reconnect_if_needed():
            return {}
            
        try:
            stats = {}
            
            # 資料庫大小
            self.cursor.execute("SELECT pg_database_size(current_database()) as db_size")
            result = self.cursor.fetchone()
            stats['database_size_mb'] = result['db_size'] / (1024 * 1024) if result else 0
            
            # 活躍連線數
            self.cursor.execute("SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active'")
            result = self.cursor.fetchone()
            stats['active_connections'] = result['active_connections'] if result else 0
            
            # 表格數量
            self.cursor.execute("SELECT count(*) as table_count FROM pg_tables WHERE schemaname = 'public'")
            result = self.cursor.fetchone()
            stats['table_count'] = result['table_count'] if result else 0
            
            return stats
        except Exception as e:
            self.logger.error(f"取得資料庫統計資訊失敗: {e}")
            return {}
    
    def cleanup_all_tables(self) -> Dict[str, Any]:
        """清理所有目標表格"""
        results = {}
        
        if not self.connect():
            return results
        
        try:
            # 取得清理前的資料庫統計
            initial_stats = self.get_database_stats()
            self.logger.info(f"清理前資料庫統計: {initial_stats}")
            
            for table_name in config.target_tables:
                self.logger.info(f"開始清理表格: {table_name}")
                
                # 檢查表格是否存在
                table_info = self.get_table_info(table_name)
                if not table_info:
                    self.logger.warning(f"表格不存在: {table_name}")
                    continue
                
                # 取得清理前的表格大小
                initial_size = self.get_table_size(table_name)
                
                # 清理舊記錄
                deleted_count = self.cleanup_old_records(
                    table_name, 
                    config.cleanup_conditions['max_age_days']
                )
                
                # 根據狀態清理
                status_list = config.cleanup_conditions['status_filter'].split(',')
                status_deleted = self.cleanup_by_status(table_name, status_list)
                
                # 執行 VACUUM
                self.vacuum_table(table_name)
                
                # 取得清理後的表格大小
                final_size = self.get_table_size(table_name)
                
                results[table_name] = {
                    'deleted_by_age': deleted_count,
                    'deleted_by_status': status_deleted,
                    'total_deleted': deleted_count + status_deleted,
                    'initial_size_mb': initial_size / (1024 * 1024) if initial_size else 0,
                    'final_size_mb': final_size / (1024 * 1024) if final_size else 0,
                    'space_saved_mb': (initial_size - final_size) / (1024 * 1024) if initial_size and final_size else 0
                }
            
            # 取得清理後的資料庫統計
            final_stats = self.get_database_stats()
            self.logger.info(f"清理後資料庫統計: {final_stats}")
            
            # 添加整體統計
            results['_database_stats'] = {
                'initial': initial_stats,
                'final': final_stats,
                'total_space_saved_mb': sum(r['space_saved_mb'] for r in results.values() if isinstance(r, dict) and 'space_saved_mb' in r)
            }
                
        finally:
            self.disconnect()
        
        return results 