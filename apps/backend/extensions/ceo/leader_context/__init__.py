"""
Leader Context Module
=====================

Provides data models and utilities for storing and managing
leader agent execution context across sessions.

This module provides:
- Data models for goals, decisions, patterns, mistakes, files, dependencies, and risks
- Serialization and validation utilities
- File-based storage with automatic backup
- Context merging and diffing capabilities
- Initialization from PROJECT.md, STATE.md, or previous phases
- Query interface for efficient context retrieval
- Unified service API for context management
"""

from .models import (
    Decision,
    Dependency,
    FileMapping,
    Goal,
    LeaderContext,
    Mistake,
    Pattern,
    Risk,
)
from .serializer import LeaderContextSerializer
from .validator import ContextValidator
from .storage import ContextStorage
from .merger import ContextMerger
from .initializer import ContextInitializer
from .query import ContextQuery, QueryFilter
from .service import LeaderContextService

__all__ = [
    # Models
    "LeaderContext",
    "Goal",
    "Decision",
    "Pattern",
    "Mistake",
    "FileMapping",
    "Dependency",
    "Risk",
    # Serialization
    "LeaderContextSerializer",
    # Validation
    "ContextValidator",
    # Storage
    "ContextStorage",
    # Merger
    "ContextMerger",
    # Initializer
    "ContextInitializer",
    # Query
    "ContextQuery",
    "QueryFilter",
    # Service
    "LeaderContextService",
]
