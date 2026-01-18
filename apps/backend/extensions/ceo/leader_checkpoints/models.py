"""
Leader Checkpoint Models
========================

Data models for the checkpoint system including trigger types,
configuration, and checkpoint data structures.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict


class CheckpointTrigger(Enum):
    """
    Checkpoint trigger types.

    Defines the conditions under which a checkpoint is created:
    - SUBTASK_COMPLETE: After a subtask finishes successfully
    - ERROR_OCCURRED: When an error is encountered
    - DECISION_MADE: When a significant decision is recorded
    - PERIODIC: After N operations (configurable interval)
    - EXPLICIT: Manual checkpoint request
    - PHASE_START: At the beginning of a phase
    - PHASE_END: At the completion of a phase
    """
    SUBTASK_COMPLETE = "subtask_complete"
    ERROR_OCCURRED = "error_occurred"
    DECISION_MADE = "decision_made"
    PERIODIC = "periodic"
    EXPLICIT = "explicit"
    PHASE_START = "phase_start"
    PHASE_END = "phase_end"


@dataclass
class CheckpointConfig:
    """
    Configuration for checkpoint behavior.

    Attributes:
        enabled: Whether checkpoint creation is enabled
        periodic_interval: Number of operations between periodic checkpoints
        on_subtask_complete: Create checkpoint after subtask completion
        on_error: Create checkpoint when an error occurs
        on_decision: Create checkpoint when a decision is made
        max_checkpoints: Maximum number of checkpoints to retain
        auto_cleanup: Automatically delete old checkpoints beyond max_checkpoints
    """
    enabled: bool = True
    periodic_interval: int = 5
    on_subtask_complete: bool = True
    on_error: bool = True
    on_decision: bool = True
    max_checkpoints: int = 50
    auto_cleanup: bool = True


@dataclass
class Checkpoint:
    """
    Represents a single checkpoint snapshot.

    Contains a full snapshot of LeaderContext at a specific point in time,
    along with metadata about what triggered the checkpoint.

    Attributes:
        id: Unique checkpoint identifier (e.g., "cp-a1b2c3d4")
        phase: Phase number when checkpoint was created
        trigger: What triggered this checkpoint
        timestamp: When the checkpoint was created
        context_snapshot: Serialized LeaderContext data
        trigger_details: Additional information about the trigger
            (e.g., subtask_id, error_message, decision_id)
        subtask_count: Cumulative subtask count at checkpoint time
        error_count: Cumulative error count at checkpoint time
        decision_count: Cumulative decision count at checkpoint time
    """
    id: str
    phase: int
    trigger: CheckpointTrigger
    timestamp: datetime
    context_snapshot: Dict[str, Any]
    trigger_details: Dict[str, Any] = field(default_factory=dict)
    subtask_count: int = 0
    error_count: int = 0
    decision_count: int = 0
