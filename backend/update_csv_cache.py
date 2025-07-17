#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新 CSV 快取檔案
當 MinIO 中的音檔有變更時，重新生成 CSV 快取
"""

import sys
from pathlib import Path

# 添加後端路徑
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from scripts.analyze_minio_episodes import MinIOEpisodeAnalyzer
import logging

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_csv_cache():
    """更新 CSV 快取檔案"""
    print("🔄 開始更新 CSV 快取檔案...")
    
    try:
        # 初始化分析器
        analyzer = MinIOEpisodeAnalyzer()
        
        # 生成分析報告
        report = analyzer.generate_analysis_report()
        print("\n" + "="*80)
        print("MINIO 音檔分析報告")
        print("="*80)
        print(report)
        
        # 保存為 CSV
        analyzer.save_analysis_to_csv()
        
        print("\n✅ CSV 快取檔案更新完成！")
        print("📁 檔案位置:")
        print("  - business_episodes_analysis.csv")
        print("  - education_episodes_analysis.csv")
        print("  - all_episodes_analysis.csv")
        
    except Exception as e:
        logger.error(f"更新 CSV 快取失敗: {e}")
        print(f"❌ 更新失敗: {e}")
    finally:
        analyzer.close_connections()

if __name__ == "__main__":
    update_csv_cache() 