#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_cleaning/database/__init__.py

Database Module – 資料庫模組

提供 PostgreSQL 匯入與批次處理的接口。
"""

from .postgresql_inserter import PostgreSQLInserter

__all__ = [
    "PostgreSQLInserter",
]
