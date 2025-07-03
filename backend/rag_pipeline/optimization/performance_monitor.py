#!/usr/bin/env python3
"""
效能監控模組
追蹤 RAG Pipeline 的各種效能指標，包含響應時間、成功率、資源使用等
"""

import time
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics
import json
import os

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """效能指標數據結構"""
    timestamp: datetime
    query_id: str
    service_name: str
    response_time: float
    success: bool
    error_message: Optional[str] = None
    confidence_score: Optional[float] = None
    agent_used: Optional[str] = None
    fallback_used: bool = False
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None

class PerformanceMonitor:
    """
    效能監控器
    追蹤和記錄系統的各種效能指標
    """
    
    def __init__(self, 
                 metrics_file: str = "performance_metrics.json",
                 max_history: int = 10000,
                 enable_realtime: bool = True):
        """
        初始化效能監控器
        
        Args:
            metrics_file: 指標儲存檔案路徑
            max_history: 最大歷史記錄數量
            enable_realtime: 是否啟用即時監控
        """
        self.metrics_file = metrics_file
        self.max_history = max_history
        self.enable_realtime = enable_realtime
        
        # 效能指標儲存
        self.metrics_history = deque(maxlen=max_history)
        self.service_metrics = defaultdict(list)
        self.realtime_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "average_response_time": 0.0,
            "current_confidence_avg": 0.0,
            "fallback_rate": 0.0
        }
        
        # 載入歷史數據
        self._load_metrics()
        
        logger.info("✅ 效能監控器初始化完成")
    
    def _load_metrics(self):
        """載入歷史效能指標"""
        try:
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for metric_data in data.get('metrics', []):
                        metric = PerformanceMetrics(
                            timestamp=datetime.fromisoformat(metric_data['timestamp']),
                            query_id=metric_data['query_id'],
                            service_name=metric_data['service_name'],
                            response_time=metric_data['response_time'],
                            success=metric_data['success'],
                            error_message=metric_data.get('error_message'),
                            confidence_score=metric_data.get('confidence_score'),
                            agent_used=metric_data.get('agent_used'),
                            fallback_used=metric_data.get('fallback_used', False),
                            memory_usage=metric_data.get('memory_usage'),
                            cpu_usage=metric_data.get('cpu_usage')
                        )
                        self.metrics_history.append(metric)
                        self.service_metrics[metric.service_name].append(metric)
                
                logger.info(f"✅ 載入 {len(self.metrics_history)} 條歷史效能指標")
        except Exception as e:
            logger.warning(f"⚠️ 載入歷史指標失敗: {e}")
    
    def _save_metrics(self):
        """儲存效能指標到檔案"""
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'total_metrics': len(self.metrics_history),
                'metrics': [asdict(metric) for metric in self.metrics_history]
            }
            
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"❌ 儲存效能指標失敗: {e}")
    
    def start_query_timer(self, query_id: str, service_name: str) -> float:
        """
        開始查詢計時器
        
        Args:
            query_id: 查詢 ID
            service_name: 服務名稱
            
        Returns:
            開始時間戳記
        """
        return time.time()
    
    def end_query_timer(self, 
                       start_time: float,
                       query_id: str,
                       service_name: str,
                       success: bool,
                       confidence_score: Optional[float] = None,
                       agent_used: Optional[str] = None,
                       fallback_used: bool = False,
                       error_message: Optional[str] = None) -> PerformanceMetrics:
        """
        結束查詢計時器並記錄指標
        
        Args:
            start_time: 開始時間戳記
            query_id: 查詢 ID
            service_name: 服務名稱
            success: 是否成功
            confidence_score: 信心值分數
            agent_used: 使用的代理
            fallback_used: 是否使用備援
            error_message: 錯誤訊息
            
        Returns:
            效能指標物件
        """
        response_time = time.time() - start_time
        
        # 創建效能指標
        metric = PerformanceMetrics(
            timestamp=datetime.now(),
            query_id=query_id,
            service_name=service_name,
            response_time=response_time,
            success=success,
            error_message=error_message,
            confidence_score=confidence_score,
            agent_used=agent_used,
            fallback_used=fallback_used
        )
        
        # 儲存指標
        self.metrics_history.append(metric)
        self.service_metrics[service_name].append(metric)
        
        # 更新即時統計
        self._update_realtime_stats(metric)
        
        # 定期儲存到檔案
        if len(self.metrics_history) % 100 == 0:
            self._save_metrics()
        
        logger.info(f"📊 效能指標記錄: {service_name} - {response_time:.3f}s - {'成功' if success else '失敗'}")
        
        return metric
    
    def _update_realtime_stats(self, metric: PerformanceMetrics):
        """更新即時統計數據"""
        self.realtime_stats["total_queries"] += 1
        
        if metric.success:
            self.realtime_stats["successful_queries"] += 1
        else:
            self.realtime_stats["failed_queries"] += 1
        
        # 更新平均響應時間
        total_time = sum(m.response_time for m in self.metrics_history)
        self.realtime_stats["average_response_time"] = total_time / len(self.metrics_history)
        
        # 更新平均信心值
        confidence_scores = [m.confidence_score for m in self.metrics_history if m.confidence_score is not None]
        if confidence_scores:
            self.realtime_stats["current_confidence_avg"] = statistics.mean(confidence_scores)
        
        # 更新備援率
        fallback_count = sum(1 for m in self.metrics_history if m.fallback_used)
        self.realtime_stats["fallback_rate"] = fallback_count / len(self.metrics_history)
    
    def get_service_performance(self, service_name: str, hours: int = 24) -> Dict[str, Any]:
        """
        獲取特定服務的效能統計
        
        Args:
            service_name: 服務名稱
            hours: 統計時間範圍（小時）
            
        Returns:
            效能統計數據
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.service_metrics[service_name]
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {
                "service_name": service_name,
                "total_queries": 0,
                "success_rate": 0.0,
                "average_response_time": 0.0,
                "error_count": 0
            }
        
        success_count = sum(1 for m in recent_metrics if m.success)
        response_times = [m.response_time for m in recent_metrics]
        
        return {
            "service_name": service_name,
            "total_queries": len(recent_metrics),
            "success_rate": success_count / len(recent_metrics),
            "average_response_time": statistics.mean(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "error_count": len(recent_metrics) - success_count,
            "confidence_avg": statistics.mean([m.confidence_score for m in recent_metrics if m.confidence_score is not None])
        }
    
    def get_overall_performance(self, hours: int = 24) -> Dict[str, Any]:
        """
        獲取整體效能統計
        
        Args:
            hours: 統計時間範圍（小時）
            
        Returns:
            整體效能統計數據
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {
                "total_queries": 0,
                "success_rate": 0.0,
                "average_response_time": 0.0,
                "service_breakdown": {}
            }
        
        # 整體統計
        success_count = sum(1 for m in recent_metrics if m.success)
        response_times = [m.response_time for m in recent_metrics]
        
        # 服務分解統計
        service_breakdown = {}
        for service_name in set(m.service_name for m in recent_metrics):
            service_breakdown[service_name] = self.get_service_performance(service_name, hours)
        
        return {
            "total_queries": len(recent_metrics),
            "success_rate": success_count / len(recent_metrics),
            "average_response_time": statistics.mean(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "fallback_rate": sum(1 for m in recent_metrics if m.fallback_used) / len(recent_metrics),
            "confidence_avg": statistics.mean([m.confidence_score for m in recent_metrics if m.confidence_score is not None]),
            "service_breakdown": service_breakdown
        }
    
    def get_performance_alerts(self) -> List[Dict[str, Any]]:
        """
        獲取效能警報
        
        Returns:
            警報列表
        """
        alerts = []
        
        # 檢查最近 1 小時的效能
        recent_performance = self.get_overall_performance(hours=1)
        
        # 響應時間警報
        if recent_performance["average_response_time"] > 5.0:  # 超過 5 秒
            alerts.append({
                "type": "high_response_time",
                "severity": "warning",
                "message": f"平均響應時間過高: {recent_performance['average_response_time']:.2f}秒",
                "timestamp": datetime.now().isoformat()
            })
        
        # 成功率警報
        if recent_performance["success_rate"] < 0.8:  # 低於 80%
            alerts.append({
                "type": "low_success_rate",
                "severity": "error",
                "message": f"成功率過低: {recent_performance['success_rate']:.2%}",
                "timestamp": datetime.now().isoformat()
            })
        
        # 備援率警報
        if recent_performance["fallback_rate"] > 0.3:  # 超過 30%
            alerts.append({
                "type": "high_fallback_rate",
                "severity": "warning",
                "message": f"備援率過高: {recent_performance['fallback_rate']:.2%}",
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts
    
    def export_metrics(self, format: str = "json", filepath: Optional[str] = None) -> str:
        """
        匯出效能指標
        
        Args:
            format: 匯出格式 (json/csv)
            filepath: 檔案路徑
            
        Returns:
            匯出檔案路徑
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"performance_metrics_{timestamp}.{format}"
        
        if format.lower() == "json":
            data = {
                'export_timestamp': datetime.now().isoformat(),
                'metrics': [asdict(metric) for metric in self.metrics_history]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        elif format.lower() == "csv":
            import csv
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # 寫入標題
                writer.writerow([
                    'timestamp', 'query_id', 'service_name', 'response_time',
                    'success', 'confidence_score', 'agent_used', 'fallback_used'
                ])
                # 寫入數據
                for metric in self.metrics_history:
                    writer.writerow([
                        metric.timestamp.isoformat(),
                        metric.query_id,
                        metric.service_name,
                        metric.response_time,
                        metric.success,
                        metric.confidence_score,
                        metric.agent_used,
                        metric.fallback_used
                    ])
        
        logger.info(f"✅ 效能指標已匯出到: {filepath}")
        return filepath
    
    def cleanup_old_metrics(self, days: int = 30):
        """
        清理舊的效能指標
        
        Args:
            days: 保留天數
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        original_count = len(self.metrics_history)
        
        # 過濾舊指標
        self.metrics_history = deque(
            [m for m in self.metrics_history if m.timestamp >= cutoff_time],
            maxlen=self.max_history
        )
        
        # 重新整理服務指標
        self.service_metrics.clear()
        for metric in self.metrics_history:
            self.service_metrics[metric.service_name].append(metric)
        
        cleaned_count = original_count - len(self.metrics_history)
        logger.info(f"🧹 清理了 {cleaned_count} 條舊效能指標")
        
        # 儲存更新後的指標
        self._save_metrics() 