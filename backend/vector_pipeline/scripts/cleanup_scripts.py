"""
清理腳本
用於清理重複和過時的檔案
符合 Google Clean Code 原則
"""

import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class CleanupScripts:
    """清理腳本類別"""
    
    def __init__(self, backup_dir: str = "backup_before_cleanup"):
        """
        初始化清理腳本
        
        Args:
            backup_dir: 備份目錄
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
    def backup_file(self, file_path: Path) -> bool:
        """
        備份檔案
        
        Args:
            file_path: 檔案路徑
            
        Returns:
            備份是否成功
        """
        try:
            if file_path.exists():
                backup_path = self.backup_dir / file_path.name
                shutil.copy2(file_path, backup_path)
                logger.info(f"已備份: {file_path} -> {backup_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"備份失敗 {file_path}: {e}")
            return False
    
    def cleanup_duplicate_tagging_files(self) -> Dict[str, Any]:
        """
        清理重複的標籤處理檔案
        
        Returns:
            清理結果
        """
        logger.info("開始清理重複的標籤處理檔案")
        
        duplicate_files = [
            "batch_enhanced_tagging.py",
            "batch_enhanced_tagging_v2.py", 
            "batch_retagging.py",
            "reprocess_rss_chunks.py"
        ]
        
        results = {
            "backed_up": [],
            "removed": [],
            "failed": []
        }
        
        for filename in duplicate_files:
            file_path = Path(filename)
            if file_path.exists():
                # 備份檔案
                if self.backup_file(file_path):
                    results["backed_up"].append(filename)
                    
                    # 移除檔案
                    try:
                        file_path.unlink()
                        results["removed"].append(filename)
                        logger.info(f"已移除: {filename}")
                    except Exception as e:
                        logger.error(f"移除失敗 {filename}: {e}")
                        results["failed"].append(filename)
        
        logger.info(f"標籤處理檔案清理完成: 備份 {len(results['backed_up'])} 個，移除 {len(results['removed'])} 個")
        return results
    
    def cleanup_duplicate_milvus_files(self) -> Dict[str, Any]:
        """
        清理重複的 Milvus 測試檔案
        
        Returns:
            清理結果
        """
        logger.info("開始清理重複的 Milvus 測試檔案")
        
        duplicate_files = [
            "test_milvus_connection.py",
            "test_single_insert.py",
            "test_simple_insert.py",
            "check_milvus_schema.py",
            "check_milvus_version.py",
            "reset_milvus_collection.py",
            "debug_insert_types.py",
            "debug_insert_data.py",
            "debug_data_types.py",
            "debug_id_formats.py",
            "debug_full_flow.py",
            "debug_chunk_id.py",
            "debug_real_embedding.py",
            "debug_embedding_process.py",
            "debug_embedding_errors.py"
        ]
        
        results = {
            "backed_up": [],
            "removed": [],
            "failed": []
        }
        
        for filename in duplicate_files:
            file_path = Path(filename)
            if file_path.exists():
                # 備份檔案
                if self.backup_file(file_path):
                    results["backed_up"].append(filename)
                    
                    # 移除檔案
                    try:
                        file_path.unlink()
                        results["removed"].append(filename)
                        logger.info(f"已移除: {filename}")
                    except Exception as e:
                        logger.error(f"移除失敗 {filename}: {e}")
                        results["failed"].append(filename)
        
        logger.info(f"Milvus 測試檔案清理完成: 備份 {len(results['backed_up'])} 個，移除 {len(results['removed'])} 個")
        return results
    
    def cleanup_duplicate_embedding_files(self) -> Dict[str, Any]:
        """
        清理重複的嵌入檔案
        
        Returns:
            清理結果
        """
        logger.info("開始清理重複的嵌入檔案")
        
        duplicate_files = [
            "embed_stage3_to_milvus.py",
            "embed_stage3_to_milvus_with_real_embeddings.py",
            "test_embedding_flow.py"
        ]
        
        results = {
            "backed_up": [],
            "removed": [],
            "failed": []
        }
        
        for filename in duplicate_files:
            file_path = Path(filename)
            if file_path.exists():
                # 備份檔案
                if self.backup_file(file_path):
                    results["backed_up"].append(filename)
                    
                    # 移除檔案
                    try:
                        file_path.unlink()
                        results["removed"].append(filename)
                        logger.info(f"已移除: {filename}")
                    except Exception as e:
                        logger.error(f"移除失敗 {filename}: {e}")
                        results["failed"].append(filename)
        
        logger.info(f"嵌入檔案清理完成: 備份 {len(results['backed_up'])} 個，移除 {len(results['removed'])} 個")
        return results
    
    def cleanup_duplicate_search_files(self) -> Dict[str, Any]:
        """
        清理重複的搜尋測試檔案
        
        Returns:
            清理結果
        """
        logger.info("開始清理重複的搜尋測試檔案")
        
        duplicate_files = [
            "test_semantic_search.py",
            "simple_semantic_search.py",
            "investigate_real_failures.py",
            "find_failed_files.py",
            "check_failed_files.py",
            "analyze_failed_files.py",
            "simulate_embedding_failures.py"
        ]
        
        results = {
            "backed_up": [],
            "removed": [],
            "failed": []
        }
        
        for filename in duplicate_files:
            file_path = Path(filename)
            if file_path.exists():
                # 備份檔案
                if self.backup_file(file_path):
                    results["backed_up"].append(filename)
                    
                    # 移除檔案
                    try:
                        file_path.unlink()
                        results["removed"].append(filename)
                        logger.info(f"已移除: {filename}")
                    except Exception as e:
                        logger.error(f"移除失敗 {filename}: {e}")
                        results["failed"].append(filename)
        
        logger.info(f"搜尋測試檔案清理完成: 備份 {len(results['backed_up'])} 個，移除 {len(results['removed'])} 個")
        return results
    
    def cleanup_other_duplicate_files(self) -> Dict[str, Any]:
        """
        清理其他重複檔案
        
        Returns:
            清理結果
        """
        logger.info("開始清理其他重複檔案")
        
        duplicate_files = [
            "standardize_stage3_data.py",
            "supplement_postgresql_fields.py",
            "rename_json_files.py",
            "cleanup_filenames.py",
            "run_vectorization.py",
            "run_all.sh",
            "start_milvus.sh"
        ]
        
        results = {
            "backed_up": [],
            "removed": [],
            "failed": []
        }
        
        for filename in duplicate_files:
            file_path = Path(filename)
            if file_path.exists():
                # 備份檔案
                if self.backup_file(file_path):
                    results["backed_up"].append(filename)
                    
                    # 移除檔案
                    try:
                        file_path.unlink()
                        results["removed"].append(filename)
                        logger.info(f"已移除: {filename}")
                    except Exception as e:
                        logger.error(f"移除失敗 {filename}: {e}")
                        results["failed"].append(filename)
        
        logger.info(f"其他檔案清理完成: 備份 {len(results['backed_up'])} 個，移除 {len(results['removed'])} 個")
        return results
    
    def run_full_cleanup(self) -> Dict[str, Any]:
        """
        執行完整清理
        
        Returns:
            完整清理結果
        """
        logger.info("🚀 開始執行完整清理")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "backup_dir": str(self.backup_dir),
            "categories": {}
        }
        
        try:
            # 清理各類別檔案
            results["categories"]["tagging"] = self.cleanup_duplicate_tagging_files()
            results["categories"]["milvus"] = self.cleanup_duplicate_milvus_files()
            results["categories"]["embedding"] = self.cleanup_duplicate_embedding_files()
            results["categories"]["search"] = self.cleanup_duplicate_search_files()
            results["categories"]["other"] = self.cleanup_other_duplicate_files()
            
            # 統計總結果
            total_backed_up = sum(len(cat["backed_up"]) for cat in results["categories"].values())
            total_removed = sum(len(cat["removed"]) for cat in results["categories"].values())
            total_failed = sum(len(cat["failed"]) for cat in results["categories"].values())
            
            results["summary"] = {
                "total_backed_up": total_backed_up,
                "total_removed": total_removed,
                "total_failed": total_failed
            }
            
            logger.info("🎉 完整清理執行完成")
            logger.info(f"總計: 備份 {total_backed_up} 個檔案，移除 {total_removed} 個檔案")
            
        except Exception as e:
            logger.error(f"清理執行失敗: {e}")
            results["error"] = str(e)
        
        return results 