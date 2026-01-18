"""
Team Sync Module
================

Team synchronization system for coordinating work between teams.

This module provides:
- Sync Points: Explicit synchronization points in team workflows
- Sync Types: Barrier, Wait, Signal, Gate
- Event Logging: Audit trail for sync point lifecycle

Storage Location: `.planning/team_sync/sync_points/`
"""

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
    # Enums
    "SyncType",
    "SyncStatus",
    # Models
    "SyncParticipant",
    "SyncCondition",
    "SyncPoint",
    "SyncEvent",
    # Manager
    "SyncPointManager",
    # Serializer
    "SyncPointSerializer",
]
