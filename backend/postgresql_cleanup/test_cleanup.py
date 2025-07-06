"""
PostgreSQL Cleanup 測試檔案

提供清理功能的單元測試
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加模組路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import PostgresCleanupConfig
from cleanup_service import PostgresCleanupService


class TestPostgresCleanupConfig(unittest.TestCase):
    """測試配置類別"""
    
    def setUp(self):
        """測試前準備"""
        self.config = PostgresCleanupConfig()
    
    def test_default_config(self):
        """測試預設配置"""
        self.assertEqual(self.config.db_config['host'], 'localhost')
        self.assertEqual(self.config.db_config['port'], 5432)
        self.assertEqual(self.config.db_config['database'], 'podwise')
        self.assertEqual(self.config.cleanup_config['batch_size'], 1000)
        self.assertEqual(self.config.cleanup_conditions['max_age_days'], 90)
    
    def test_get_db_url(self):
        """測試資料庫 URL 生成"""
        url = self.config.get_db_url()
        self.assertIn('postgresql://', url)
        self.assertIn('localhost', url)
        self.assertIn('podwise', url)
    
    def test_validate_config(self):
        """測試配置驗證"""
        # 測試有效配置
        self.config.db_config['password'] = 'test_password'
        self.assertTrue(self.config.validate_config())
        
        # 測試無效配置
        self.config.db_config['password'] = ''
        self.assertFalse(self.config.validate_config())


class TestPostgresCleanupService(unittest.TestCase):
    """測試清理服務類別"""
    
    def setUp(self):
        """測試前準備"""
        self.service = PostgresCleanupService()
    
    @patch('psycopg2.connect')
    def test_connect_success(self, mock_connect):
        """測試成功連線"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        result = self.service.connect()
        
        self.assertTrue(result)
        self.assertEqual(self.service.connection, mock_connection)
        self.assertEqual(self.service.cursor, mock_cursor)
    
    @patch('psycopg2.connect')
    def test_connect_failure(self, mock_connect):
        """測試連線失敗"""
        mock_connect.side_effect = Exception("Connection failed")
        
        result = self.service.connect()
        
        self.assertFalse(result)
        self.assertIsNone(self.service.connection)
        self.assertIsNone(self.service.cursor)
    
    def test_disconnect(self):
        """測試斷開連線"""
        # 模擬連線狀態
        self.service.connection = Mock()
        self.service.cursor = Mock()
        
        self.service.disconnect()
        
        self.service.cursor.close.assert_called_once()
        self.service.connection.close.assert_called_once()
    
    def test_get_table_info(self):
        """測試取得表格資訊"""
        # 模擬資料庫連線
        self.service.cursor = Mock()
        mock_result = {
            'schemaname': 'public',
            'tablename': 'test_table',
            'tableowner': 'postgres'
        }
        self.service.cursor.fetchone.return_value = mock_result
        
        result = self.service.get_table_info('test_table')
        
        self.assertEqual(result, mock_result)
        self.service.cursor.execute.assert_called_once()
    
    def test_get_table_size(self):
        """測試取得表格大小"""
        # 模擬資料庫連線
        self.service.cursor = Mock()
        mock_result = {'size': 1024000}  # 1MB
        self.service.cursor.fetchone.return_value = mock_result
        
        result = self.service.get_table_size('test_table')
        
        self.assertEqual(result, 1024000)
        self.service.cursor.execute.assert_called_once()
    
    def test_get_old_records_count(self):
        """測試計算舊記錄數量"""
        # 模擬資料庫連線
        self.service.cursor = Mock()
        mock_result = {'count': 150}
        self.service.cursor.fetchone.return_value = mock_result
        
        result = self.service.get_old_records_count('test_table', 90)
        
        self.assertEqual(result, 150)
        self.service.cursor.execute.assert_called_once()


class TestCleanupOperations(unittest.TestCase):
    """測試清理操作"""
    
    def setUp(self):
        """測試前準備"""
        self.service = PostgresCleanupService()
        self.service.connection = Mock()
        self.service.cursor = Mock()
    
    def test_cleanup_old_records(self):
        """測試清理舊記錄"""
        # 模擬批次刪除
        self.service.cursor.rowcount = 100  # 第一次刪除 100 筆
        self.service.cursor.rowcount = 50   # 第二次刪除 50 筆
        self.service.cursor.rowcount = 0    # 第三次沒有更多記錄
        
        result = self.service.cleanup_old_records('test_table', 90, 100)
        
        self.assertEqual(result, 150)  # 100 + 50
        self.assertEqual(self.service.connection.commit.call_count, 2)
    
    def test_cleanup_by_status(self):
        """測試根據狀態清理"""
        # 模擬批次刪除
        self.service.cursor.rowcount = 75   # 第一次刪除 75 筆
        self.service.cursor.rowcount = 0    # 第二次沒有更多記錄
        
        result = self.service.cleanup_by_status('test_table', ['failed', 'expired'], 100)
        
        self.assertEqual(result, 75)
        self.assertEqual(self.service.connection.commit.call_count, 1)
    
    def test_vacuum_table(self):
        """測試 VACUUM 操作"""
        result = self.service.vacuum_table('test_table')
        
        self.assertTrue(result)
        self.service.cursor.execute.assert_called_once()
        self.assertIn('VACUUM ANALYZE', self.service.cursor.execute.call_args[0][0])


if __name__ == '__main__':
    # 設定測試環境
    unittest.main(verbosity=2) 