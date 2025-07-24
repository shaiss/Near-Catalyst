# database/__init__.py
"""
Database package for NEAR Partnership Analysis

Provides database management functionality including:
- SQLite schema management
- Data persistence and caching
- Export and reporting capabilities
- Concurrent access handling
"""

from .database_manager import DatabaseManager

__all__ = ['DatabaseManager'] 