"""設定管理模組，負責管理所有配置參數。"""

import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """資料庫連線設定。"""
    host: str = "postgres.podwise.svc.cluster.local"
    port: int = 5432
    database: str = "podcast"
    username: str = "bdse37"
    password: str = "111111"
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式。"""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "password": self.password
        }


@dataclass
class TestDataConfig:
    """測試資料設定。"""
    backup_file: str = "episodes_backup_20250706_163501.sql"
    test_output_dir: str = "../../data/cleaned_data"
    sample_size: int = 100  # 測試用的資料量


class Config:
    """全域設定管理類別。"""
    
    def __init__(self, config_path: str = ""):
        """初始化設定。
        
        Args:
            config_path: 設定檔案路徑，如果為 None 則使用預設值
        """
        self.db_config = DatabaseConfig()
        self.test_config = TestDataConfig()
        self._load_environment_variables()
        
    def _load_environment_variables(self):
        """從環境變數載入設定。"""
        # 資料庫設定
        db_host = os.getenv("DB_HOST")
        if db_host:
            self.db_config.host = db_host
        db_port = os.getenv("DB_PORT")
        if db_port:
            self.db_config.port = int(db_port)
        db_name = os.getenv("DB_NAME")
        if db_name:
            self.db_config.database = db_name
        db_user = os.getenv("DB_USER")
        if db_user:
            self.db_config.username = db_user
        db_password = os.getenv("DB_PASSWORD")
        if db_password:
            self.db_config.password = db_password
            
        # 測試資料設定
        test_sample_size = os.getenv("TEST_SAMPLE_SIZE")
        if test_sample_size:
            self.test_config.sample_size = int(test_sample_size)
        test_output_dir = os.getenv("TEST_OUTPUT_DIR")
        if test_output_dir:
            self.test_config.test_output_dir = test_output_dir
    
    def get_db_config(self) -> Dict[str, Any]:
        """取得資料庫設定。
        
        Returns:
            資料庫設定字典
        """
        return self.db_config.to_dict()
    
    def get_test_config(self) -> TestDataConfig:
        """取得測試設定。
        
        Returns:
            測試設定物件
        """
        return self.test_config
    
    def get_backup_file_path(self) -> str:
        """取得備份檔案完整路徑。
        
        Returns:
            備份檔案路徑
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, self.test_config.backup_file)
    
    def get_test_output_path(self) -> str:
        """取得測試輸出目錄路徑。
        
        Returns:
            測試輸出目錄路徑
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(current_dir, self.test_config.test_output_dir)
        os.makedirs(output_path, exist_ok=True)
        return output_path 