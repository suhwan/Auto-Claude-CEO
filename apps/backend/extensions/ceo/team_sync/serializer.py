"""
Sync Point Serializer
=====================

Provides JSON serialization and deserialization for SyncPoint
and related models.
"""

import json
from datetime import datetime
from typing import Any, Dict, List

from .models import (
    SyncCondition,
    SyncEvent,
    SyncParticipant,
    SyncPoint,
    SyncStatus,
    SyncType,
)


class SyncPointSerializer:
    """
    Serializer for SyncPoint and related models.

    Provides static methods to convert SyncPoint objects to/from
    dictionaries and JSON strings. Handles datetime conversion
    using ISO 8601 format.
    """

    # ==========================================================================
    # DateTime Helpers
    # ==========================================================================

    @staticmethod
    def _datetime_to_str(dt: datetime) -> str:
        """Convert datetime to ISO format string."""
        return dt.isoformat()

    @staticmethod
    def _str_to_datetime(dt_str: str) -> datetime:
        """Convert ISO format string to datetime."""
        return datetime.fromisoformat(dt_str)

    # ==========================================================================
    # Participant Serialization
    # ==========================================================================

    @staticmethod
    def participant_to_dict(p: SyncParticipant) -> Dict[str, Any]:
        """
        Convert SyncParticipant to dictionary.

        Args:
            p: SyncParticipant instance

        Returns:
            Dictionary representation
        """
        return {
            "team_id": p.team_id,
            "team_name": p.team_name,
            "role": p.role,
            "arrived": p.arrived,
            "arrived_at": (
                SyncPointSerializer._datetime_to_str(p.arrived_at)
                if p.arrived_at
                else None
            ),
            "data": p.data,
        }

    @staticmethod
    def participant_from_dict(data: Dict[str, Any]) -> SyncParticipant:
        """
        Create SyncParticipant from dictionary.

        Args:
            data: Dictionary with participant data

        Returns:
            SyncParticipant instance
        """
        return SyncParticipant(
            team_id=data["team_id"],
            team_name=data["team_name"],
            role=data["role"],
            arrived=data.get("arrived", False),
            arrived_at=(
                SyncPointSerializer._str_to_datetime(data["arrived_at"])
                if data.get("arrived_at")
                else None
            ),
            data=data.get("data", {}),
        )

    # ==========================================================================
    # Condition Serialization
    # ==========================================================================

    @staticmethod
    def condition_to_dict(c: SyncCondition) -> Dict[str, Any]:
        """
        Convert SyncCondition to dictionary.

        Args:
            c: SyncCondition instance

        Returns:
            Dictionary representation
        """
        return {
            "condition_type": c.condition_type,
            "value": c.value,
            "met": c.met,
            "met_at": (
                SyncPointSerializer._datetime_to_str(c.met_at)
                if c.met_at
                else None
            ),
        }

    @staticmethod
    def condition_from_dict(data: Dict[str, Any]) -> SyncCondition:
        """
        Create SyncCondition from dictionary.

        Args:
            data: Dictionary with condition data

        Returns:
            SyncCondition instance
        """
        return SyncCondition(
            condition_type=data["condition_type"],
            value=data.get("value"),
            met=data.get("met", False),
            met_at=(
                SyncPointSerializer._str_to_datetime(data["met_at"])
                if data.get("met_at")
                else None
            ),
        )

    # ==========================================================================
    # SyncPoint Serialization
    # ==========================================================================

    @staticmethod
    def sync_point_to_dict(sp: SyncPoint) -> Dict[str, Any]:
        """
        Convert SyncPoint to dictionary.

        Args:
            sp: SyncPoint instance

        Returns:
            Dictionary representation
        """
        return {
            "id": sp.id,
            "name": sp.name,
            "sync_type": sp.sync_type.value,
            "status": sp.status.value,
            # Participants
            "participants": [
                SyncPointSerializer.participant_to_dict(p)
                for p in sp.participants
            ],
            "required_count": sp.required_count,
            # Conditions
            "conditions": [
                SyncPointSerializer.condition_to_dict(c)
                for c in sp.conditions
            ],
            # Context
            "phase": sp.phase,
            "description": sp.description,
            "context": sp.context,
            # Timestamps
            "created_at": SyncPointSerializer._datetime_to_str(sp.created_at),
            "timeout_at": (
                SyncPointSerializer._datetime_to_str(sp.timeout_at)
                if sp.timeout_at
                else None
            ),
            "completed_at": (
                SyncPointSerializer._datetime_to_str(sp.completed_at)
                if sp.completed_at
                else None
            ),
            # Result
            "result": sp.result,
            # Callbacks
            "on_ready_callback": sp.on_ready_callback,
            "on_timeout_callback": sp.on_timeout_callback,
        }

    @staticmethod
    def sync_point_from_dict(data: Dict[str, Any]) -> SyncPoint:
        """
        Create SyncPoint from dictionary.

        Args:
            data: Dictionary with sync point data

        Returns:
            SyncPoint instance
        """
        return SyncPoint(
            id=data["id"],
            name=data["name"],
            sync_type=SyncType(data["sync_type"]),
            status=SyncStatus(data["status"]),
            # Participants
            participants=[
                SyncPointSerializer.participant_from_dict(p)
                for p in data.get("participants", [])
            ],
            required_count=data.get("required_count", 0),
            # Conditions
            conditions=[
                SyncPointSerializer.condition_from_dict(c)
                for c in data.get("conditions", [])
            ],
            # Context
            phase=data.get("phase", 0),
            description=data.get("description", ""),
            context=data.get("context", {}),
            # Timestamps
            created_at=SyncPointSerializer._str_to_datetime(data["created_at"]),
            timeout_at=(
                SyncPointSerializer._str_to_datetime(data["timeout_at"])
                if data.get("timeout_at")
                else None
            ),
            completed_at=(
                SyncPointSerializer._str_to_datetime(data["completed_at"])
                if data.get("completed_at")
                else None
            ),
            # Result
            result=data.get("result", {}),
            # Callbacks
            on_ready_callback=data.get("on_ready_callback"),
            on_timeout_callback=data.get("on_timeout_callback"),
        )

    # ==========================================================================
    # SyncEvent Serialization
    # ==========================================================================

    @staticmethod
    def event_to_dict(e: SyncEvent) -> Dict[str, Any]:
        """
        Convert SyncEvent to dictionary.

        Args:
            e: SyncEvent instance

        Returns:
            Dictionary representation
        """
        return {
            "id": e.id,
            "sync_point_id": e.sync_point_id,
            "event_type": e.event_type,
            "timestamp": SyncPointSerializer._datetime_to_str(e.timestamp),
            "team_id": e.team_id,
            "details": e.details,
        }

    @staticmethod
    def event_from_dict(data: Dict[str, Any]) -> SyncEvent:
        """
        Create SyncEvent from dictionary.

        Args:
            data: Dictionary with event data

        Returns:
            SyncEvent instance
        """
        return SyncEvent(
            id=data["id"],
            sync_point_id=data["sync_point_id"],
            event_type=data["event_type"],
            timestamp=SyncPointSerializer._str_to_datetime(data["timestamp"]),
            team_id=data.get("team_id"),
            details=data.get("details", {}),
        )

    # ==========================================================================
    # JSON Serialization
    # ==========================================================================

    @staticmethod
    def to_json(sp: SyncPoint, indent: int = 2) -> str:
        """
        Serialize SyncPoint to JSON string.

        Args:
            sp: SyncPoint instance
            indent: JSON indentation level (default: 2)

        Returns:
            JSON string representation
        """
        return json.dumps(
            SyncPointSerializer.sync_point_to_dict(sp),
            indent=indent,
            ensure_ascii=False,
        )

    @staticmethod
    def from_json(json_str: str) -> SyncPoint:
        """
        Deserialize SyncPoint from JSON string.

        Args:
            json_str: JSON string to parse

        Returns:
            SyncPoint instance
        """
        data = json.loads(json_str)
        return SyncPointSerializer.sync_point_from_dict(data)

    # ==========================================================================
    # Batch Serialization
    # ==========================================================================

    @staticmethod
    def sync_points_to_dict(sync_points: List[SyncPoint]) -> List[Dict[str, Any]]:
        """
        Convert list of SyncPoints to list of dictionaries.

        Args:
            sync_points: List of SyncPoint instances

        Returns:
            List of dictionary representations
        """
        return [SyncPointSerializer.sync_point_to_dict(sp) for sp in sync_points]

    @staticmethod
    def sync_points_from_dict(data_list: List[Dict[str, Any]]) -> List[SyncPoint]:
        """
        Create list of SyncPoints from list of dictionaries.

        Args:
            data_list: List of dictionaries

        Returns:
            List of SyncPoint instances
        """
        return [SyncPointSerializer.sync_point_from_dict(d) for d in data_list]

    @staticmethod
    def events_to_dict(events: List[SyncEvent]) -> List[Dict[str, Any]]:
        """
        Convert list of SyncEvents to list of dictionaries.

        Args:
            events: List of SyncEvent instances

        Returns:
            List of dictionary representations
        """
        return [SyncPointSerializer.event_to_dict(e) for e in events]

    @staticmethod
    def events_from_dict(data_list: List[Dict[str, Any]]) -> List[SyncEvent]:
        """
        Create list of SyncEvents from list of dictionaries.

        Args:
            data_list: List of dictionaries

        Returns:
            List of SyncEvent instances
        """
        return [SyncPointSerializer.event_from_dict(d) for d in data_list]
