"""
標籤服務
整合所有標籤處理功能
符合 Google Clean Code 原則
"""

import logging
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# 添加路徑以便匯入模組
sys.path.append(str(Path(__file__).parent.parent))

from ..core.tag_processor import UnifiedTagProcessor
from ..config.settings import config

logger = logging.getLogger(__name__)


class TaggingService:
    """標籤服務 - 整合所有標籤處理功能"""
    
    def __init__(self, tag_csv_path: Optional[str] = None):
        """
        初始化標籤服務
        
        Args:
            tag_csv_path: TAG_info.csv 檔案路徑
        """
        self.tag_csv_path = tag_csv_path or config.tag_csv_path
        self.tag_processor = UnifiedTagProcessor(self.tag_csv_path)
        
        logger.info(f"標籤服務初始化完成，使用標籤檔案: {self.tag_csv_path}")
    
    def process_single_file(self, input_file: Path, output_file: Path) -> bool:
        """
        處理單一檔案
        
        Args:
            input_file: 輸入檔案路徑
            output_file: 輸出檔案路徑
            
        Returns:
            處理是否成功
        """
        try:
            # 讀取輸入檔案
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 處理 chunks
            chunks = data.get('chunks', [])
            if not chunks:
                logger.warning(f"檔案 {input_file} 沒有 chunks 資料")
                return False
            
            # 為每個 chunk 添加標籤
            for chunk in chunks:
                chunk_text = chunk.get('chunk_text', '')
                if chunk_text and chunk_text.strip() != '' and chunk_text.strip() != '!':
                    # 使用統一標籤處理器
                    enhanced_tags = self.tag_processor.process_chunk(chunk_text)
                    chunk['enhanced_tags'] = enhanced_tags
            
            # 保存結果
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"檔案處理完成: {input_file} -> {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"處理檔案失敗 {input_file}: {e}")
            return False
    
    def process_rss_folder(self, rss_folder: str, stage1_dir: str, stage3_dir: str) -> Dict[str, Any]:
        """
        處理單一 RSS 資料夾
        
        Args:
            rss_folder: RSS 資料夾名稱
            stage1_dir: stage1 目錄路徑
            stage3_dir: stage3 目錄路徑
            
        Returns:
            處理結果統計
        """
        stage1_path = Path(stage1_dir)
        stage3_path = Path(stage3_dir)
        
        rss_input_path = stage1_path / rss_folder
        rss_output_path = stage3_path / rss_folder
        
        if not rss_input_path.exists():
            return {
                "rss_folder": rss_folder,
                "error": f"輸入路徑不存在: {rss_input_path}"
            }
        
        # 創建輸出目錄
        rss_output_path.mkdir(parents=True, exist_ok=True)
        
        # 處理所有 JSON 檔案
        json_files = list(rss_input_path.glob("*.json"))
        
        if not json_files:
            return {
                "rss_folder": rss_folder,
                "error": f"沒有找到 JSON 檔案: {rss_input_path}"
            }
        
        total_files = len(json_files)
        successful_files = 0
        failed_files = 0
        total_chunks = 0
        total_tags = 0
        failed_files_list = []
        
        logger.info(f"開始處理 RSS 資料夾: {rss_folder} ({total_files} 個檔案)")
        
        for json_file in json_files:
            output_file = rss_output_path / json_file.name
            
            if self.process_single_file(json_file, output_file):
                successful_files += 1
                
                # 統計 chunks 和 tags
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    chunks = data.get('chunks', [])
                    total_chunks += len(chunks)
                    
                    for chunk in chunks:
                        tags = chunk.get('enhanced_tags', [])
                        total_tags += len(tags)
                        
                except Exception as e:
                    logger.warning(f"統計檔案失敗 {output_file}: {e}")
            else:
                failed_files += 1
                failed_files_list.append(str(json_file))
        
        # 計算處理時間
        processing_time = datetime.now().timestamp()
        
        result = {
            "rss_folder": rss_folder,
            "total_files": total_files,
            "successful_files": successful_files,
            "failed_files": failed_files,
            "total_chunks": total_chunks,
            "total_tags": total_tags,
            "failed_files_list": failed_files_list,
            "processing_time": processing_time,
            "success_rate": successful_files / total_files * 100 if total_files > 0 else 0
        }
        
        logger.info(f"RSS 資料夾處理完成: {rss_folder}")
        logger.info(f"  成功: {successful_files}/{total_files} 檔案")
        logger.info(f"  總 chunks: {total_chunks}, 總標籤: {total_tags}")
        
        return result
    
    def process_multiple_rss_folders(self, rss_folders: List[str], 
                                   stage1_dir: str, stage3_dir: str) -> Dict[str, Dict[str, Any]]:
        """
        處理多個 RSS 資料夾
        
        Args:
            rss_folders: RSS 資料夾名稱列表
            stage1_dir: stage1 目錄路徑
            stage3_dir: stage3 目錄路徑
            
        Returns:
            每個資料夾的處理結果
        """
        results = {}
        
        logger.info(f"開始處理 {len(rss_folders)} 個 RSS 資料夾")
        
        for rss_folder in rss_folders:
            logger.info(f"處理 RSS 資料夾: {rss_folder}")
            result = self.process_rss_folder(rss_folder, stage1_dir, stage3_dir)
            results[rss_folder] = result
        
        # 顯示總體統計
        self._show_overall_stats(results)
        
        return results
    
    def _show_overall_stats(self, results: Dict[str, Dict[str, Any]]) -> None:
        """顯示總體統計"""
        total_files = sum(r.get('total_files', 0) for r in results.values())
        total_successful = sum(r.get('successful_files', 0) for r in results.values())
        total_failed = sum(r.get('failed_files', 0) for r in results.values())
        total_chunks = sum(r.get('total_chunks', 0) for r in results.values())
        total_tags = sum(r.get('total_tags', 0) for r in results.values())
        
        logger.info("=" * 60)
        logger.info("總體處理統計")
        logger.info("=" * 60)
        logger.info(f"總檔案數: {total_files}")
        logger.info(f"成功檔案: {total_successful}")
        logger.info(f"失敗檔案: {total_failed}")
        logger.info(f"總 chunks: {total_chunks}")
        logger.info(f"總標籤: {total_tags}")
        logger.info(f"成功率: {total_successful/total_files*100:.2f}%" if total_files > 0 else "0%")
        logger.info("=" * 60)
    
    def get_tag_statistics(self, stage3_dir: str = None) -> Dict[str, Any]:
        """
        獲取標籤統計資訊
        
        Args:
            stage3_dir: stage3 目錄路徑
            
        Returns:
            標籤統計資訊
        """
        stage3_path = Path(stage3_dir or config.stage3_dir)
        
        if not stage3_path.exists():
            return {"error": f"目錄不存在: {stage3_path}"}
        
        tag_counts = {}
        total_chunks = 0
        total_files = 0
        
        # 遍歷所有檔案
        for json_file in stage3_path.rglob("*.json"):
            total_files += 1
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                chunks = data.get('chunks', [])
                for chunk in chunks:
                    total_chunks += 1
                    tags = chunk.get('enhanced_tags', [])
                    
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                        
            except Exception as e:
                logger.warning(f"統計檔案失敗 {json_file}: {e}")
        
        # 排序標籤
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "total_files": total_files,
            "total_chunks": total_chunks,
            "unique_tags": len(tag_counts),
            "tag_counts": dict(sorted_tags[:50]),  # 只返回前 50 個
            "most_common_tags": sorted_tags[:10]
        } 