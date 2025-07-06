"""
PostgreSQL Cleanup Configuration

此檔案包含清理 PostgreSQL meta_data 所需的配置設定
支援 Kubernetes 環境部署
"""

import os
from typing import Dict, Any


class PostgresCleanupConfig:
    """PostgreSQL 清理配置類別"""
    
    def __init__(self):
        # 資料庫連線配置
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', '192.168.32.xx'),  # 使用實際 IP 地址
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'database': os.getenv('POSTGRES_DB', 'podcast'),
            'user': os.getenv('POSTGRES_USER', 'bdse37'),
            'password': os.getenv('POSTGRES_PASSWORD', '111111'),
            'namespace': os.getenv('K8S_NAMESPACE', 'podwise'),
            'service_name': os.getenv('POSTGRES_SERVICE_NAME', 'postgres'),
            'pod_name': os.getenv('POSTGRES_POD_NAME', ''),
            'sslmode': os.getenv('POSTGRES_SSLMODE', 'prefer'),
            'ssl_cert': os.getenv('POSTGRES_SSL_CERT', ''),
            'ssl_key': os.getenv('POSTGRES_SSL_KEY', ''),
            'ssl_ca': os.getenv('POSTGRES_SSL_CA', '')
        }
        
        # 清理配置
        self.cleanup_config = {
            'batch_size': int(os.getenv('CLEANUP_BATCH_SIZE', '1000')),
            'max_retries': int(os.getenv('CLEANUP_MAX_RETRIES', '3')),
            'timeout_seconds': int(os.getenv('CLEANUP_TIMEOUT', '300')),
            'dry_run': os.getenv('CLEANUP_DRY_RUN', 'false').lower() == 'true',
            'k8s_job_timeout': int(os.getenv('K8S_JOB_TIMEOUT', '3600')),
            'k8s_retry_interval': int(os.getenv('K8S_RETRY_INTERVAL', '30'))
        }
        
        # 目標表格
        self.target_tables = [
            'podcast_metadata',
            'episodes',  # 使用現有的 episodes 表格
            'transcript_metadata',
            'embedding_metadata',
            'processing_metadata'
        ]
        
        # 清理條件
        self.cleanup_conditions = {
            'max_age_days': int(os.getenv('CLEANUP_MAX_AGE_DAYS', '90')),
            'status_filter': os.getenv('CLEANUP_STATUS_FILTER', 'completed,failed'),
            'size_limit_mb': int(os.getenv('CLEANUP_SIZE_LIMIT_MB', '1000'))
        }
        
        # Kubernetes 配置
        self.k8s_config = {
            'context': os.getenv('K8S_CONTEXT', ''),
            'namespace': os.getenv('K8S_NAMESPACE', 'podwise'),
            'service_account': os.getenv('K8S_SERVICE_ACCOUNT', 'default'),
            'image': os.getenv('CLEANUP_IMAGE', 'postgresql-cleanup:latest'),
            'resources': {
                'requests': {
                    'memory': os.getenv('CLEANUP_MEMORY_REQUEST', '256Mi'),
                    'cpu': os.getenv('CLEANUP_CPU_REQUEST', '100m')
                },
                'limits': {
                    'memory': os.getenv('CLEANUP_MEMORY_LIMIT', '512Mi'),
                    'cpu': os.getenv('CLEANUP_CPU_LIMIT', '500m')
                }
            }
        }
    
    def get_database_url(self) -> str:
        """取得資料庫連線字串"""
        return f"postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
    
    def get_connection_params(self) -> Dict[str, Any]:
        """取得資料庫連線參數"""
        return {
            'host': self.db_config['host'],
            'port': self.db_config['port'],
            'database': self.db_config['database'],
            'user': self.db_config['user'],
            'password': self.db_config['password'],
            'sslmode': self.db_config['sslmode']
        }


# 全域配置實例
config = PostgresCleanupConfig() 