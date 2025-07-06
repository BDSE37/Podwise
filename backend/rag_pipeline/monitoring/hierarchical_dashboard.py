#!/usr/bin/env python3
"""
層級化樹狀結構 RAG 系統監控面板
用於實時監控各層級的效能指標和系統狀態
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import yaml

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
        
        self.metrics_history = []
        self.ml_pipeline_metrics = {}
        self.load_mock_data()
        self._initialize_ml_pipeline_monitoring()
    
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
                from services import RecommendationService
                from config.recommender_config import get_recommender_config
                
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
            self.metrics_history.append({
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
        st.subheader("📊 層級化效能指標")
        
        # 獲取當前指標
        current_metrics = monitor.get_current_metrics()
        
        # 信心值圖表
        if "信心值" in selected_metrics:
            confidence_data = {
                '層級': monitor.levels,
                '信心值': [
                    current_metrics['level_1_confidence'],
                    current_metrics['level_2_confidence'],
                    current_metrics['level_3_confidence'],
                    current_metrics['level_4_confidence'],
                    current_metrics['level_5_confidence'],
                    current_metrics['level_6_confidence']
                ]
            }
            
            df_confidence = pd.DataFrame(confidence_data)
            
            fig_confidence = px.bar(
                df_confidence,
                x='層級',
                y='信心值',
                title="各層級信心值",
                color='信心值',
                color_continuous_scale='RdYlGn',
                range_color=[0.5, 1.0]
            )
            
            fig_confidence.update_layout(
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig_confidence, use_container_width=True)
        
        # 回應時間圖表
        if "回應時間" in selected_metrics:
            # 模擬各層級回應時間
            response_times = [0.5, 1.2, 0.8, 0.6, 0.4, 2.0]
            
            fig_response = px.line(
                x=monitor.levels,
                y=response_times,
                title="各層級回應時間 (秒)",
                markers=True
            )
            
            fig_response.update_layout(
                height=300,
                xaxis_title="層級",
                yaxis_title="回應時間 (秒)"
            )
            
            st.plotly_chart(fig_response, use_container_width=True)
    
    with col2:
        st.subheader("🔧 系統狀態")
        
        # 服務狀態
        service_status = monitor.get_service_status()
        
        for service, status in service_status.items():
            st.markdown(f"**{service}**: {status}")
        
        st.markdown("---")
        
        # 關鍵指標卡片
        st.subheader("📈 關鍵指標")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.metric(
                label="平均信心值",
                value=f"{current_metrics['level_6_confidence']:.3f}",
                delta="+0.02"
            )
            
            st.metric(
                label="回應時間",
                value=f"{current_metrics['response_time']:.1f}s",
                delta="-0.2s"
            )
        
        with col_b:
            st.metric(
                label="吞吐量",
                value=f"{current_metrics['throughput']} req/min",
                delta="+3"
            )
            
            st.metric(
                label="錯誤率",
                value=f"{current_metrics['error_rate']:.3f}",
                delta="-0.005"
            )
    
    # 詳細監控區域
    st.markdown("---")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🔄 層級間數據流")
        
        # 層級間數據流圖
        fig_flow = go.Figure()
        
        # 添加節點
        node_x = [0, 0, 0, 0, 0, 0]
        node_y = [0, 1, 2, 3, 4, 5]
        node_text = monitor.levels
        
        fig_flow.add_trace(go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            marker=dict(size=20, color='lightblue'),
            text=node_text,
            textposition="middle right",
            name="層級"
        ))
        
        # 添加連接線
        for i in range(len(node_y) - 1):
            fig_flow.add_trace(go.Scatter(
                x=[0, 0],
                y=[node_y[i], node_y[i + 1]],
                mode='lines',
                line=dict(color='gray', width=2),
                showlegend=False
            ))
        
        fig_flow.update_layout(
            title="層級化數據流",
            height=400,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            showlegend=False
        )
        
        st.plotly_chart(fig_flow, use_container_width=True)
    
    with col4:
        st.subheader("📋 層級詳細信息")
        
        # 層級詳細信息表格
        level_details = []
        for i, level in enumerate(monitor.levels, 1):
            level_details.append({
                '層級': f"第{i}層",
                '名稱': level,
                '信心值': current_metrics[f'level_{i}_confidence'],
                '狀態': '🟢 正常' if current_metrics[f'level_{i}_confidence'] > 0.7 else '🟡 警告',
                '處理時間': f"{0.5 + i * 0.2:.1f}s"
            })
        
        df_details = pd.DataFrame(level_details)
        st.dataframe(df_details, use_container_width=True)
    
    # 歷史趨勢圖
    st.markdown("---")
    st.subheader("📈 歷史趨勢")
    
    # 轉換歷史數據為 DataFrame
    df_history = pd.DataFrame(monitor.metrics_history)
    
    # 選擇要顯示的指標
    if "信心值" in selected_metrics:
        fig_trend = make_subplots(
            rows=2, cols=1,
            subplot_titles=("信心值趨勢", "回應時間趨勢"),
            vertical_spacing=0.1
        )
        
        # 添加信心值趨勢
        for i in range(1, 7):
            fig_trend.add_trace(
                go.Scatter(
                    x=df_history['timestamp'],
                    y=df_history[f'level_{i}_confidence'],
                    name=f"第{i}層",
                    mode='lines'
                ),
                row=1, col=1
            )
        
        # 添加回應時間趨勢
        fig_trend.add_trace(
            go.Scatter(
                x=df_history['timestamp'],
                y=df_history['response_time'],
                name="回應時間",
                mode='lines',
                line=dict(color='red')
            ),
            row=2, col=1
        )
        
        fig_trend.update_layout(height=600, showlegend=True)
        st.plotly_chart(fig_trend, use_container_width=True)
    
    # 告警和建議
    st.markdown("---")
    
    col5, col6 = st.columns(2)
    
    with col5:
        st.subheader("⚠️ 系統告警")
        
        alerts = []
        if current_metrics['error_rate'] > 0.05:
            alerts.append("🔴 錯誤率過高 (>5%)")
        if current_metrics['response_time'] > 5:
            alerts.append("🟡 回應時間過長 (>5s)")
        if current_metrics['level_1_confidence'] < 0.7:
            alerts.append("🟡 第一層信心值偏低")
        
        if alerts:
            for alert in alerts:
                st.error(alert)
        else:
            st.success("✅ 系統運行正常，無告警")
    
    with col6:
        st.subheader("💡 優化建議")
        
        suggestions = []
        if current_metrics['level_2_confidence'] < 0.8:
            suggestions.append("考慮優化混合搜尋策略")
        if current_metrics['throughput'] < 30:
            suggestions.append("增加系統資源或優化性能")
        if current_metrics['user_satisfaction'] < 0.8:
            suggestions.append("改進回應質量和相關性")
        
        if suggestions:
            for suggestion in suggestions:
                st.info(suggestion)
        else:
            st.success("✅ 系統運行良好，無需優化")
    
    # 頁腳
    st.markdown("---")
    st.markdown(
        f"<div style='text-align: center; color: gray;'>"
        f"最後更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"層級化樹狀結構 RAG 系統監控面板"
        f"</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main() 