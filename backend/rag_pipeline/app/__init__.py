"""
RAG Pipeline FastAPI 應用程式模組
提供 REST API 介面
"""

from .main_crewai import app, ApplicationManager, get_app_manager

__all__ = [
    "app",
    "ApplicationManager", 
    "get_app_manager"
] 