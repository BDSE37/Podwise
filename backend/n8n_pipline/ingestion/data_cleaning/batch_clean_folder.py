#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch clean JSON files under specified folder:
- Removes emoji/unwanted characters
- Ensures uniform JSON list output
- Skips non-JSON files based on extension to avoid decoding errors
"""
import os
import argparse
import json
from typing import Any, Dict, List

from data_cleaning.core.unified_cleaner import UnifiedCleaner


def clean_record(record: Dict[str, Any], cleaner: UnifiedCleaner) -> Dict[str, Any]:
    """Clean a single JSON record, including comments list."""
    cleaned: Dict[str, Any] = {}
    for key, value in record.items():
        lk = key.lower()
        # Clean comment(s) fields specially: remove emoji from each entry
        if lk in ('comment', 'comments'):
            if isinstance(value, list):
                cleaned[key] = [cleaner.clean_text(str(v)) for v in value]
            elif isinstance(value, str):
                cleaned[key] = cleaner.clean_text(value)
            else:
                cleaned[key] = value
            continue

        # Clean all string fields
        if isinstance(value, str):
            cleaned[key] = cleaner.clean_text(value)

        # Clean lists of strings
        elif isinstance(value, list):
            new_list: List[Any] = []
            for v in value:
                if isinstance(v, str):
                    new_list.append(cleaner.clean_text(v))
                else:
                    new_list.append(v)
            cleaned[key] = new_list

        # Preserve other types
        else:
            cleaned[key] = value

    return cleaned


def main():
    parser = argparse.ArgumentParser(
        description="Batch clean JSON files by removing emoji, preserving list format"
    )
    parser.add_argument(
        "--input-folder", "-i", default="/data",
        help="Input folder containing raw JSON files"
    )
    parser.add_argument(
        "--output-folder", "-o", default="/data/cleaned",
        help="Output folder for cleaned JSON files"
    )
    args = parser.parse_args()

    cleaner = UnifiedCleaner()
    cleaned_files: List[str] = []

    # Walk through input directory
    for root, _, files in os.walk(args.input_folder):
        rel = os.path.relpath(root, args.input_folder)
        target_dir = args.output_folder if rel in ('.', '') else os.path.join(args.output_folder, rel)
        os.makedirs(target_dir, exist_ok=True)

        for fn in files:
            # Process only JSON files
            if not fn.lower().endswith('.json'):
                continue
            src_path = os.path.join(root, fn)
            print(f"Cleaning {src_path}...")
            try:
                with open(src_path, 'r', encoding='utf-8') as rf:
                    data = json.load(rf)
            except Exception as e:
                print(f"Failed to load JSON {src_path}: {e}")
                continue

            records = data if isinstance(data, list) else [data]
            cleaned_list = [clean_record(rec, cleaner) for rec in records]

            out_path = os.path.join(target_dir, fn)
            try:
                with open(out_path, 'w', encoding='utf-8') as wf:
                    json.dump(cleaned_list, wf, ensure_ascii=False, indent=2)
                cleaned_files.append(out_path)
                print(f"  -> Saved cleaned file: {out_path}")
            except Exception as e:
                print(f"Error writing cleaned file {out_path}: {e}")

    print(f"Done. Total cleaned JSON files: {len(cleaned_files)}")

if __name__ == '__main__':
    main()
