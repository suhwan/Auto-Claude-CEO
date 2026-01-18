"""
Leader Checkpoints
==================

Checkpoint system for LeaderContext that enables automatic state snapshots
at key execution points (subtask completion, errors, decisions, periodic).

This module provides:
- CheckpointTrigger: Enum defining when checkpoints are created
- CheckpointConfig: Configuration for checkpoint behavior
- Checkpoint: Data model for individual checkpoints
- CheckpointManager: Manages checkpoint lifecycle
- CheckpointSerializer: JSON serialization for checkpoints

Error Log System:
- ErrorSeverity: Error severity levels (WARNING, ERROR, CRITICAL)
- ErrorCategory: Error type classification
- ErrorContext: Error execution context
- ErrorLog: Error log entry with resolution tracking
- ErrorPattern: Repeated error pattern detection
- ErrorLogger: Error logging and pattern analysis
- ErrorLogSerializer: JSON serialization for error logs
"""

from .models import Checkpoint, CheckpointConfig, CheckpointTrigger
from .manager import CheckpointManager
from .serializer import CheckpointSerializer
from .error_models import (
    ErrorCategory,
    ErrorContext,
    ErrorLog,
    ErrorPattern,
    ErrorSeverity,
)
from .error_logger import ErrorLogger
from .error_serializer import ErrorLogSerializer

__all__ = [
    # Checkpoint system
    'CheckpointTrigger',
    'CheckpointConfig',
    'Checkpoint',
    'CheckpointManager',
    'CheckpointSerializer',
    # Error log system
    'ErrorSeverity',
    'ErrorCategory',
    'ErrorContext',
    'ErrorLog',
    'ErrorPattern',
    'ErrorLogger',
    'ErrorLogSerializer',
]
