"""
Checkpoint Serializer
=====================

JSON serialization and deserialization for Checkpoint objects.
"""

import json
from datetime import datetime
from typing import Any, Dict

from .models import Checkpoint, CheckpointTrigger


class CheckpointSerializer:
    """
    Serializer for Checkpoint objects.

    Provides static methods to convert Checkpoint objects to/from
    dictionaries and JSON strings.
    """

    @staticmethod
    def to_dict(checkpoint: Checkpoint) -> Dict[str, Any]:
        """
        Convert Checkpoint to dictionary.

        Args:
            checkpoint: Checkpoint instance to convert

        Returns:
            Dictionary representation of the checkpoint
        """
        return {
            "id": checkpoint.id,
            "phase": checkpoint.phase,
            "trigger": checkpoint.trigger.value,
            "timestamp": checkpoint.timestamp.isoformat(),
            "context_snapshot": checkpoint.context_snapshot,
            "trigger_details": checkpoint.trigger_details,
            "subtask_count": checkpoint.subtask_count,
            "error_count": checkpoint.error_count,
            "decision_count": checkpoint.decision_count,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Checkpoint:
        """
        Create Checkpoint from dictionary.

        Args:
            data: Dictionary containing checkpoint data

        Returns:
            Checkpoint instance
        """
        return Checkpoint(
            id=data["id"],
            phase=data["phase"],
            trigger=CheckpointTrigger(data["trigger"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            context_snapshot=data["context_snapshot"],
            trigger_details=data.get("trigger_details", {}),
            subtask_count=data.get("subtask_count", 0),
            error_count=data.get("error_count", 0),
            decision_count=data.get("decision_count", 0),
        )

    @staticmethod
    def to_json(checkpoint: Checkpoint, indent: int = 2) -> str:
        """
        Serialize Checkpoint to JSON string.

        Args:
            checkpoint: Checkpoint instance to serialize
            indent: JSON indentation level (default: 2)

        Returns:
            JSON string representation
        """
        return json.dumps(
            CheckpointSerializer.to_dict(checkpoint),
            indent=indent,
            ensure_ascii=False,
        )

    @staticmethod
    def from_json(json_str: str) -> Checkpoint:
        """
        Deserialize Checkpoint from JSON string.

        Args:
            json_str: JSON string to parse

        Returns:
            Checkpoint instance
        """
        data = json.loads(json_str)
        return CheckpointSerializer.from_dict(data)
