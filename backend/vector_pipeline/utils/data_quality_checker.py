#!/usr/bin/env python3
"""
統一的資料品質檢查工具
整合所有資料品質檢查功能：exclamation 檔案檢查、STT 檔案檢查等
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataQualityChecker:
    """統一的資料品質檢查器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.stage1_path = self.data_dir / "stage1_chunking"
        
    def check_exclamation_files(self) -> Dict[str, Any]:
        """
        檢查 stage1_chunking 中所有檔案的 chunk_text 內容
        找出全部都是 "!" 的檔案清單
        """
        logger.info("=== 開始檢查 exclamation 檔案 ===")
        
        if not self.stage1_path.exists():
            logger.error(f"目錄不存在: {self.stage1_path}")
            return {}
        
        # 統計資訊
        stats = {
            'total_files': 0,
            'processed_files': 0,
            'error_files': 0,
            'all_exclamation_files': [],
            'partial_exclamation_files': [],
            'normal_files': [],
            'file_details': []
        }
        
        # 尋找所有 JSON 檔案
        json_files = list(self.stage1_path.rglob("*.json"))
        stats['total_files'] = len(json_files)
        
        logger.info(f"找到 {len(json_files)} 個 JSON 檔案")
        
        # 檢查每個檔案
        for i, json_file in enumerate(json_files, 1):
            logger.info(f"檢查進度: {i}/{len(json_files)} - {json_file.name}")
            
            result = self._check_chunk_text_content(json_file)
            stats['file_details'].append(result)
            
            if result['error']:
                stats['error_files'] += 1
                logger.warning(f"檔案檢查失敗: {json_file} - {result['error']}")
            else:
                stats['processed_files'] += 1
                
                if result['all_exclamation']:
                    stats['all_exclamation_files'].append(result['file_path'])
                    logger.warning(f"發現全部都是 '!' 的檔案: {json_file}")
                elif result['exclamation_only_chunks'] > 0:
                    stats['partial_exclamation_files'].append({
                        'file_path': result['file_path'],
                        'total_chunks': result['total_chunks'],
                        'exclamation_chunks': result['exclamation_only_chunks']
                    })
                    logger.info(f"發現部分 '!' 的檔案: {json_file} ({result['exclamation_only_chunks']}/{result['total_chunks']})")
                else:
                    stats['normal_files'].append(result['file_path'])
        
        return stats
    
    def _check_chunk_text_content(self, file_path: Path) -> Dict[str, Any]:
        """檢查單一檔案的 chunk_text 內容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'chunks' not in data:
                return {
                    'file_path': str(file_path),
                    'has_chunks': False,
                    'total_chunks': 0,
                    'exclamation_only_chunks': 0,
                    'all_exclamation': False,
                    'error': 'No chunks field found'
                }
            
            chunks = data['chunks']
            total_chunks = len(chunks)
            exclamation_only_chunks = 0
            
            for chunk in chunks:
                if 'chunk_text' not in chunk:
                    continue
                
                chunk_text = chunk['chunk_text']
                
                # 檢查是否只包含 "!" 字符
                if chunk_text and chunk_text.strip() and all(char == '!' for char in chunk_text.strip()):
                    exclamation_only_chunks += 1
            
            # 如果所有 chunk 都只包含 "!"
            all_exclamation = (exclamation_only_chunks == total_chunks and total_chunks > 0)
            
            return {
                'file_path': str(file_path),
                'has_chunks': True,
                'total_chunks': total_chunks,
                'exclamation_only_chunks': exclamation_only_chunks,
                'all_exclamation': all_exclamation,
                'error': None
            }
            
        except Exception as e:
            return {
                'file_path': str(file_path),
                'has_chunks': False,
                'total_chunks': 0,
                'exclamation_only_chunks': 0,
                'all_exclamation': False,
                'error': str(e)
            }
    
    def check_stt_files(self) -> Dict[str, Any]:
        """檢查 STT 檔案品質"""
        logger.info("=== 開始檢查 STT 檔案 ===")
        
        # 這裡可以添加 STT 檔案檢查邏輯
        # 暫時返回空字典
        return {}
    
    def generate_report(self, stats: Dict[str, Any], report_type: str = "exclamation") -> str:
        """生成檢查報告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"{report_type}_check_report_{timestamp}.json"
        
        # 添加報告生成時間
        stats['report_generated_at'] = datetime.now().isoformat()
        stats['report_type'] = report_type
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            logger.info(f"報告已生成: {report_file}")
            return report_file
        except Exception as e:
            logger.error(f"生成報告失敗: {e}")
            return ""
    
    def save_exclamation_list_to_txt(self, stats: Dict[str, Any]) -> Optional[str]:
        """將 exclamation 檔案清單保存為 txt 檔案"""
        exclamation_files = stats.get('all_exclamation_files', [])
        
        if not exclamation_files:
            logger.warning("沒有發現 exclamation 檔案")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"exclamation_files_list_{timestamp}.txt"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                # 寫入標題
                f.write("="*80 + "\n")
                f.write("🔴 全部都是 '!' 的檔案清單\n")
                f.write("="*80 + "\n")
                f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"總計: {len(exclamation_files)} 個檔案\n")
                f.write("\n")
                
                # 按 RSS 資料夾分組
                rss_groups = {}
                for file_path in exclamation_files:
                    parts = file_path.split('/')
                    if len(parts) >= 3:
                        rss_folder = parts[2]  # data/stage1_chunking/RSS_XXXXX
                        if rss_folder not in rss_groups:
                            rss_groups[rss_folder] = []
                        rss_groups[rss_folder].append(file_path)
                
                # 寫入分組結果
                for rss_folder, files in rss_groups.items():
                    f.write(f"📁 {rss_folder} ({len(files)} 個檔案)\n")
                    f.write("-" * 60 + "\n")
                    
                    for i, file_path in enumerate(files, 1):
                        file_name = file_path.split('/')[-1]
                        f.write(f"{i:3d}. {file_name}\n")
                    
                    f.write("\n")
                
                # 寫入完整路徑清單
                f.write("="*80 + "\n")
                f.write("📋 完整檔案路徑清單\n")
                f.write("="*80 + "\n")
                
                for i, file_path in enumerate(exclamation_files, 1):
                    f.write(f"{i:3d}. {file_path}\n")
                
                f.write("\n")
                f.write("="*80 + "\n")
                f.write(f"總計: {len(exclamation_files)} 個檔案\n")
                f.write("="*80 + "\n")
                
                # 寫入問題分析
                f.write("\n")
                f.write("🔍 問題分析\n")
                f.write("-" * 40 + "\n")
                f.write("這些檔案的 chunk_text 都只包含 \"!\" 字符，這表示：\n")
                f.write("1. 可能是 STT 處理問題：語音轉文字過程中出現錯誤\n")
                f.write("2. 可能是原始音訊問題：音訊檔案品質不佳或格式問題\n")
                f.write("3. 可能是處理流程問題：在 chunking 過程中出現錯誤\n")
                f.write("\n")
                f.write("💡 建議處理方式\n")
                f.write("-" * 40 + "\n")
                f.write("1. 重新進行 STT 處理：對這些檔案重新進行語音轉文字\n")
                f.write("2. 檢查原始音訊：確認音訊檔案是否正常\n")
                f.write("3. 跳過問題檔案：在後續的標籤提取和向量化處理中跳過這些檔案\n")
                f.write("4. 標記問題檔案：建立問題檔案清單，避免影響後續處理\n")
            
            logger.info(f"檔案清單已保存: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"保存檔案清單失敗: {e}")
            return None
    
    def print_report_summary(self, stats: Dict[str, Any]):
        """打印報告摘要"""
        print("\n" + "="*60)
        print("檢查結果報告")
        print("="*60)
        print(f"總檔案數: {stats['total_files']}")
        print(f"成功處理: {stats['processed_files']}")
        print(f"處理失敗: {stats['error_files']}")
        print()
        
        # 全部都是 "!" 的檔案
        print("🔴 全部都是 '!' 的檔案清單:")
        print("-" * 40)
        if stats['all_exclamation_files']:
            for i, file_path in enumerate(stats['all_exclamation_files'], 1):
                print(f"{i:3d}. {file_path}")
        else:
            print("✅ 沒有發現全部都是 '!' 的檔案")
        print()
        
        # 部分包含 "!" 的檔案
        print("🟡 部分包含 '!' 的檔案清單:")
        print("-" * 40)
        if stats['partial_exclamation_files']:
            for i, file_info in enumerate(stats['partial_exclamation_files'], 1):
                print(f"{i:3d}. {file_info['file_path']}")
                print(f"     (總chunks: {file_info['total_chunks']}, '!' chunks: {file_info['exclamation_chunks']})")
        else:
            print("✅ 沒有發現部分包含 '!' 的檔案")
        print()
        
        # 正常檔案統計
        print("🟢 正常檔案統計:")
        print("-" * 40)
        print(f"正常檔案數: {len(stats['normal_files'])}")
        print(f"正常檔案比例: {len(stats['normal_files'])/stats['total_files']*100:.2f}%")
        print()
        
        # 詳細統計
        print("📊 詳細統計:")
        print("-" * 40)
        total_exclamation_files = len(stats['all_exclamation_files']) + len(stats['partial_exclamation_files'])
        print(f"包含 '!' 的檔案總數: {total_exclamation_files}")
        print(f"包含 '!' 的檔案比例: {total_exclamation_files/stats['total_files']*100:.2f}%")
        
        # 計算總的 exclamation chunks
        total_exclamation_chunks = 0
        for file_info in stats['file_details']:
            if file_info['exclamation_only_chunks']:
                total_exclamation_chunks += file_info['exclamation_only_chunks']
        
        total_chunks = sum(file_info['total_chunks'] for file_info in stats['file_details'])
        if total_chunks > 0:
            print(f"總 chunks 數: {total_chunks}")
            print(f"'!' chunks 數: {total_exclamation_chunks}")
            print(f"'!' chunks 比例: {total_exclamation_chunks/total_chunks*100:.2f}%")
        
        print("="*60)

def main():
    """主函數"""
    checker = DataQualityChecker()
    
    # 檢查 exclamation 檔案
    stats = checker.check_exclamation_files()
    
    if stats:
        # 打印報告摘要
        checker.print_report_summary(stats)
        
        # 生成 JSON 報告
        report_file = checker.generate_report(stats, "exclamation")
        
        # 保存 txt 清單
        txt_file = checker.save_exclamation_list_to_txt(stats)
        
        print(f"\n📊 報告檔案:")
        print(f"JSON 報告: {report_file}")
        if txt_file:
            print(f"TXT 清單: {txt_file}")

if __name__ == "__main__":
    main() 