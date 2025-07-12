#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
報告生成器工具類別

提供各種格式的報告生成功能

作者: Podwise Team
版本: 2.0.0
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    報告生成器
    
    提供各種格式的報告生成功能
    """
    
    def __init__(self):
        """初始化報告生成器"""
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """設定日誌"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    def generate_csv_report(self, data: List[Dict[str, Any]], 
                           output_path: str,
                           encoding: str = 'utf-8-sig') -> bool:
        """
        生成 CSV 報告
        
        Args:
            data: 數據列表
            output_path: 輸出路徑
            encoding: 編碼格式
            
        Returns:
            bool: 是否成功
        """
        try:
            import pandas as pd
            
            if not data:
                logger.warning("沒有數據可生成報告")
                return False
                
            df = pd.DataFrame(data)
            df.to_csv(output_path, index=False, encoding=encoding)
            
            logger.info(f"CSV 報告已生成: {output_path}")
            return True
            
        except ImportError:
            logger.error("pandas 未安裝，無法生成 CSV 報告")
            return False
        except Exception as e:
            logger.error(f"生成 CSV 報告失敗: {e}")
            return False
            
    def generate_json_report(self, data: Dict[str, Any], 
                            output_path: str) -> bool:
        """
        生成 JSON 報告
        
        Args:
            data: 數據字典
            output_path: 輸出路徑
            
        Returns:
            bool: 是否成功
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"JSON 報告已生成: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"生成 JSON 報告失敗: {e}")
            return False
            
    def generate_text_report(self, content: str, 
                            output_path: str) -> bool:
        """
        生成文字報告
        
        Args:
            content: 報告內容
            output_path: 輸出路徑
            
        Returns:
            bool: 是否成功
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"文字報告已生成: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"生成文字報告失敗: {e}")
            return False
            
    def generate_html_report(self, data: Dict[str, Any], 
                            template_path: Optional[str] = None,
                            output_path: str = "report.html") -> bool:
        """
        生成 HTML 報告
        
        Args:
            data: 數據字典
            template_path: 模板路徑
            output_path: 輸出路徑
            
        Returns:
            bool: 是否成功
        """
        try:
            html_content = self._generate_html_content(data, template_path)
            return self.generate_text_report(html_content, output_path)
            
        except Exception as e:
            logger.error(f"生成 HTML 報告失敗: {e}")
            return False
            
    def _generate_html_content(self, data: Dict[str, Any], 
                              template_path: Optional[str] = None) -> str:
        """生成 HTML 內容"""
        if template_path and Path(template_path).exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        else:
            template = self._get_default_html_template()
            
        # 簡單的模板替換
        html_content = template.replace('{{title}}', data.get('title', '報告'))
        html_content = html_content.replace('{{timestamp}}', 
                                          datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        html_content = html_content.replace('{{content}}', 
                                          json.dumps(data, ensure_ascii=False, indent=2))
        
        return html_content
        
    def _get_default_html_template(self) -> str:
        """獲取預設 HTML 模板"""
        return """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .content { margin-top: 20px; }
        .timestamp { color: #666; font-size: 0.9em; }
        pre { background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{title}}</h1>
        <div class="timestamp">生成時間: {{timestamp}}</div>
    </div>
    <div class="content">
        <pre>{{content}}</pre>
    </div>
</body>
</html>
        """
        
    def generate_summary_report(self, results: List[Dict[str, Any]], 
                               output_path: str = "summary_report.txt") -> bool:
        """
        生成摘要報告
        
        Args:
            results: 結果列表
            output_path: 輸出路徑
            
        Returns:
            bool: 是否成功
        """
        try:
            summary = self._create_summary_content(results)
            return self.generate_text_report(summary, output_path)
            
        except Exception as e:
            logger.error(f"生成摘要報告失敗: {e}")
            return False
            
    def _create_summary_content(self, results: List[Dict[str, Any]]) -> str:
        """創建摘要內容"""
        if not results:
            return "沒有數據可生成摘要"
            
        summary_lines = []
        summary_lines.append("=" * 80)
        summary_lines.append("📊 分析摘要報告")
        summary_lines.append("=" * 80)
        summary_lines.append(f"📅 生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_lines.append(f"📁 數據總數: {len(results)}")
        summary_lines.append("")
        
        # 統計資訊
        if results:
            # 假設有分數欄位
            scores = [r.get('total_score', 0) for r in results if 'total_score' in r]
            if scores:
                summary_lines.append("📈 分數統計:")
                summary_lines.append(f"   • 最高分: {max(scores):.3f}")
                summary_lines.append(f"   • 最低分: {min(scores):.3f}")
                summary_lines.append(f"   • 平均分: {sum(scores)/len(scores):.3f}")
                summary_lines.append("")
                
        # 前 10 名
        if len(results) > 10:
            summary_lines.append("🏆 前 10 名:")
            for i, result in enumerate(results[:10]):
                title = result.get('title', '未知')[:50]
                score = result.get('total_score', 0)
                summary_lines.append(f"   {i+1:2d}. {title:<50} {score:.3f}")
        else:
            summary_lines.append("📋 完整排名:")
            for i, result in enumerate(results):
                title = result.get('title', '未知')[:50]
                score = result.get('total_score', 0)
                summary_lines.append(f"   {i+1:2d}. {title:<50} {score:.3f}")
                
        summary_lines.append("=" * 80)
        
        return "\n".join(summary_lines)
        
    def generate_comparison_report(self, data1: Dict[str, Any], 
                                  data2: Dict[str, Any],
                                  output_path: str = "comparison_report.txt") -> bool:
        """
        生成比較報告
        
        Args:
            data1: 第一組數據
            data2: 第二組數據
            output_path: 輸出路徑
            
        Returns:
            bool: 是否成功
        """
        try:
            comparison = self._create_comparison_content(data1, data2)
            return self.generate_text_report(comparison, output_path)
            
        except Exception as e:
            logger.error(f"生成比較報告失敗: {e}")
            return False
            
    def _create_comparison_content(self, data1: Dict[str, Any], 
                                  data2: Dict[str, Any]) -> str:
        """創建比較內容"""
        comparison_lines = []
        comparison_lines.append("=" * 80)
        comparison_lines.append("📊 數據比較報告")
        comparison_lines.append("=" * 80)
        comparison_lines.append(f"📅 生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        comparison_lines.append("")
        
        # 比較共同欄位
        common_keys = set(data1.keys()) & set(data2.keys())
        
        for key in common_keys:
            val1 = data1[key]
            val2 = data2[key]
            
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                diff = val2 - val1
                comparison_lines.append(f"📊 {key}:")
                comparison_lines.append(f"   • 數據1: {val1}")
                comparison_lines.append(f"   • 數據2: {val2}")
                comparison_lines.append(f"   • 差異: {diff:+.3f}")
                comparison_lines.append("")
            else:
                comparison_lines.append(f"📊 {key}:")
                comparison_lines.append(f"   • 數據1: {val1}")
                comparison_lines.append(f"   • 數據2: {val2}")
                comparison_lines.append("")
                
        comparison_lines.append("=" * 80)
        
        return "\n".join(comparison_lines) 