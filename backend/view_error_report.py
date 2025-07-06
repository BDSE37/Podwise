"""
錯誤報告查看器
用於查看和分析向量化過程中的錯誤報告
"""

import argparse
import json
import csv
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class ErrorReportViewer:
    """錯誤報告查看器"""
    
    def __init__(self, error_logs_dir: str = "error_logs"):
        """
        初始化查看器
        
        Args:
            error_logs_dir: 錯誤日誌目錄
        """
        self.error_logs_dir = Path(error_logs_dir)
    
    def list_error_files(self) -> List[Path]:
        """列出所有錯誤報告檔案"""
        if not self.error_logs_dir.exists():
            print(f"錯誤日誌目錄不存在: {self.error_logs_dir}")
            return []
        
        json_files = list(self.error_logs_dir.glob("*.json"))
        csv_files = list(self.error_logs_dir.glob("*.csv"))
        
        all_files = json_files + csv_files
        all_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return all_files
    
    def view_json_report(self, file_path: Path) -> None:
        """查看 JSON 格式的錯誤報告"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"\n=== JSON 錯誤報告: {file_path.name} ===")
            
            # 顯示摘要
            summary = data.get('summary', {})
            print(f"總錯誤數: {summary.get('total_errors', 0)}")
            print(f"生成時間: {summary.get('generated_at', 'N/A')}")
            
            error_types = summary.get('error_types', {})
            if error_types:
                print("\n錯誤類型統計:")
                for error_type, count in error_types.items():
                    print(f"  {error_type}: {count}")
            
            # 顯示詳細錯誤
            errors = data.get('errors', [])
            if errors:
                print(f"\n詳細錯誤 (顯示前10個):")
                for i, error in enumerate(errors[:10], 1):
                    print(f"\n{i}. Collection: {error.get('collection_id', 'N/A')}")
                    print(f"   RSS ID: {error.get('rss_id', 'N/A')}")
                    print(f"   Title: {error.get('title', 'N/A')}")
                    print(f"   Error Type: {error.get('error_type', 'N/A')}")
                    print(f"   Stage: {error.get('processing_stage', 'N/A')}")
                    print(f"   Message: {error.get('error_message', 'N/A')}")
                    print(f"   Time: {error.get('timestamp', 'N/A')}")
                
                if len(errors) > 10:
                    print(f"\n... 還有 {len(errors) - 10} 個錯誤")
            
        except Exception as e:
            print(f"讀取 JSON 檔案失敗: {e}")
    
    def view_csv_report(self, file_path: Path) -> None:
        """查看 CSV 格式的錯誤報告"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            print(f"\n=== CSV 錯誤報告: {file_path.name} ===")
            print(f"總錯誤數: {len(rows)}")
            
            if rows:
                # 統計錯誤類型
                error_types = {}
                collections = {}
                stages = {}
                
                for row in rows:
                    error_type = row.get('Error Type', 'N/A')
                    collection = row.get('Collection ID', 'N/A')
                    stage = row.get('Processing Stage', 'N/A')
                    
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                    collections[collection] = collections.get(collection, 0) + 1
                    stages[stage] = stages.get(stage, 0) + 1
                
                print("\n錯誤類型統計:")
                for error_type, count in error_types.items():
                    print(f"  {error_type}: {count}")
                
                print("\n受影響的 Collections:")
                for collection, count in collections.items():
                    print(f"  {collection}: {count}")
                
                print("\n處理階段統計:")
                for stage, count in stages.items():
                    print(f"  {stage}: {count}")
                
                # 顯示詳細錯誤
                print(f"\n詳細錯誤 (顯示前10個):")
                for i, row in enumerate(rows[:10], 1):
                    print(f"\n{i}. Collection: {row.get('Collection ID', 'N/A')}")
                    print(f"   RSS ID: {row.get('RSS ID', 'N/A')}")
                    print(f"   Title: {row.get('Title', 'N/A')}")
                    print(f"   Error Type: {row.get('Error Type', 'N/A')}")
                    print(f"   Stage: {row.get('Processing Stage', 'N/A')}")
                    print(f"   Message: {row.get('Error Message', 'N/A')}")
                    print(f"   Time: {row.get('Timestamp', 'N/A')}")
                
                if len(rows) > 10:
                    print(f"\n... 還有 {len(rows) - 10} 個錯誤")
            
        except Exception as e:
            print(f"讀取 CSV 檔案失敗: {e}")
    
    def view_report(self, file_path: Path) -> None:
        """查看錯誤報告"""
        if file_path.suffix.lower() == '.json':
            self.view_json_report(file_path)
        elif file_path.suffix.lower() == '.csv':
            self.view_csv_report(file_path)
        else:
            print(f"不支援的檔案格式: {file_path.suffix}")
    
    def search_errors(self, file_path: Path, search_term: str) -> None:
        """搜尋錯誤"""
        try:
            if file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                errors = data.get('errors', [])
            elif file_path.suffix.lower() == '.csv':
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    errors = list(reader)
            else:
                print(f"不支援的檔案格式: {file_path.suffix}")
                return
            
            print(f"\n=== 搜尋結果: '{search_term}' ===")
            
            matched_errors = []
            for error in errors:
                # 搜尋標題、錯誤訊息、Collection ID、RSS ID
                searchable_fields = [
                    str(error.get('title', '')),
                    str(error.get('error_message', '')),
                    str(error.get('collection_id', '')),
                    str(error.get('rss_id', '')),
                    str(error.get('Title', '')),
                    str(error.get('Error Message', '')),
                    str(error.get('Collection ID', '')),
                    str(error.get('RSS ID', ''))
                ]
                
                if any(search_term.lower() in field.lower() for field in searchable_fields):
                    matched_errors.append(error)
            
            print(f"找到 {len(matched_errors)} 個匹配的錯誤")
            
            for i, error in enumerate(matched_errors, 1):
                print(f"\n{i}. Collection: {error.get('collection_id', error.get('Collection ID', 'N/A'))}")
                print(f"   RSS ID: {error.get('rss_id', error.get('RSS ID', 'N/A'))}")
                print(f"   Title: {error.get('title', error.get('Title', 'N/A'))}")
                print(f"   Error Type: {error.get('error_type', error.get('Error Type', 'N/A'))}")
                print(f"   Message: {error.get('error_message', error.get('Error Message', 'N/A'))}")
            
        except Exception as e:
            print(f"搜尋錯誤失敗: {e}")
    
    def export_filtered_errors(self, file_path: Path, output_file: str, 
                              collection_id: str = None, error_type: str = None) -> None:
        """匯出過濾後的錯誤"""
        try:
            if file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                errors = data.get('errors', [])
            elif file_path.suffix.lower() == '.csv':
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    errors = list(reader)
            else:
                print(f"不支援的檔案格式: {file_path.suffix}")
                return
            
            # 過濾錯誤
            filtered_errors = []
            for error in errors:
                match = True
                
                if collection_id:
                    error_collection = error.get('collection_id', error.get('Collection ID', ''))
                    if collection_id.lower() not in error_collection.lower():
                        match = False
                
                if error_type and match:
                    error_type_field = error.get('error_type', error.get('Error Type', ''))
                    if error_type.lower() not in error_type_field.lower():
                        match = False
                
                if match:
                    filtered_errors.append(error)
            
            # 匯出到新檔案
            output_path = Path(output_file)
            if output_path.suffix.lower() == '.json':
                export_data = {
                    "summary": {
                        "total_errors": len(filtered_errors),
                        "filtered_from": len(errors),
                        "collection_filter": collection_id,
                        "error_type_filter": error_type,
                        "exported_at": datetime.now().isoformat()
                    },
                    "errors": filtered_errors
                }
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            elif output_path.suffix.lower() == '.csv':
                if filtered_errors:
                    fieldnames = filtered_errors[0].keys()
                    with open(output_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(filtered_errors)
            
            print(f"已匯出 {len(filtered_errors)} 個錯誤到: {output_file}")
            
        except Exception as e:
            print(f"匯出錯誤失敗: {e}")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='錯誤報告查看器')
    parser.add_argument('--list', action='store_true', help='列出所有錯誤報告檔案')
    parser.add_argument('--view', type=str, help='查看指定的錯誤報告檔案')
    parser.add_argument('--search', type=str, help='搜尋錯誤')
    parser.add_argument('--export', type=str, help='匯出過濾後的錯誤')
    parser.add_argument('--collection', type=str, help='過濾 Collection ID')
    parser.add_argument('--error-type', type=str, help='過濾錯誤類型')
    parser.add_argument('--output', type=str, help='輸出檔案名稱')
    
    args = parser.parse_args()
    
    viewer = ErrorReportViewer()
    
    if args.list:
        files = viewer.list_error_files()
        if files:
            print("可用的錯誤報告檔案:")
            for i, file_path in enumerate(files, 1):
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                print(f"{i:2d}. {file_path.name} ({mtime.strftime('%Y-%m-%d %H:%M:%S')})")
        else:
            print("沒有找到錯誤報告檔案")
    
    elif args.view:
        file_path = Path(args.view)
        if not file_path.is_absolute():
            file_path = viewer.error_logs_dir / file_path
        
        if file_path.exists():
            viewer.view_report(file_path)
        else:
            print(f"檔案不存在: {file_path}")
    
    elif args.search:
        files = viewer.list_error_files()
        if files:
            # 搜尋最新的檔案
            latest_file = files[0]
            viewer.search_errors(latest_file, args.search)
        else:
            print("沒有找到錯誤報告檔案")
    
    elif args.export:
        files = viewer.list_error_files()
        if files:
            latest_file = files[0]
            output_file = args.output or f"filtered_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            viewer.export_filtered_errors(latest_file, output_file, args.collection, args.error_type)
        else:
            print("沒有找到錯誤報告檔案")
    
    else:
        # 預設顯示最新檔案
        files = viewer.list_error_files()
        if files:
            print("顯示最新的錯誤報告:")
            viewer.view_report(files[0])
        else:
            print("沒有找到錯誤報告檔案")


if __name__ == "__main__":
    main() 