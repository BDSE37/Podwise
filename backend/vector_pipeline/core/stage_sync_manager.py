#!/usr/bin/env python3
"""
Stage 同步管理核心模組
處理 stage3 到 stage4 的檔案同步，修復錯誤檔案
"""

import os
import json
import shutil
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)

class StageSyncManager:
    """
    Stage 同步管理器
    處理 stage3 到 stage4 的檔案同步與錯誤修復
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        初始化 Stage 同步管理器
        
        Args:
            base_dir: 資料目錄路徑，預設為當前目錄的 data 資料夾
        """
        self.base_dir = base_dir or Path(__file__).parent.parent / "data"
        self.stage3_dir = self.base_dir / "stage3_tagging"
        self.stage4_dir = self.base_dir / "stage4_embedding_prep"
        
        # 統計資訊
        self.stats = {
            'stage3_files': 0,
            'stage4_files': 0,
            'missing_files': 0,
            'synced_files': 0,
            'failed_syncs': 0,
            'error_files': []
        }
    
    def scan_stage3_files(self) -> Dict[str, Path]:
        """
        掃描 stage3 目錄下的所有檔案
        
        Returns:
            檔案名到路徑的映射
        """
        stage3_files = {}
        
        for rss_dir in self.stage3_dir.iterdir():
            if rss_dir.is_dir() and rss_dir.name.startswith('RSS_'):
                for json_file in rss_dir.glob('*.json'):
                    if json_file.name.endswith('.json'):
                        stage3_files[json_file.name] = json_file
        
        self.stats['stage3_files'] = len(stage3_files)
        logger.info(f"掃描到 {len(stage3_files)} 個 stage3 檔案")
        return stage3_files
    
    def scan_stage4_files(self) -> Dict[str, Path]:
        """
        掃描 stage4 目錄下的所有檔案
        
        Returns:
            檔案名到路徑的映射（移除 _milvus 後綴）
        """
        stage4_files = {}
        
        for json_file in self.stage4_dir.glob('*_milvus.json'):
            # 移除 _milvus 後綴以匹配 stage3 檔案名
            base_filename = json_file.name.replace('_milvus.json', '.json')
            stage4_files[base_filename] = json_file
        
        self.stats['stage4_files'] = len(stage4_files)
        logger.info(f"掃描到 {len(stage4_files)} 個 stage4 檔案")
        return stage4_files
    
    def find_missing_files(self) -> List[str]:
        """
        找出 stage3 中有但 stage4 中缺少的檔案
        
        Returns:
            缺少的檔案名列表
        """
        stage3_files = self.scan_stage3_files()
        stage4_files = self.scan_stage4_files()
        
        missing_files = []
        for filename in stage3_files.keys():
            if filename not in stage4_files:
                missing_files.append(filename)
        
        self.stats['missing_files'] = len(missing_files)
        logger.info(f"發現 {len(missing_files)} 個缺少的檔案")
        return missing_files
    
    def sync_missing_files(self) -> bool:
        """
        同步缺少的檔案從 stage3 到 stage4
        
        Returns:
            是否成功同步
        """
        missing_files = self.find_missing_files()
        
        if not missing_files:
            logger.info("沒有缺少的檔案需要同步")
            return True
        
        stage3_files = self.scan_stage3_files()
        success_count = 0
        
        for filename in missing_files:
            try:
                stage3_path = stage3_files[filename]
                
                # 建立 stage4 檔案名（加上 _milvus 後綴）
                stage4_filename = filename.replace('.json', '_milvus.json')
                stage4_path = self.stage4_dir / stage4_filename
                
                # 複製檔案
                shutil.copy2(stage3_path, stage4_path)
                
                logger.info(f"同步檔案: {filename} -> {stage4_filename}")
                success_count += 1
                
            except Exception as e:
                logger.error(f"同步檔案失敗 {filename}: {e}")
                self.stats['error_files'].append({
                    'filename': filename,
                    'error': str(e)
                })
                self.stats['failed_syncs'] += 1
        
        self.stats['synced_files'] = success_count
        logger.info(f"同步完成，成功: {success_count}, 失敗: {self.stats['failed_syncs']}")
        return success_count > 0
    
    def fix_error_files(self, error_files_list: Optional[List[str]] = None) -> bool:
        """
        修復錯誤檔案清單中的檔案
        
        Args:
            error_files_list: 錯誤檔案清單，如果為 None 則自動檢測
            
        Returns:
            是否成功修復
        """
        if error_files_list is None:
            # 自動檢測錯誤檔案
            error_files_list = self.find_missing_files()
        
        if not error_files_list:
            logger.info("沒有錯誤檔案需要修復")
            return True
        
        logger.info(f"開始修復 {len(error_files_list)} 個錯誤檔案")
        
        success_count = 0
        for filename in error_files_list:
            try:
                # 嘗試從 stage3 重新同步
                stage3_files = self.scan_stage3_files()
                
                if filename in stage3_files:
                    stage3_path = stage3_files[filename]
                    
                    # 建立 stage4 檔案名
                    stage4_filename = filename.replace('.json', '_milvus.json')
                    stage4_path = self.stage4_dir / stage4_filename
                    
                    # 如果 stage4 檔案已存在，先備份
                    if stage4_path.exists():
                        backup_path = stage4_path.with_suffix('.milvus.json.backup')
                        shutil.copy2(stage4_path, backup_path)
                        logger.info(f"備份原檔案: {stage4_filename}")
                    
                    # 複製檔案
                    shutil.copy2(stage3_path, stage4_path)
                    
                    logger.info(f"修復檔案: {filename}")
                    success_count += 1
                else:
                    logger.warning(f"stage3 中找不到檔案: {filename}")
                    self.stats['error_files'].append({
                        'filename': filename,
                        'error': 'stage3 中找不到檔案'
                    })
                    
            except Exception as e:
                logger.error(f"修復檔案失敗 {filename}: {e}")
                self.stats['error_files'].append({
                    'filename': filename,
                    'error': str(e)
                })
        
        logger.info(f"修復完成，成功: {success_count}")
        return success_count > 0
    
    def validate_stage4_files(self) -> Dict[str, List[str]]:
        """
        驗證 stage4 檔案的完整性
        
        Returns:
            驗證結果，包含錯誤檔案列表
        """
        stage3_files = self.scan_stage3_files()
        stage4_files = self.scan_stage4_files()
        
        validation_results = {
            'missing_files': [],
            'corrupted_files': [],
            'extra_files': []
        }
        
        # 檢查缺少的檔案
        for filename in stage3_files.keys():
            if filename not in stage4_files:
                validation_results['missing_files'].append(filename)
        
        # 檢查多餘的檔案
        for filename in stage4_files.keys():
            if filename not in stage3_files:
                validation_results['extra_files'].append(filename)
        
        # 檢查檔案完整性
        for filename, stage4_path in stage4_files.items():
            try:
                with open(stage4_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 檢查基本結構
                if not isinstance(data, dict) or 'chunks' not in data:
                    validation_results['corrupted_files'].append(filename)
                    
            except Exception as e:
                logger.error(f"驗證檔案失敗 {filename}: {e}")
                validation_results['corrupted_files'].append(filename)
        
        return validation_results
    
    def generate_sync_report(self) -> str:
        """
        生成同步報告
        
        Returns:
            報告內容
        """
        validation_results = self.validate_stage4_files()
        
        report = f"""
=== Stage 同步報告 ===
處理時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

統計資訊:
- Stage3 檔案數: {self.stats['stage3_files']}
- Stage4 檔案數: {self.stats['stage4_files']}
- 缺少檔案數: {self.stats['missing_files']}
- 同步成功: {self.stats['synced_files']}
- 同步失敗: {self.stats['failed_syncs']}

驗證結果:
- 缺少檔案: {len(validation_results['missing_files'])}
- 損壞檔案: {len(validation_results['corrupted_files'])}
- 多餘檔案: {len(validation_results['extra_files'])}

錯誤檔案列表:
"""
        
        for error in self.stats['error_files']:
            report += f"- {error['filename']}: {error['error']}\n"
        
        if validation_results['missing_files']:
            report += "\n缺少檔案列表:\n"
            for filename in validation_results['missing_files']:
                report += f"- {filename}\n"
        
        if validation_results['corrupted_files']:
            report += "\n損壞檔案列表:\n"
            for filename in validation_results['corrupted_files']:
                report += f"- {filename}\n"
        
        # 寫入報告檔案
        report_file = Path(__file__).parent.parent / 'stage_sync_report.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"同步報告已寫入 {report_file}")
        return report
    
    def run(self, fix_errors: bool = True) -> bool:
        """
        執行完整的 stage 同步流程
        
        Args:
            fix_errors: 是否自動修復錯誤檔案
            
        Returns:
            是否全部成功
        """
        logger.info("開始 Stage 同步處理...")
        
        success = True
        
        # 1. 掃描檔案
        logger.info("步驟 1: 掃描 stage3 和 stage4 檔案")
        self.scan_stage3_files()
        self.scan_stage4_files()
        
        # 2. 同步缺少的檔案
        logger.info("步驟 2: 同步缺少的檔案")
        if not self.sync_missing_files():
            success = False
        
        # 3. 修復錯誤檔案（如果需要）
        if fix_errors:
            logger.info("步驟 3: 修復錯誤檔案")
            if not self.fix_error_files():
                success = False
        
        # 4. 生成報告
        logger.info("步驟 4: 生成同步報告")
        self.generate_sync_report()
        
        logger.info("Stage 同步處理完成！")
        return success 