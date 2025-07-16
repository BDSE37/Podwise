import os
import json
import csv
from typing import Literal

class FileFormatDetector:
    """自動偵測檔案格式的工具類別。"""
    SUPPORTED_FORMATS = ("json", "csv", "txt")

    @staticmethod
    def detect_format(file_path: str) -> Literal["json", "csv", "txt"]:
        """根據副檔名與內容自動判斷格式。"""
        ext = os.path.splitext(file_path)[-1].lower()
        if ext == ".json":
            return "json"
        if ext == ".csv":
            return "csv"
        if ext == ".txt":
            return "txt"
        # 嘗試根據內容判斷
        with open(file_path, "r", encoding="utf-8") as f:
            head = f.read(2048)
            try:
                json.loads(head)
                return "json"
            except Exception:
                pass
            if "," in head and "\n" in head:
                return "csv"
        return "txt" 