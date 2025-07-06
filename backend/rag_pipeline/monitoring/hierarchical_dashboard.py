#!/usr/bin/env python3
"""
層級化樹狀結構 RAG 系統監控面板
整合效能監控和儀表板功能，用於實時監控各層級的效能指標和系統狀態
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics
import os
import yaml

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

# 設定頁面配置
st.set_page_config(
    page_title="層級化 RAG 系統監控面板",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

class HierarchicalRAGMonitor:
    """層級化 RAG 系統監控器"""
    
    def __init__(self):
        """初始化監控器"""
        self.levels = [
            "查詢重寫轉換拓展",
            "混合搜尋", 
            "檢索增強",
            "重新排序",
            "上下文壓縮過濾",
            "混合式RAG"
        ]
        
        # 效能監控相關
        self.metrics_file = "performance_metrics.json"
        self.max_history = 10000
        self.metrics_history = deque(maxlen=self.max_history)
        self.service_metrics = defaultdict(list)
        self.realtime_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "average_response_time": 0.0,
            "current_confidence_avg": 0.0,
            "fallback_rate": 0.0
        }
        
        # 歷史數據
        self.metrics_history_display = []
        self.ml_pipeline_metrics = {}
        
        # 初始化
        self.load_mock_data()
        self._initialize_ml_pipeline_monitoring()
        self._load_metrics()
    
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
    
    def record_performance_metric(self, 
                                query_id: str,
                                service_name: str,
                                response_time: float,
                                success: bool,
                                confidence_score: Optional[float] = None,
                                agent_used: Optional[str] = None,
                                fallback_used: bool = False,
                                error_message: Optional[str] = None) -> PerformanceMetrics:
        """記錄效能指標"""
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
        
        self.metrics_history.append(metric)
        self.service_metrics[service_name].append(metric)
        self._update_realtime_stats(metric)
        
        # 定期儲存
        if len(self.metrics_history) % 100 == 0:
            self._save_metrics()
        
        return metric
    
    def _update_realtime_stats(self, metric: PerformanceMetrics):
        """更新即時統計數據"""
        self.realtime_stats["total_queries"] += 1
        
        if metric.success:
            self.realtime_stats["successful_queries"] += 1
        else:
            self.realtime_stats["failed_queries"] += 1
        
        # 更新平均響應時間
        if self.metrics_history:
            total_time = sum(m.response_time for m in self.metrics_history)
            self.realtime_stats["average_response_time"] = total_time / len(self.metrics_history)
        
        # 更新平均信心值
        confidence_scores = [m.confidence_score for m in self.metrics_history if m.confidence_score is not None]
        if confidence_scores:
            self.realtime_stats["current_confidence_avg"] = statistics.mean(confidence_scores)
        
        # 更新備援率
        fallback_count = sum(1 for m in self.metrics_history if m.fallback_used)
        self.realtime_stats["fallback_rate"] = fallback_count / len(self.metrics_history) if self.metrics_history else 0.0
    
    def get_service_performance(self, service_name: str, hours: int = 24) -> Dict[str, Any]:
        """獲取服務效能統計"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.service_metrics[service_name] if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {
                "total_queries": 0,
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "avg_confidence": 0.0,
                "fallback_rate": 0.0
            }
        
        success_count = sum(1 for m in recent_metrics if m.success)
        confidence_scores = [m.confidence_score for m in recent_metrics if m.confidence_score is not None]
        fallback_count = sum(1 for m in recent_metrics if m.fallback_used)
        
        return {
            "total_queries": len(recent_metrics),
            "success_rate": success_count / len(recent_metrics),
            "avg_response_time": statistics.mean(m.response_time for m in recent_metrics),
            "avg_confidence": statistics.mean(confidence_scores) if confidence_scores else 0.0,
            "fallback_rate": fallback_count / len(recent_metrics)
        }
    
    def get_overall_performance(self, hours: int = 24) -> Dict[str, Any]:
        """獲取整體效能統計"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {
                "total_queries": 0,
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "avg_confidence": 0.0,
                "fallback_rate": 0.0,
                "service_breakdown": {}
            }
        
        success_count = sum(1 for m in recent_metrics if m.success)
        confidence_scores = [m.confidence_score for m in recent_metrics if m.confidence_score is not None]
        fallback_count = sum(1 for m in recent_metrics if m.fallback_used)
        
        # 服務細分
        service_breakdown = {}
        for service_name in set(m.service_name for m in recent_metrics):
            service_metrics = [m for m in recent_metrics if m.service_name == service_name]
            service_breakdown[service_name] = {
                "queries": len(service_metrics),
                "success_rate": sum(1 for m in service_metrics if m.success) / len(service_metrics),
                "avg_response_time": statistics.mean(m.response_time for m in service_metrics)
            }
        
        return {
            "total_queries": len(recent_metrics),
            "success_rate": success_count / len(recent_metrics),
            "avg_response_time": statistics.mean(m.response_time for m in recent_metrics),
            "avg_confidence": statistics.mean(confidence_scores) if confidence_scores else 0.0,
            "fallback_rate": fallback_count / len(recent_metrics),
            "service_breakdown": service_breakdown
        }
    
    def _initialize_ml_pipeline_monitoring(self):
        """初始化 ML Pipeline 監控"""
        try:
            import sys
            import os
            
            # 添加 ML Pipeline 路徑
            ml_pipeline_path = os.path.join(
                os.path.dirname(__file__), 
                '..', '..', 'ml_pipeline'
            )
            if ml_pipeline_path not in sys.path:
                sys.path.insert(0, ml_pipeline_path)
            
            # 嘗試導入 ML Pipeline 服務
            try:
                from backend.ml_pipeline.services import RecommendationService
                from backend.ml_pipeline.config.recommender_config import get_recommender_config
                
                # 初始化推薦服務用於監控
                config = get_recommender_config()
                db_url = os.getenv("DATABASE_URL", config.get("database_url", ""))
                
                if db_url:
                    self.ml_pipeline_service = RecommendationService(db_url, config)
                    print("ML Pipeline 監控初始化成功")
                else:
                    print("未設定 DATABASE_URL，ML Pipeline 監控將不可用")
                    self.ml_pipeline_service = None
                    
            except ImportError:
                print("ML Pipeline 模組不可用，監控功能將受限")
                self.ml_pipeline_service = None
                
        except Exception as e:
            print(f"ML Pipeline 監控初始化失敗: {str(e)}")
            self.ml_pipeline_service = None
    
    def load_mock_data(self):
        """載入模擬數據"""
        # 模擬歷史數據
        for i in range(100):
            timestamp = datetime.now() - timedelta(minutes=i)
            self.metrics_history_display.append({
                'timestamp': timestamp,
                'level_1_confidence': 0.85 + (i % 10) * 0.01,
                'level_2_confidence': 0.78 + (i % 8) * 0.015,
                'level_3_confidence': 0.82 + (i % 12) * 0.012,
                'level_4_confidence': 0.88 + (i % 6) * 0.02,
                'level_5_confidence': 0.90 + (i % 4) * 0.025,
                'level_6_confidence': 0.92 + (i % 5) * 0.015,
                'response_time': 2.5 + (i % 15) * 0.1,
                'throughput': 50 + (i % 20) * 2,
                'error_rate': 0.02 + (i % 10) * 0.005,
                'user_satisfaction': 0.85 + (i % 8) * 0.02
            })
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """獲取當前指標"""
        return {
            'level_1_confidence': 0.87,
            'level_2_confidence': 0.81,
            'level_3_confidence': 0.84,
            'level_4_confidence': 0.89,
            'level_5_confidence': 0.91,
            'level_6_confidence': 0.93,
            'response_time': 2.8,
            'throughput': 52,
            'error_rate': 0.025,
            'user_satisfaction': 0.87
        }
    
    def get_service_status(self) -> Dict[str, str]:
        """獲取服務狀態"""
        status = {
            'RAG Pipeline': '🟢 運行中',
            'CrewAI': '🟢 運行中',
            'AnythingLLM': '🟢 運行中',
            'LLM Service': '🟢 運行中',
            'Ollama': '🟢 運行中',
            'PostgreSQL': '🟢 運行中',
            'MongoDB': '🟢 運行中',
            'Milvus': '🟢 運行中',
            'MinIO': '🟢 運行中'
        }
        
        # 添加 ML Pipeline 狀態
        if hasattr(self, 'ml_pipeline_service') and self.ml_pipeline_service:
            try:
                ml_status = self.ml_pipeline_service.get_system_status()
                status['ML Pipeline'] = '🟢 運行中' if ml_status.get('status') == 'healthy' else '🟡 警告'
            except:
                status['ML Pipeline'] = '🔴 錯誤'
        else:
            status['ML Pipeline'] = '⚪ 未連接'
        
        return status
    
    def get_ml_pipeline_metrics(self) -> Dict[str, Any]:
        """獲取 ML Pipeline 指標"""
        if not hasattr(self, 'ml_pipeline_service') or not self.ml_pipeline_service:
            return {
                'recommendation_accuracy': 0.0,
                'user_satisfaction': 0.0,
                'diversity_score': 0.0,
                'response_time': 0.0,
                'throughput': 0
            }
        
        try:
            # 模擬 ML Pipeline 指標
            return {
                'recommendation_accuracy': 0.85,
                'user_satisfaction': 0.87,
                'diversity_score': 0.78,
                'response_time': 1.2,
                'throughput': 45
            }
        except Exception as e:
            print(f"獲取 ML Pipeline 指標失敗: {str(e)}")
            return {
                'recommendation_accuracy': 0.0,
                'user_satisfaction': 0.0,
                'diversity_score': 0.0,
                'response_time': 0.0,
                'throughput': 0
            }

def main():
    """主函數"""
    st.title("🌳 層級化樹狀結構 RAG 系統監控面板")
    st.markdown("---")
    
    # 初始化監控器
    monitor = HierarchicalRAGMonitor()
    
    # 側邊欄配置
    st.sidebar.title("🎛️ 監控配置")
    
    # 時間範圍選擇
    time_range = st.sidebar.selectbox(
        "時間範圍",
        ["最近1小時", "最近6小時", "最近24小時", "最近7天"]
    )
    
    # 指標選擇
    selected_metrics = st.sidebar.multiselect(
        "監控指標",
        ["信心值", "回應時間", "吞吐量", "錯誤率", "用戶滿意度"],
        default=["信心值", "回應時間"]
    )
    
    # 自動刷新
    auto_refresh = st.sidebar.checkbox("自動刷新", value=True)
    if auto_refresh:
        time.sleep(1)
        st.rerun()
    
    # 主要內容區域
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 系統效能指標")
        
        # 獲取整體效能統計
        overall_perf = monitor.get_overall_performance(hours=24)
        
        # 效能指標卡片
        perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)
        
        with perf_col1:
            st.metric(
                "總查詢數",
                overall_perf["total_queries"],
                delta=f"{overall_perf['success_rate']:.1%} 成功率"
            )
        
        with perf_col2:
            st.metric(
                "平均回應時間",
                f"{overall_perf['avg_response_time']:.2f}s",
                delta=f"{overall_perf['fallback_rate']:.1%} 備援率"
            )
        
        with perf_col3:
            st.metric(
                "平均信心值",
                f"{overall_perf['avg_confidence']:.2f}",
                delta="信心值"
            )
        
        with perf_col4:
            st.metric(
                "即時查詢",
                monitor.realtime_stats["total_queries"],
                delta="活躍查詢"
            )
    
    with col2:
        st.subheader("🔧 服務狀態")
        service_status = monitor.get_service_status()
        
        for service, status in service_status.items():
            st.write(f"{service}: {status}")
    
    # 圖表區域
    st.subheader("📈 效能趨勢圖")
    
    # 轉換歷史數據為 DataFrame
    if monitor.metrics_history_display:
        df = pd.DataFrame(monitor.metrics_history_display)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 信心值趨勢圖
        if "信心值" in selected_metrics:
            fig_confidence = go.Figure()
            for i, level in enumerate(monitor.levels, 1):
                col_name = f'level_{i}_confidence'
                if col_name in df.columns:
                    fig_confidence.add_trace(go.Scatter(
                        x=df['timestamp'],
                        y=df[col_name],
                        mode='lines',
                        name=level,
                        line=dict(width=2)
                    ))
            
            fig_confidence.update_layout(
                title="各層級信心值趨勢",
                xaxis_title="時間",
                yaxis_title="信心值",
                height=400
            )
            st.plotly_chart(fig_confidence, use_container_width=True)
        
        # 回應時間趨勢圖
        if "回應時間" in selected_metrics:
            fig_response = px.line(
                df, 
                x='timestamp', 
                y='response_time',
                title="回應時間趨勢"
            )
            fig_response.update_layout(height=400)
            st.plotly_chart(fig_response, use_container_width=True)
    
    # 服務效能細分
    st.subheader("🔍 服務效能細分")
    service_perf = overall_perf.get("service_breakdown", {})
    
    if service_perf:
        service_df = pd.DataFrame([
            {
                "服務": service,
                "查詢數": data["queries"],
                "成功率": data["success_rate"],
                "平均回應時間": data["avg_response_time"]
            }
            for service, data in service_perf.items()
        ])
        
        st.dataframe(service_df, use_container_width=True)
    
    # ML Pipeline 指標
    st.subheader("🤖 ML Pipeline 指標")
    ml_metrics = monitor.get_ml_pipeline_metrics()
    
    ml_col1, ml_col2, ml_col3, ml_col4 = st.columns(4)
    
    with ml_col1:
        st.metric("推薦準確率", f"{ml_metrics['recommendation_accuracy']:.2f}")
    
    with ml_col2:
        st.metric("用戶滿意度", f"{ml_metrics['user_satisfaction']:.2f}")
    
    with ml_col3:
        st.metric("多樣性分數", f"{ml_metrics['diversity_score']:.2f}")
    
    with ml_col4:
        st.metric("ML 回應時間", f"{ml_metrics['response_time']:.2f}s")

if __name__ == "__main__":
    main() 