"""清理服務模組，負責整合所有清理功能。"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

# 添加父目錄到路徑以支援絕對導入
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from data_cleaning.utils.data_extractor import DataExtractor
    from data_cleaning.utils.db_utils import DBUtils
    from data_cleaning.services.cleaner_orchestrator import CleanerOrchestrator
    from data_cleaning.config.config import Config
except ImportError:
    # Fallback: 相對導入
    from utils.data_extractor import DataExtractor
    from utils.db_utils import DBUtils
    from services.cleaner_orchestrator import CleanerOrchestrator
    from config.config import Config

logger = logging.getLogger(__name__)


class CleanupService:
    """清理服務主類別，負責整合所有清理功能。"""
    
    def __init__(self, config: Config):
        """初始化清理服務。
        
        Args:
            config: 設定物件
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化各個模組
        self.data_extractor = DataExtractor(config)
        self.cleaner_orchestrator = CleanerOrchestrator(output_dir=config.get_test_output_path())
        self.db_utils = DBUtils(config.get_db_config())
        
    def run_local_test(self, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """執行本地測試，不涉及資料庫操作。"""
        try:
            self.logger.info("開始執行本地測試...")
        
            # 1. 提取測試資料
            self.logger.info("步驟1: 提取測試資料")
            episodes = self.data_extractor.extract_episodes_from_sql(sample_size)
            if not episodes:
                return {"success": False, "error": "無法提取測試資料"}
            
            # 2. 處理資料
            self.logger.info("步驟2: 處理資料")
            # 使用 episode_cleaner 進行批次清理
            from data_cleaning.core.episode_cleaner import EpisodeCleaner
            episode_cleaner = EpisodeCleaner()
            processed_episodes = episode_cleaner.batch_clean(episodes)
            
            # 3. 儲存處理結果
            self.logger.info("步驟3: 儲存處理結果")
            json_path = self.data_extractor.save_to_json(processed_episodes, "local_test_episodes.json")
            csv_path = self.data_extractor.save_to_csv(processed_episodes, "local_test_episodes.csv")
            
            # 4. 統計結果
            total_count = len(processed_episodes)
            success_count = len([ep for ep in processed_episodes if ep.get('cleaning_status') != 'error'])
            
            result = {
                "success": True,
                "total_episodes": total_count,
                "successful_cleans": success_count,
                "failed_cleans": total_count - success_count,
                "output_files": {
                    "json": json_path,
                    "csv": csv_path
                },
                "test_type": "local",
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"本地測試完成: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"本地測試失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def run_database_test(self, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """執行資料庫測試，包含資料庫操作。"""
        try:
            self.logger.info("開始執行資料庫測試...")
            
            # 1. 連接資料庫
            self.logger.info("步驟1: 連接資料庫")
            self.db_utils.connect()
            
            # 2. 提取測試資料
            self.logger.info("步驟2: 提取測試資料")
            episodes = self.data_extractor.extract_episodes_from_sql(sample_size)
            if not episodes:
                return {"success": False, "error": "無法提取測試資料"}
            
            # 3. 處理資料
            self.logger.info("步驟3: 處理資料")
            # 使用 episode_cleaner 進行批次清理
            from data_cleaning.core.episode_cleaner import EpisodeCleaner
            episode_cleaner = EpisodeCleaner()
            processed_episodes = episode_cleaner.batch_clean(episodes)
            
            # 4. 準備資料庫插入資料
            self.logger.info("步驟4: 準備資料庫插入資料")
            insert_data = []
            for episode in processed_episodes:
                if episode.get('cleaning_status') != 'error':
                    insert_data.append({
                        'podcast_id': episode.get('podcast_id'),
                        'episode_title': episode.get('episode_title'),
                        'published_date': episode.get('published_date'),
                        'audio_url': episode.get('audio_url'),
                        'duration': episode.get('duration'),
                        'description': episode.get('description'),
                        'audio_preview_url': episode.get('audio_preview_url'),
                        'languages': episode.get('languages'),
                        'explicit': episode.get('explicit'),
                        'apple_episodes_ranking': episode.get('apple_episodes_ranking')
                    })
            
            # 5. 插入資料庫
            self.logger.info("步驟5: 插入資料庫")
            success_count = 0
            for episode_data in insert_data:
                try:
                    if self.db_utils.insert_episode(episode_data):
                        success_count += 1
                except Exception as e:
                    self.logger.error(f"插入 episode 失敗: {e}")
            
            # 6. 關閉資料庫連接
            self.db_utils.disconnect()
            
            # 7. 統計結果
            total_count = len(processed_episodes)
            cleaned_count = len([ep for ep in processed_episodes if ep.get('cleaning_status') != 'error'])
            
            result = {
                "success": True,
                "total_episodes": total_count,
                "successful_cleans": cleaned_count,
                "successful_inserts": success_count,
                "failed_cleans": total_count - cleaned_count,
                "failed_inserts": cleaned_count - success_count,
                "test_type": "database",
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"資料庫測試完成: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"資料庫測試失敗: {e}")
            if hasattr(self, 'db_utils') and self.db_utils:
                self.db_utils.disconnect()
            return {"success": False, "error": str(e)}
    
    def run_full_cleanup_test(self, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """執行完整清理測試流程。
        
        Args:
            sample_size: 測試資料量
            
        Returns:
            完整測試結果字典
        """
        self.logger.info("開始執行完整清理測試流程")
        
        # 1. 本地測試
        local_result = self.run_local_test(sample_size)
        
        # 2. 資料庫測試
        db_result = self.run_database_test(sample_size)
        
        # 3. 整合結果
        full_result = {
            "timestamp": datetime.now().isoformat(),
            "local_test": local_result,
            "database_test": db_result,
            "overall_success": local_result.get("success", False) and db_result.get("success", False)
        }
        
        # 4. 儲存完整結果
        output_path = self.config.get_test_output_path()
        result_file = f"{output_path}/full_test_result.json"
        
        try:
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(full_result, f, ensure_ascii=False, indent=2, default=str)
            full_result["result_file"] = result_file
        except Exception as e:
            self.logger.error(f"儲存完整結果時發生錯誤: {e}")
        
        self.logger.info(f"完整清理測試完成: {full_result}")
        return full_result
    
    def validate_data_format(self, episodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證資料格式是否符合PostgreSQL要求。
        
        Args:
            episodes: episodes資料列表
            
        Returns:
            驗證結果字典
        """
        validation_result = {
            "total_episodes": len(episodes),
            "valid_episodes": 0,
            "invalid_episodes": 0,
            "errors": []
        }
        
        for i, episode in enumerate(episodes):
            episode_errors = []
            
            # 檢查必要欄位
            required_fields = ['episode_id', 'podcast_id', 'episode_title']
            for field in required_fields:
                if not episode.get(field):
                    episode_errors.append(f"缺少必要欄位: {field}")
            
            # 檢查資料類型
            if episode.get('duration') and not str(episode['duration']).isdigit():
                episode_errors.append("duration必須為數字")
            
            if episode.get('explicit') is not None and not isinstance(episode['explicit'], bool):
                episode_errors.append("explicit必須為布林值")
            
            # 檢查字串長度
            if episode.get('episode_title') and len(episode['episode_title']) > 255:
                episode_errors.append("episode_title超過255字元限制")
            
            if episode.get('audio_url') and len(episode['audio_url']) > 512:
                episode_errors.append("audio_url超過512字元限制")
            
            # 記錄錯誤
            if episode_errors:
                validation_result["invalid_episodes"] += 1
                validation_result["errors"].append({
                    "episode_index": i,
                    "episode_id": episode.get('episode_id'),
                    "errors": episode_errors
                })
            else:
                validation_result["valid_episodes"] += 1
        
        return validation_result
    
    def generate_test_report(self, test_result: Dict[str, Any]) -> str:
        """生成測試報告。
        
        Args:
            test_result: 測試結果字典
            
        Returns:
            報告內容
        """
        report = []
        report.append("# PostgreSQL Cleanup 測試報告")
        report.append(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 本地測試結果
        local_test = test_result.get("local_test", {})
        report.append("## 本地測試結果")
        report.append(f"- 總資料量: {local_test.get('total_episodes', 0)}")
        report.append(f"- 處理成功: {local_test.get('successful_cleans', 0)}")
        report.append(f"- 處理失敗: {local_test.get('failed_cleans', 0)}")
        report.append(f"- JSON輸出: {local_test.get('output_files', {}).get('json', 'N/A')}")
        report.append(f"- CSV輸出: {local_test.get('output_files', {}).get('csv', 'N/A')}")
        report.append("")
        
        # 資料庫測試結果
        db_test = test_result.get("database_test", {})
        report.append("## 資料庫測試結果")
        report.append(f"- 插入episodes: {db_test.get('successful_inserts', 0)}")
        report.append(f"- 插入metadata: {db_test.get('inserted_metadata', 0)}")
        report.append(f"- 最終episodes數: {db_test.get('final_episode_count', 0)}")
        report.append(f"- 最終metadata數: {db_test.get('final_metadata_count', 0)}")
        report.append("")
        
        # 表格結構資訊
        table_info = db_test.get("table_info", {})
        if table_info:
            report.append("## 表格結構資訊")
            for table_name, info in table_info.items():
                if info.get("exists"):
                    report.append(f"- {table_name}: {info.get('count', 0)} 筆記錄")
                else:
                    report.append(f"- {table_name}: 不存在")
            report.append("")
        
        # 整體結果
        report.append("## 整體結果")
        report.append(f"- 測試狀態: {'成功' if test_result.get('overall_success') else '失敗'}")
        report.append(f"- 結果檔案: {test_result.get('result_file', 'N/A')}")
        
        return "\n".join(report) 