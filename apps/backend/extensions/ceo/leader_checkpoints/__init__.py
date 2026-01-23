"""
Leader Checkpoints Module
=========================

Subtask-level checkpoint, error logging, and automatic review system.
Integrates with LeaderContext to automatically apply learning points.

This module provides:

Checkpoint System:
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

Review System:
- ReviewType: Review trigger types (SUBTASK, PHASE, ERROR_RESOLUTION, etc.)
- ReviewRating: Quality rating levels (EXCELLENT to POOR)
- ReviewCriteria: Ratings per review dimension
- LearningPoint: Extracted learning for LeaderContext
- Review: Complete review with ratings and learning points
- ReviewGenerator: Automatic review generation

Unified Service:
- LeaderCheckpointService: Integrates checkpoints, errors, and reviews
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
from .review_models import (
    LearningPoint,
    Review,
    ReviewCriteria,
    ReviewRating,
    ReviewType,
)
from .review_generator import ReviewGenerator
from .service import LeaderCheckpointService

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
    # Review system
    'ReviewType',
    'ReviewRating',
    'ReviewCriteria',
    'LearningPoint',
    'Review',
    'ReviewGenerator',
    # Unified service
    'LeaderCheckpointService',
]
