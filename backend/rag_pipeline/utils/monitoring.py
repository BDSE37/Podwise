#!/usr/bin/env python3
"""
監控模組

整合性能監控、系統狀態追蹤等功能。

作者: Podwise Team
版本: 1.0.0
"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指標數據結構"""
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
    """性能監控器"""
    
    def __init__(self, 
                 metrics_file: str = "performance_metrics.json",
                 max_history: int = 10000,
                 enable_realtime: bool = True):
        """初始化性能監控器"""
        self.metrics_file = metrics_file
        self.max_history = max_history
        self.enable_realtime = enable_realtime
        
        # 性能指標存儲
        self.metrics_history: deque = deque(maxlen=max_history)
        self.realtime_stats: Dict[str, Any] = defaultdict(dict)
        
        # 統計資訊
        self.total_queries = 0
        self.successful_queries = 0
        self.failed_queries = 0
        self.total_response_time = 0.0
        self.avg_confidence = 0.0
        
        logger.info("✅ 性能監控器初始化完成")
    
    def start_query_timer(self, query_id: str, service_name: str) -> float:
        """
        開始查詢計時
        
        Args:
            query_id: 查詢 ID
            service_name: 服務名稱
            
        Returns:
            開始時間戳
        """
        start_time = time.time()
        
        if self.enable_realtime:
            self.realtime_stats[service_name]["active_queries"] = \
                self.realtime_stats[service_name].get("active_queries", 0) + 1
        
        return start_time
    
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
        結束查詢計時
        
        Args:
            start_time: 開始時間
            query_id: 查詢 ID
            service_name: 服務名稱
            success: 是否成功
            confidence_score: 信心度分數
            agent_used: 使用的代理人
            fallback_used: 是否使用備援
            error_message: 錯誤訊息
            
        Returns:
            性能指標
        """
        end_time = time.time()
        response_time = end_time - start_time
        
        # 創建性能指標
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
        
        # 添加到歷史記錄
        self.metrics_history.append(metric)
        
        # 更新統計資訊
        self.total_queries += 1
        self.total_response_time += response_time
        
        if success:
            self.successful_queries += 1
            if confidence_score is not None:
                self.avg_confidence = (
                    (self.avg_confidence * (self.successful_queries - 1) + confidence_score) / 
                    self.successful_queries
                )
        else:
            self.failed_queries += 1
        
        # 更新即時統計
        if self.enable_realtime:
            self._update_realtime_stats(metric)
        
        return metric
    
    def _update_realtime_stats(self, metric: PerformanceMetrics) -> None:
        """更新即時統計"""
        service_name = metric.service_name
        
        # 更新活躍查詢數
        self.realtime_stats[service_name]["active_queries"] = \
            max(0, self.realtime_stats[service_name].get("active_queries", 1) - 1)
        
        # 更新平均回應時間
        current_avg = self.realtime_stats[service_name].get("avg_response_time", 0.0)
        query_count = self.realtime_stats[service_name].get("query_count", 0) + 1
        
        new_avg = (current_avg * (query_count - 1) + metric.response_time) / query_count
        
        self.realtime_stats[service_name].update({
            "avg_response_time": new_avg,
            "query_count": query_count,
            "last_query_time": metric.timestamp.isoformat(),
            "success_rate": (
                self.realtime_stats[service_name].get("successful_queries", 0) + 
                (1 if metric.success else 0)
            ) / query_count
        })
        
        if metric.success:
            self.realtime_stats[service_name]["successful_queries"] = \
                self.realtime_stats[service_name].get("successful_queries", 0) + 1
    
    def get_service_performance(self, service_name: str, hours: int = 24) -> Dict[str, Any]:
        """
        獲取服務性能統計
        
        Args:
            service_name: 服務名稱
            hours: 統計時間範圍（小時）
            
        Returns:
            性能統計
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 篩選指定時間範圍內的指標
        recent_metrics = [
            m for m in self.metrics_history 
            if m.service_name == service_name and m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {
                "service_name": service_name,
                "total_queries": 0,
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "avg_confidence": 0.0,
                "error_rate": 0.0
            }
        
        # 計算統計資訊
        total_queries = len(recent_metrics)
        successful_queries = sum(1 for m in recent_metrics if m.success)
        total_response_time = sum(m.response_time for m in recent_metrics)
        avg_response_time = total_response_time / total_queries
        success_rate = successful_queries / total_queries
        
        # 計算平均信心度
        confidence_scores = [m.confidence_score for m in recent_metrics if m.confidence_score is not None]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            "service_name": service_name,
            "total_queries": total_queries,
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "avg_confidence": avg_confidence,
            "error_rate": 1.0 - success_rate,
            "time_range_hours": hours
        }
    
    def get_overall_performance(self, hours: int = 24) -> Dict[str, Any]:
        """
        獲取整體性能統計
        
        Args:
            hours: 統計時間範圍（小時）
            
        Returns:
            整體性能統計
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 篩選指定時間範圍內的指標
        recent_metrics = [
            m for m in self.metrics_history 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {
                "total_queries": 0,
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "avg_confidence": 0.0,
                "services": {}
            }
        
        # 計算整體統計
        total_queries = len(recent_metrics)
        successful_queries = sum(1 for m in recent_metrics if m.success)
        total_response_time = sum(m.response_time for m in recent_metrics)
        avg_response_time = total_response_time / total_queries
        success_rate = successful_queries / total_queries
        
        # 計算平均信心度
        confidence_scores = [m.confidence_score for m in recent_metrics if m.confidence_score is not None]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # 按服務分組統計
        services = {}
        for metric in recent_metrics:
            if metric.service_name not in services:
                services[metric.service_name] = {
                    "total_queries": 0,
                    "successful_queries": 0,
                    "total_response_time": 0.0,
                    "confidence_scores": []
                }
            
            services[metric.service_name]["total_queries"] += 1
            services[metric.service_name]["total_response_time"] += metric.response_time
            
            if metric.success:
                services[metric.service_name]["successful_queries"] += 1
            
            if metric.confidence_score is not None:
                services[metric.service_name]["confidence_scores"].append(metric.confidence_score)
        
        # 計算每個服務的統計
        for service_name, stats in services.items():
            stats["success_rate"] = stats["successful_queries"] / stats["total_queries"]
            stats["avg_response_time"] = stats["total_response_time"] / stats["total_queries"]
            stats["avg_confidence"] = (
                sum(stats["confidence_scores"]) / len(stats["confidence_scores"])
                if stats["confidence_scores"] else 0.0
            )
            del stats["confidence_scores"]
        
        return {
            "total_queries": total_queries,
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "avg_confidence": avg_confidence,
            "services": services,
            "time_range_hours": hours
        }
    
    def get_performance_alerts(self) -> list:
        """
        獲取性能警報
        
        Returns:
            警報列表
        """
        alerts = []
        
        # 檢查整體成功率
        if self.total_queries > 0:
            success_rate = self.successful_queries / self.total_queries
            if success_rate < 0.8:
                alerts.append({
                    "type": "low_success_rate",
                    "message": f"整體成功率過低: {success_rate:.2%}",
                    "severity": "high" if success_rate < 0.6 else "medium",
                    "timestamp": datetime.now().isoformat()
                })
        
        # 檢查平均回應時間
        if self.total_queries > 0:
            avg_response_time = self.total_response_time / self.total_queries
            if avg_response_time > 10.0:
                alerts.append({
                    "type": "high_response_time",
                    "message": f"平均回應時間過高: {avg_response_time:.2f}秒",
                    "severity": "high" if avg_response_time > 30.0 else "medium",
                    "timestamp": datetime.now().isoformat()
                })
        
        # 檢查即時統計
        for service_name, stats in self.realtime_stats.items():
            if stats.get("active_queries", 0) > 100:
                alerts.append({
                    "type": "high_concurrency",
                    "message": f"{service_name} 服務並發量過高: {stats['active_queries']}",
                    "severity": "medium",
                    "timestamp": datetime.now().isoformat()
                })
        
        return alerts
    
    def export_metrics(self, format: str = "json", filepath: Optional[str] = None) -> str:
        """
        匯出性能指標
        
        Args:
            format: 匯出格式
            filepath: 檔案路徑
            
        Returns:
            匯出檔案路徑
        """
        import json
        from datetime import datetime
        
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"performance_metrics_{timestamp}.{format}"
        
        try:
            if format.lower() == "json":
                # 轉換為可序列化的格式
                export_data = {
                    "export_timestamp": datetime.now().isoformat(),
                    "total_queries": self.total_queries,
                    "successful_queries": self.successful_queries,
                    "failed_queries": self.failed_queries,
                    "avg_response_time": self.total_response_time / max(self.total_queries, 1),
                    "avg_confidence": self.avg_confidence,
                    "metrics": [
                        {
                            "timestamp": m.timestamp.isoformat(),
                            "query_id": m.query_id,
                            "service_name": m.service_name,
                            "response_time": m.response_time,
                            "success": m.success,
                            "confidence_score": m.confidence_score,
                            "agent_used": m.agent_used,
                            "fallback_used": m.fallback_used
                        }
                        for m in self.metrics_history
                    ]
                }
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 性能指標已匯出到: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ 匯出性能指標失敗: {e}")
            raise
    
    def cleanup_old_metrics(self, days: int = 30) -> None:
        """
        清理舊的性能指標
        
        Args:
            days: 保留天數
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # 移除舊指標
        original_count = len(self.metrics_history)
        self.metrics_history = deque(
            [m for m in self.metrics_history if m.timestamp >= cutoff_time],
            maxlen=self.max_history
        )
        
        removed_count = original_count - len(self.metrics_history)
        if removed_count > 0:
            logger.info(f"🧹 清理了 {removed_count} 個舊性能指標")


def get_performance_monitor() -> PerformanceMonitor:
    """獲取性能監控器實例"""
    return PerformanceMonitor() 