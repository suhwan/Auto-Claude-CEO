"""
Team Sync Module
================

Team synchronization system for coordinating work between teams.

This module provides:
- Sync Points: Explicit synchronization points in team workflows
- Sync Types: Barrier, Wait, Signal, Gate
- Event Logging: Audit trail for sync point lifecycle
- Shared Board: Visual dashboard for team coordination
- Leader Meeting: Automated meeting management

Storage Locations:
- Sync Points: `.planning/team_sync/sync_points/`
- Shared Board: `.planning/team_sync/shared_board/`
- Meetings: `.planning/team_sync/meetings/`

Key Features:
- Sync Points: Team synchronization barriers and signals
- Shared Board: Task tracking and blocker management
- Leader Meeting: Automatic agenda and action item tracking
"""

# Sync Points
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

# Shared Board
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
from .board_manager import SharedBoardManager

# Leader Meeting
from .meeting_models import (
    ActionItem,
    AgendaItem,
    Meeting,
    MeetingMinutes,
    MeetingParticipant,
    MeetingSchedule,
    MeetingStatus,
    MeetingType,
)
from .meeting_manager import MeetingManager

# Service
from .service import TeamSyncService

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
    # Leader Meeting Enums
    "MeetingType",
    "MeetingStatus",
    # Leader Meeting Models
    "AgendaItem",
    "ActionItem",
    "MeetingParticipant",
    "MeetingMinutes",
    "Meeting",
    "MeetingSchedule",
    # Leader Meeting Manager
    "MeetingManager",
    # Service
    "TeamSyncService",
]
