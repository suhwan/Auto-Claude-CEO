"""
Team Sync Models
================

Data models for team synchronization points.

Sync Points are explicit synchronization points in team workflows:
- Barrier: Wait for all participants
- Wait: Wait for specific teams to complete
- Signal: Notification-only sync
- Gate: Approval-required checkpoint
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SyncType(Enum):
    """
    Synchronization types.

    Defines the type of synchronization behavior:
    - BARRIER: Wait for all participants to arrive
    - WAIT: Wait for specific teams to complete
    - SIGNAL: Notification-only (no blocking)
    - GATE: Requires explicit approval to proceed
    """
    BARRIER = "barrier"
    WAIT = "wait"
    SIGNAL = "signal"
    GATE = "gate"


class SyncStatus(Enum):
    """
    Synchronization status.

    Tracks the lifecycle of a sync point:
    - PENDING: Not yet started, no arrivals
    - WAITING: Some participants arrived, waiting for others
    - READY: All conditions met, can proceed
    - COMPLETED: Sync point completed
    - TIMEOUT: Timed out before completion
    - CANCELLED: Explicitly cancelled
    """
    PENDING = "pending"
    WAITING = "waiting"
    READY = "ready"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class SyncParticipant:
    """
    Sync point participant.

    Represents a team participating in a sync point.

    Attributes:
        team_id: Unique identifier for the team
        team_name: Human-readable team name
        role: Participation role ('required', 'optional', 'observer')
        arrived: Whether the team has arrived
        arrived_at: When the team arrived
        data: Data brought by the participant
    """
    team_id: str
    team_name: str
    role: str  # 'required', 'optional', 'observer'
    arrived: bool = False
    arrived_at: Optional[datetime] = None
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncCondition:
    """
    Sync point condition.

    Defines a condition that must be met for the sync point to be ready.

    Attributes:
        condition_type: Type of condition ('all_arrived', 'min_count',
                        'specific_teams', 'timeout')
        value: Condition value (varies by type)
        met: Whether the condition has been met
        met_at: When the condition was met
    """
    condition_type: str  # 'all_arrived', 'min_count', 'specific_teams', 'timeout'
    value: Any = None
    met: bool = False
    met_at: Optional[datetime] = None


@dataclass
class SyncPoint:
    """
    Synchronization point.

    Represents a point where teams must synchronize before proceeding.

    Attributes:
        id: Unique identifier
        name: Human-readable name
        sync_type: Type of synchronization
        status: Current status

        participants: List of participating teams
        required_count: Minimum required participants (0 = all)
        conditions: Conditions to be met

        phase: Associated phase number
        description: Detailed description
        context: Additional context data

        created_at: Creation timestamp
        timeout_at: Optional timeout timestamp
        completed_at: Completion timestamp

        result: Merged data from all participants
        on_ready_callback: Callback function name for ready state
        on_timeout_callback: Callback function name for timeout
    """
    id: str
    name: str
    sync_type: SyncType
    status: SyncStatus = SyncStatus.PENDING

    # Participants
    participants: List[SyncParticipant] = field(default_factory=list)
    required_count: int = 0  # 0 = all required participants

    # Conditions
    conditions: List[SyncCondition] = field(default_factory=list)

    # Context
    phase: int = 0
    description: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    timeout_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Result (merged participant data)
    result: Dict[str, Any] = field(default_factory=dict)

    # Callbacks
    on_ready_callback: Optional[str] = None
    on_timeout_callback: Optional[str] = None


@dataclass
class SyncEvent:
    """
    Sync point event.

    Records events in the sync point lifecycle for audit and debugging.

    Attributes:
        id: Unique event identifier
        sync_point_id: Associated sync point
        event_type: Type of event ('created', 'participant_arrived',
                    'condition_met', 'completed', 'timeout', 'cancelled')
        timestamp: When the event occurred
        team_id: Associated team (if applicable)
        details: Additional event details
    """
    id: str
    sync_point_id: str
    event_type: str  # 'created', 'participant_arrived', 'condition_met', 'completed', 'timeout', 'cancelled'
    timestamp: datetime
    team_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
