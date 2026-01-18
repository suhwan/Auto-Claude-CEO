"""
Error Log Serializer
====================

JSON serialization and deserialization for error log objects.
"""

import json
from datetime import datetime
from typing import Any, Dict

from .error_models import (
    ErrorCategory,
    ErrorContext,
    ErrorLog,
    ErrorPattern,
    ErrorSeverity,
)


class ErrorLogSerializer:
    """
    Serializer for error log objects.

    Provides static methods to convert ErrorLog, ErrorPattern, and
    ErrorContext objects to/from dictionaries and JSON strings.
    """

    @staticmethod
    def context_to_dict(context: ErrorContext) -> Dict[str, Any]:
        """
        Convert ErrorContext to dictionary.

        Args:
            context: ErrorContext instance to convert

        Returns:
            Dictionary representation of the context
        """
        return {
            "file_path": context.file_path,
            "function_name": context.function_name,
            "line_number": context.line_number,
            "subtask_id": context.subtask_id,
            "agent_type": context.agent_type,
            "command": context.command,
            "input_data": context.input_data,
        }

    @staticmethod
    def context_from_dict(data: Dict[str, Any]) -> ErrorContext:
        """
        Create ErrorContext from dictionary.

        Args:
            data: Dictionary containing context data

        Returns:
            ErrorContext instance
        """
        return ErrorContext(
            file_path=data.get("file_path"),
            function_name=data.get("function_name"),
            line_number=data.get("line_number"),
            subtask_id=data.get("subtask_id"),
            agent_type=data.get("agent_type"),
            command=data.get("command"),
            input_data=data.get("input_data"),
        )

    @staticmethod
    def error_to_dict(error: ErrorLog) -> Dict[str, Any]:
        """
        Convert ErrorLog to dictionary.

        Args:
            error: ErrorLog instance to convert

        Returns:
            Dictionary representation of the error log
        """
        return {
            "id": error.id,
            "phase": error.phase,
            "timestamp": error.timestamp.isoformat(),
            "severity": error.severity.value,
            "category": error.category.value,
            "message": error.message,
            "stack_trace": error.stack_trace,
            "context": ErrorLogSerializer.context_to_dict(error.context),
            "resolved": error.resolved,
            "resolution": error.resolution,
            "resolved_at": error.resolved_at.isoformat() if error.resolved_at else None,
            "error_hash": error.error_hash,
            "occurrence_count": error.occurrence_count,
            "first_seen": error.first_seen.isoformat() if error.first_seen else None,
            "last_seen": error.last_seen.isoformat() if error.last_seen else None,
            "checkpoint_id": error.checkpoint_id,
            "related_error_ids": error.related_error_ids,
        }

    @staticmethod
    def error_from_dict(data: Dict[str, Any]) -> ErrorLog:
        """
        Create ErrorLog from dictionary.

        Args:
            data: Dictionary containing error log data

        Returns:
            ErrorLog instance
        """
        return ErrorLog(
            id=data["id"],
            phase=data["phase"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            severity=ErrorSeverity(data["severity"]),
            category=ErrorCategory(data["category"]),
            message=data["message"],
            stack_trace=data.get("stack_trace"),
            context=ErrorLogSerializer.context_from_dict(data.get("context", {})),
            resolved=data.get("resolved", False),
            resolution=data.get("resolution"),
            resolved_at=(
                datetime.fromisoformat(data["resolved_at"])
                if data.get("resolved_at")
                else None
            ),
            error_hash=data.get("error_hash"),
            occurrence_count=data.get("occurrence_count", 1),
            first_seen=(
                datetime.fromisoformat(data["first_seen"])
                if data.get("first_seen")
                else None
            ),
            last_seen=(
                datetime.fromisoformat(data["last_seen"])
                if data.get("last_seen")
                else None
            ),
            checkpoint_id=data.get("checkpoint_id"),
            related_error_ids=data.get("related_error_ids", []),
        )

    @staticmethod
    def pattern_to_dict(pattern: ErrorPattern) -> Dict[str, Any]:
        """
        Convert ErrorPattern to dictionary.

        Args:
            pattern: ErrorPattern instance to convert

        Returns:
            Dictionary representation of the pattern
        """
        return {
            "id": pattern.id,
            "error_hash": pattern.error_hash,
            "category": pattern.category.value,
            "message_pattern": pattern.message_pattern,
            "occurrence_count": pattern.occurrence_count,
            "first_seen": pattern.first_seen.isoformat(),
            "last_seen": pattern.last_seen.isoformat(),
            "example_error_ids": pattern.example_error_ids,
            "suggested_fix": pattern.suggested_fix,
            "auto_resolved": pattern.auto_resolved,
        }

    @staticmethod
    def pattern_from_dict(data: Dict[str, Any]) -> ErrorPattern:
        """
        Create ErrorPattern from dictionary.

        Args:
            data: Dictionary containing pattern data

        Returns:
            ErrorPattern instance
        """
        return ErrorPattern(
            id=data["id"],
            error_hash=data["error_hash"],
            category=ErrorCategory(data["category"]),
            message_pattern=data["message_pattern"],
            occurrence_count=data["occurrence_count"],
            first_seen=datetime.fromisoformat(data["first_seen"]),
            last_seen=datetime.fromisoformat(data["last_seen"]),
            example_error_ids=data.get("example_error_ids", []),
            suggested_fix=data.get("suggested_fix"),
            auto_resolved=data.get("auto_resolved", False),
        )

    @staticmethod
    def error_to_json(error: ErrorLog, indent: int = 2) -> str:
        """
        Serialize ErrorLog to JSON string.

        Args:
            error: ErrorLog instance to serialize
            indent: JSON indentation level (default: 2)

        Returns:
            JSON string representation
        """
        return json.dumps(
            ErrorLogSerializer.error_to_dict(error),
            indent=indent,
            ensure_ascii=False,
        )

    @staticmethod
    def error_from_json(json_str: str) -> ErrorLog:
        """
        Deserialize ErrorLog from JSON string.

        Args:
            json_str: JSON string to parse

        Returns:
            ErrorLog instance
        """
        data = json.loads(json_str)
        return ErrorLogSerializer.error_from_dict(data)

    @staticmethod
    def pattern_to_json(pattern: ErrorPattern, indent: int = 2) -> str:
        """
        Serialize ErrorPattern to JSON string.

        Args:
            pattern: ErrorPattern instance to serialize
            indent: JSON indentation level (default: 2)

        Returns:
            JSON string representation
        """
        return json.dumps(
            ErrorLogSerializer.pattern_to_dict(pattern),
            indent=indent,
            ensure_ascii=False,
        )

    @staticmethod
    def pattern_from_json(json_str: str) -> ErrorPattern:
        """
        Deserialize ErrorPattern from JSON string.

        Args:
            json_str: JSON string to parse

        Returns:
            ErrorPattern instance
        """
        data = json.loads(json_str)
        return ErrorLogSerializer.pattern_from_dict(data)
