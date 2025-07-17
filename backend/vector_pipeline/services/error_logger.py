#!/usr/bin/env python3
"""
錯誤日誌服務模組
提供統一的錯誤記錄與管理功能
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import traceback

class ErrorLogger:
    """
    錯誤日誌管理器
    提供統一的錯誤記錄、查詢與報告功能
    """
    
    def __init__(self, log_dir: Optional[Path] = None):
        """
        初始化錯誤日誌管理器
        
        Args:
            log_dir: 日誌目錄路徑，預設為當前目錄
        """
        self.log_dir = log_dir or Path(__file__).parent.parent
        self.error_log_file = self.log_dir / 'error_log.json'
        self.error_summary_file = self.log_dir / 'error_summary.txt'
        
        # 初始化日誌檔案
        self._init_log_files()
        
        # 統計資訊
        self.stats = {
            'total_errors': 0,
            'critical_errors': 0,
            'warning_errors': 0,
            'info_errors': 0
        }
    
    def _init_log_files(self):
        """初始化日誌檔案"""
        if not self.error_log_file.exists():
            with open(self.error_log_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    
    def log_error(self, 
                  error_type: str, 
                  message: str, 
                  details: Optional[Dict] = None, 
                  severity: str = 'error',
                  context: Optional[str] = None) -> None:
        """
        記錄錯誤
        
        Args:
            error_type: 錯誤類型
            message: 錯誤訊息
            details: 詳細資訊
            severity: 嚴重程度 (critical, error, warning, info)
            context: 錯誤上下文
        """
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'message': message,
            'details': details or {},
            'severity': severity,
            'context': context,
            'traceback': traceback.format_exc()
        }
        
        # 讀取現有日誌
        try:
            with open(self.error_log_file, 'r', encoding='utf-8') as f:
                error_log = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            error_log = []
        
        # 添加新錯誤
        error_log.append(error_entry)
        
        # 寫回日誌檔案
        with open(self.error_log_file, 'w', encoding='utf-8') as f:
            json.dump(error_log, f, ensure_ascii=False, indent=2)
        
        # 更新統計
        self.stats['total_errors'] += 1
        if severity == 'critical':
            self.stats['critical_errors'] += 1
        elif severity == 'warning':
            self.stats['warning_errors'] += 1
        elif severity == 'info':
            self.stats['info_errors'] += 1
        
        # 同時寫入標準日誌
        log_level = getattr(logging, severity.upper(), logging.ERROR)
        logger = logging.getLogger(__name__)
        logger.log(log_level, f"[{error_type}] {message}")
    
    def get_errors(self, 
                   error_type: Optional[str] = None, 
                   severity: Optional[str] = None,
                   limit: Optional[int] = None) -> List[Dict]:
        """
        獲取錯誤記錄
        
        Args:
            error_type: 過濾錯誤類型
            severity: 過濾嚴重程度
            limit: 限制返回數量
            
        Returns:
            錯誤記錄列表
        """
        try:
            with open(self.error_log_file, 'r', encoding='utf-8') as f:
                error_log = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        
        # 過濾錯誤
        filtered_errors = error_log
        
        if error_type:
            filtered_errors = [e for e in filtered_errors if e['error_type'] == error_type]
        
        if severity:
            filtered_errors = [e for e in filtered_errors if e['severity'] == severity]
        
        # 限制數量
        if limit:
            filtered_errors = filtered_errors[-limit:]
        
        return filtered_errors
    
    def clear_errors(self, before_date: Optional[str] = None) -> int:
        """
        清理錯誤記錄
        
        Args:
            before_date: 清理指定日期之前的記錄（ISO 格式）
            
        Returns:
            清理的記錄數量
        """
        try:
            with open(self.error_log_file, 'r', encoding='utf-8') as f:
                error_log = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return 0
        
        original_count = len(error_log)
        
        if before_date:
            # 清理指定日期之前的記錄
            filtered_errors = []
            for error in error_log:
                if error['timestamp'] >= before_date:
                    filtered_errors.append(error)
            error_log = filtered_errors
        else:
            # 清理所有記錄
            error_log = []
        
        # 寫回檔案
        with open(self.error_log_file, 'w', encoding='utf-8') as f:
            json.dump(error_log, f, ensure_ascii=False, indent=2)
        
        cleared_count = original_count - len(error_log)
        return cleared_count
    
    def generate_error_summary(self) -> str:
        """
        生成錯誤摘要報告
        
        Returns:
            摘要報告內容
        """
        errors = self.get_errors()
        
        # 按類型統計
        type_stats = {}
        severity_stats = {}
        
        for error in errors:
            error_type = error['error_type']
            severity = error['severity']
            
            type_stats[error_type] = type_stats.get(error_type, 0) + 1
            severity_stats[severity] = severity_stats.get(severity, 0) + 1
        
        summary = f"""
=== 錯誤摘要報告 ===
生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

總體統計:
- 總錯誤數: {self.stats['total_errors']}
- 嚴重錯誤: {self.stats['critical_errors']}
- 警告錯誤: {self.stats['warning_errors']}
- 資訊錯誤: {self.stats['info_errors']}

按類型統計:
"""
        
        for error_type, count in sorted(type_stats.items()):
            summary += f"- {error_type}: {count}\n"
        
        summary += "\n按嚴重程度統計:\n"
        for severity, count in sorted(severity_stats.items()):
            summary += f"- {severity}: {count}\n"
        
        # 最近錯誤
        recent_errors = self.get_errors(limit=10)
        if recent_errors:
            summary += "\n最近 10 個錯誤:\n"
            for error in recent_errors:
                summary += f"- [{error['timestamp']}] {error['error_type']}: {error['message']}\n"
        
        # 寫入摘要檔案
        with open(self.error_summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        return summary
    
    def export_errors(self, output_file: Path, format: str = 'json') -> bool:
        """
        匯出錯誤記錄
        
        Args:
            output_file: 輸出檔案路徑
            format: 輸出格式 (json, csv, txt)
            
        Returns:
            是否成功匯出
        """
        try:
            errors = self.get_errors()
            
            if format == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(errors, f, ensure_ascii=False, indent=2)
            
            elif format == 'csv':
                import csv
                with open(output_file, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        'timestamp', 'error_type', 'message', 'severity', 'context'
                    ])
                    writer.writeheader()
                    for error in errors:
                        writer.writerow({
                            'timestamp': error['timestamp'],
                            'error_type': error['error_type'],
                            'message': error['message'],
                            'severity': error['severity'],
                            'context': error.get('context', '')
                        })
            
            elif format == 'txt':
                with open(output_file, 'w', encoding='utf-8') as f:
                    for error in errors:
                        f.write(f"[{error['timestamp']}] {error['error_type']}: {error['message']}\n")
                        if error.get('context'):
                            f.write(f"  上下文: {error['context']}\n")
                        f.write("\n")
            
            return True
            
        except Exception as e:
            logging.error(f"匯出錯誤記錄失敗: {e}")
            return False
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        獲取錯誤統計資訊
        
        Returns:
            統計資訊字典
        """
        errors = self.get_errors()
        
        stats = {
            'total_errors': len(errors),
            'error_types': {},
            'severity_levels': {},
            'recent_errors': len([e for e in errors if e['timestamp'] >= 
                                (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat())])
        }
        
        for error in errors:
            error_type = error['error_type']
            severity = error['severity']
            
            stats['error_types'][error_type] = stats['error_types'].get(error_type, 0) + 1
            stats['severity_levels'][severity] = stats['severity_levels'].get(severity, 0) + 1
        
        return stats 