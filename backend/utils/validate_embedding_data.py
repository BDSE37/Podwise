#!/usr/bin/env python3
"""
驗證 embedding 資料完整性腳本
確保所有必要欄位都正確從 PostgreSQL 補足
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
import psycopg2
from datetime import datetime

class EmbeddingDataValidator:
    """Embedding 資料驗證器"""
    
    def __init__(self):
        """初始化驗證器"""
        self.pg_config = {
            'host': os.getenv('POSTGRES_HOST', '10.233.50.117'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'podcast'),
            'user': os.getenv('POSTGRES_USER', 'bdse37'),
            'password': os.getenv('POSTGRES_PASSWORD', '111111')
        }
        
        # 必要欄位定義
        self.required_fields = {
            'chunk_id': {'type': 'str', 'max_length': 64, 'required': True},
            'chunk_index': {'type': 'int', 'required': True},
            'episode_id': {'type': 'int', 'required': True},
            'podcast_id': {'type': 'int', 'required': True},
            'podcast_name': {'type': 'str', 'max_length': 255, 'required': True},
            'author': {'type': 'str', 'max_length': 255, 'required': True},
            'category': {'type': 'str', 'max_length': 64, 'required': True},
            'episode_title': {'type': 'str', 'max_length': 255, 'required': True},
            'duration': {'type': 'str', 'max_length': 255, 'required': True},
            'published_date': {'type': 'str', 'max_length': 64, 'required': True},
            'apple_rating': {'type': 'int', 'required': True},
            'chunk_text': {'type': 'str', 'max_length': 1024, 'required': True},
            'embedding': {'type': 'list', 'required': True},
            'language': {'type': 'str', 'max_length': 16, 'required': True},
            'created_at': {'type': 'str', 'required': True},
            'source_model': {'type': 'str', 'max_length': 64, 'required': True},
            'tags': {'type': 'str', 'max_length': 1024, 'required': True}
        }
    
    def validate_single_chunk(self, chunk: Dict) -> Dict[str, Any]:
        """驗證單個 chunk 的資料完整性"""
        validation_result = {
            'valid': True,
            'missing_fields': [],
            'invalid_fields': [],
            'warnings': []
        }
        
        # 檢查必要欄位
        for field_name, field_config in self.required_fields.items():
            if field_name not in chunk:
                validation_result['missing_fields'].append(field_name)
                validation_result['valid'] = False
                continue
            
            value = chunk[field_name]
            
            # 檢查欄位類型
            if field_config['type'] == 'int':
                if not isinstance(value, int):
                    validation_result['invalid_fields'].append(f"{field_name}: 應為 int，實際為 {type(value)}")
                    validation_result['valid'] = False
            elif field_config['type'] == 'str':
                if not isinstance(value, str):
                    validation_result['invalid_fields'].append(f"{field_name}: 應為 str，實際為 {type(value)}")
                    validation_result['valid'] = False
                elif 'max_length' in field_config and len(value) > field_config['max_length']:
                    validation_result['warnings'].append(f"{field_name}: 長度 {len(value)} 超過限制 {field_config['max_length']}")
            elif field_config['type'] == 'list':
                if not isinstance(value, list):
                    validation_result['invalid_fields'].append(f"{field_name}: 應為 list，實際為 {type(value)}")
                    validation_result['valid'] = False
                elif field_name == 'embedding' and len(value) != 1024:
                    validation_result['warnings'].append(f"{field_name}: embedding 維度 {len(value)} 不是 1024")
        
        # 檢查 PostgreSQL 資料完整性
        if chunk.get('episode_id', 0) > 0:
            # 有 episode_id，檢查是否為預設值
            if chunk.get('podcast_name') == '未知播客':
                validation_result['warnings'].append("有 episode_id 但 podcast_name 為預設值")
            if chunk.get('author') == '未知作者':
                validation_result['warnings'].append("有 episode_id 但 author 為預設值")
            if chunk.get('duration') == '未知時長':
                validation_result['warnings'].append("有 episode_id 但 duration 為預設值")
        else:
            # 沒有 episode_id，檢查是否為預設值
            if chunk.get('podcast_name') == '未知播客':
                validation_result['warnings'].append("沒有 episode_id 且 podcast_name 為預設值")
            if chunk.get('author') == '未知作者':
                validation_result['warnings'].append("沒有 episode_id 且 author 為預設值")
            if chunk.get('duration') == '未知時長':
                validation_result['warnings'].append("沒有 episode_id 且 duration 為預設值")
        
        return validation_result
    
    def validate_file(self, file_path: Path) -> Dict[str, Any]:
        """驗證單個檔案"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            chunks = data.get('chunks', [])
            if not chunks:
                return {
                    'file': str(file_path),
                    'valid': False,
                    'error': '沒有 chunks 資料'
                }
            
            validation_results = []
            for i, chunk in enumerate(chunks):
                chunk_validation = self.validate_single_chunk(chunk)
                chunk_validation['chunk_index'] = i
                validation_results.append(chunk_validation)
            
            # 統計結果
            valid_chunks = sum(1 for r in validation_results if r['valid'])
            total_chunks = len(validation_results)
            
            return {
                'file': str(file_path),
                'valid': valid_chunks == total_chunks,
                'total_chunks': total_chunks,
                'valid_chunks': valid_chunks,
                'invalid_chunks': total_chunks - valid_chunks,
                'chunk_validations': validation_results
            }
            
        except Exception as e:
            return {
                'file': str(file_path),
                'valid': False,
                'error': str(e)
            }
    
    def validate_all_files(self) -> Dict[str, Any]:
        """驗證所有檔案"""
        stage4_path = Path("backend/vector_pipeline/data/stage4_embedding_prep")
        
        if not stage4_path.exists():
            return {
                'valid': False,
                'error': f'目錄不存在: {stage4_path}'
            }
        
        all_files = list(stage4_path.rglob("*.json"))
        if not all_files:
            return {
                'valid': False,
                'error': '沒有找到任何檔案'
            }
        
        print(f"🔍 開始驗證 {len(all_files)} 個檔案...")
        
        validation_results = []
        for i, file_path in enumerate(all_files):
            print(f"驗證進度: {i+1}/{len(all_files)} - {file_path.name}")
            result = self.validate_file(file_path)
            validation_results.append(result)
        
        # 統計總結果
        valid_files = sum(1 for r in validation_results if r['valid'])
        total_files = len(validation_results)
        total_chunks = sum(r.get('total_chunks', 0) for r in validation_results)
        valid_chunks = sum(r.get('valid_chunks', 0) for r in validation_results)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_files': total_files,
            'valid_files': valid_files,
            'invalid_files': total_files - valid_files,
            'total_chunks': total_chunks,
            'valid_chunks': valid_chunks,
            'invalid_chunks': total_chunks - valid_chunks,
            'validation_results': validation_results,
            'summary': {
                'file_success_rate': valid_files / total_files * 100 if total_files > 0 else 0,
                'chunk_success_rate': valid_chunks / total_chunks * 100 if total_chunks > 0 else 0
            }
        }
    
    def print_validation_report(self, report: Dict[str, Any]):
        """列印驗證報告"""
        print("\n" + "="*80)
        print("📊 Embedding 資料完整性驗證報告")
        print("="*80)
        
        if 'error' in report:
            print(f"❌ 驗證失敗: {report['error']}")
            return
        
        print(f"📁 檔案統計:")
        print(f"   總檔案數: {report['total_files']}")
        print(f"   有效檔案: {report['valid_files']}")
        print(f"   無效檔案: {report['invalid_files']}")
        print(f"   檔案成功率: {report['summary']['file_success_rate']:.1f}%")
        
        print(f"\n🧩 Chunk 統計:")
        print(f"   總 Chunk 數: {report['total_chunks']}")
        print(f"   有效 Chunk: {report['valid_chunks']}")
        print(f"   無效 Chunk: {report['invalid_chunks']}")
        print(f"   Chunk 成功率: {report['summary']['chunk_success_rate']:.1f}%")
        
        # 顯示問題檔案
        invalid_files = [r for r in report['validation_results'] if not r['valid']]
        if invalid_files:
            print(f"\n❌ 問題檔案清單:")
            for file_result in invalid_files[:10]:  # 只顯示前10個
                print(f"   {file_result['file']}: {file_result.get('error', '資料不完整')}")
            if len(invalid_files) > 10:
                print(f"   ... 還有 {len(invalid_files) - 10} 個問題檔案")
        
        # 顯示警告
        warnings = []
        for file_result in report['validation_results']:
            for chunk_validation in file_result.get('chunk_validations', []):
                warnings.extend(chunk_validation.get('warnings', []))
        
        if warnings:
            print(f"\n⚠️ 警告清單 (前10個):")
            for warning in warnings[:10]:
                print(f"   {warning}")
            if len(warnings) > 10:
                print(f"   ... 還有 {len(warnings) - 10} 個警告")
        
        print("\n" + "="*80)

def main():
    """主函數"""
    validator = EmbeddingDataValidator()
    report = validator.validate_all_files()
    validator.print_validation_report(report)

if __name__ == "__main__":
    main() 