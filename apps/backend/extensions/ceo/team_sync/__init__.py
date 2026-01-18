"""
Team Sync Module
================

Team synchronization system for coordinating work between teams.

This module provides:
- Sync Points: Explicit synchronization points in team workflows
- Sync Types: Barrier, Wait, Signal, Gate
- Event Logging: Audit trail for sync point lifecycle
- Shared Board: Visual dashboard for team coordination

Storage Locations:
- Sync Points: `.planning/team_sync/sync_points/`
- Shared Board: `.planning/team_sync/shared_board/`
"""

from .board_manager import SharedBoardManager
from .board_models import (
    BlockerType,
    Blocker,
    BoardTask,
    DependencyEdge,
    SharedBoard,
    TaskStatus,
    TeamLane,
)
from .board_serializer import BoardSerializer
from .models import (
    SyncCondition,
    SyncEvent,
    SyncParticipant,
    SyncPoint,
    SyncStatus,
    SyncType,
)
from .serializer import SyncPointSerializer
from .sync_manager import SyncPointManager

__all__ = [
    # Sync Point Enums
    "SyncType",
    "SyncStatus",
    # Sync Point Models
    "SyncParticipant",
    "SyncCondition",
    "SyncPoint",
    "SyncEvent",
    # Sync Point Manager
    "SyncPointManager",
    # Sync Point Serializer
    "SyncPointSerializer",
    # Shared Board Enums
    "TaskStatus",
    "BlockerType",
    # Shared Board Models
    "BoardTask",
    "Blocker",
    "TeamLane",
    "DependencyEdge",
    "SharedBoard",
    # Shared Board Manager
    "SharedBoardManager",
    # Shared Board Serializer
    "BoardSerializer",
]
