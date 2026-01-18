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
"""

from .models import Checkpoint, CheckpointConfig, CheckpointTrigger
from .manager import CheckpointManager
from .serializer import CheckpointSerializer

__all__ = [
    'CheckpointTrigger',
    'CheckpointConfig',
    'Checkpoint',
    'CheckpointManager',
    'CheckpointSerializer',
]
