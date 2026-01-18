"""
Board Serializer
================

Provides JSON serialization and deserialization for SharedBoard
and related models.
"""

import json
from datetime import datetime
from typing import Any, Dict, List

from .board_models import (
    BlockerType,
    Blocker,
    BoardTask,
    DependencyEdge,
    SharedBoard,
    TaskStatus,
    TeamLane,
)


class BoardSerializer:
    """
    Serializer for SharedBoard and related models.

    Provides static methods to convert SharedBoard objects to/from
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
    # BoardTask Serialization
    # ==========================================================================

    @staticmethod
    def task_to_dict(task: BoardTask) -> Dict[str, Any]:
        """
        Convert BoardTask to dictionary.

        Args:
            task: BoardTask instance

        Returns:
            Dictionary representation
        """
        return {
            "id": task.id,
            "team_id": task.team_id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "progress": task.progress,
            # Dependencies
            "depends_on": task.depends_on,
            "blocking": task.blocking,
            # Assignment
            "assignee": task.assignee,
            "priority": task.priority,
            # Timestamps
            "created_at": BoardSerializer._datetime_to_str(task.created_at),
            "started_at": (
                BoardSerializer._datetime_to_str(task.started_at)
                if task.started_at
                else None
            ),
            "completed_at": (
                BoardSerializer._datetime_to_str(task.completed_at)
                if task.completed_at
                else None
            ),
            # Metadata
            "metadata": task.metadata,
        }

    @staticmethod
    def task_from_dict(data: Dict[str, Any]) -> BoardTask:
        """
        Create BoardTask from dictionary.

        Args:
            data: Dictionary with task data

        Returns:
            BoardTask instance
        """
        return BoardTask(
            id=data["id"],
            team_id=data["team_id"],
            title=data["title"],
            description=data.get("description", ""),
            status=TaskStatus(data["status"]),
            progress=data.get("progress", 0),
            # Dependencies
            depends_on=data.get("depends_on", []),
            blocking=data.get("blocking", []),
            # Assignment
            assignee=data.get("assignee"),
            priority=data.get("priority", 3),
            # Timestamps
            created_at=BoardSerializer._str_to_datetime(data["created_at"]),
            started_at=(
                BoardSerializer._str_to_datetime(data["started_at"])
                if data.get("started_at")
                else None
            ),
            completed_at=(
                BoardSerializer._str_to_datetime(data["completed_at"])
                if data.get("completed_at")
                else None
            ),
            # Metadata
            metadata=data.get("metadata", {}),
        )

    # ==========================================================================
    # Blocker Serialization
    # ==========================================================================

    @staticmethod
    def blocker_to_dict(blocker: Blocker) -> Dict[str, Any]:
        """
        Convert Blocker to dictionary.

        Args:
            blocker: Blocker instance

        Returns:
            Dictionary representation
        """
        return {
            "id": blocker.id,
            "team_id": blocker.team_id,
            "blocker_type": blocker.blocker_type.value,
            "title": blocker.title,
            "description": blocker.description,
            # Related items
            "related_task_id": blocker.related_task_id,
            "blocking_team_id": blocker.blocking_team_id,
            # Resolution status
            "resolved": blocker.resolved,
            "resolved_at": (
                BoardSerializer._datetime_to_str(blocker.resolved_at)
                if blocker.resolved_at
                else None
            ),
            "resolution": blocker.resolution,
            # Timestamps and priority
            "created_at": BoardSerializer._datetime_to_str(blocker.created_at),
            "priority": blocker.priority,
        }

    @staticmethod
    def blocker_from_dict(data: Dict[str, Any]) -> Blocker:
        """
        Create Blocker from dictionary.

        Args:
            data: Dictionary with blocker data

        Returns:
            Blocker instance
        """
        return Blocker(
            id=data["id"],
            team_id=data["team_id"],
            blocker_type=BlockerType(data["blocker_type"]),
            title=data["title"],
            description=data.get("description", ""),
            # Related items
            related_task_id=data.get("related_task_id"),
            blocking_team_id=data.get("blocking_team_id"),
            # Resolution status
            resolved=data.get("resolved", False),
            resolved_at=(
                BoardSerializer._str_to_datetime(data["resolved_at"])
                if data.get("resolved_at")
                else None
            ),
            resolution=data.get("resolution"),
            # Timestamps and priority
            created_at=BoardSerializer._str_to_datetime(data["created_at"]),
            priority=data.get("priority", "medium"),
        )

    # ==========================================================================
    # TeamLane Serialization
    # ==========================================================================

    @staticmethod
    def lane_to_dict(lane: TeamLane) -> Dict[str, Any]:
        """
        Convert TeamLane to dictionary.

        Args:
            lane: TeamLane instance

        Returns:
            Dictionary representation
        """
        return {
            "team_id": lane.team_id,
            "team_name": lane.team_name,
            "display_order": lane.display_order,
            # Tasks and blockers
            "tasks": [BoardSerializer.task_to_dict(t) for t in lane.tasks],
            "blockers": [BoardSerializer.blocker_to_dict(b) for b in lane.blockers],
            # Statistics
            "total_tasks": lane.total_tasks,
            "completed_tasks": lane.completed_tasks,
            "in_progress_tasks": lane.in_progress_tasks,
            "blocked_tasks": lane.blocked_tasks,
            # Current state
            "current_focus": lane.current_focus,
            "last_updated": BoardSerializer._datetime_to_str(lane.last_updated),
        }

    @staticmethod
    def lane_from_dict(data: Dict[str, Any]) -> TeamLane:
        """
        Create TeamLane from dictionary.

        Args:
            data: Dictionary with lane data

        Returns:
            TeamLane instance
        """
        return TeamLane(
            team_id=data["team_id"],
            team_name=data["team_name"],
            display_order=data.get("display_order", 0),
            # Tasks and blockers
            tasks=[BoardSerializer.task_from_dict(t) for t in data.get("tasks", [])],
            blockers=[
                BoardSerializer.blocker_from_dict(b) for b in data.get("blockers", [])
            ],
            # Statistics
            total_tasks=data.get("total_tasks", 0),
            completed_tasks=data.get("completed_tasks", 0),
            in_progress_tasks=data.get("in_progress_tasks", 0),
            blocked_tasks=data.get("blocked_tasks", 0),
            # Current state
            current_focus=data.get("current_focus"),
            last_updated=BoardSerializer._str_to_datetime(data["last_updated"]),
        )

    # ==========================================================================
    # DependencyEdge Serialization
    # ==========================================================================

    @staticmethod
    def dependency_to_dict(dep: DependencyEdge) -> Dict[str, Any]:
        """
        Convert DependencyEdge to dictionary.

        Args:
            dep: DependencyEdge instance

        Returns:
            Dictionary representation
        """
        return {
            "from_team": dep.from_team,
            "from_task": dep.from_task,
            "to_team": dep.to_team,
            "to_task": dep.to_task,
            "status": dep.status,
        }

    @staticmethod
    def dependency_from_dict(data: Dict[str, Any]) -> DependencyEdge:
        """
        Create DependencyEdge from dictionary.

        Args:
            data: Dictionary with dependency data

        Returns:
            DependencyEdge instance
        """
        return DependencyEdge(
            from_team=data["from_team"],
            from_task=data["from_task"],
            to_team=data["to_team"],
            to_task=data["to_task"],
            status=data.get("status", "pending"),
        )

    # ==========================================================================
    # SharedBoard Serialization
    # ==========================================================================

    @staticmethod
    def board_to_dict(board: SharedBoard) -> Dict[str, Any]:
        """
        Convert SharedBoard to dictionary.

        Args:
            board: SharedBoard instance

        Returns:
            Dictionary representation
        """
        return {
            "id": board.id,
            "name": board.name,
            "phase": board.phase,
            # Team lanes
            "lanes": [BoardSerializer.lane_to_dict(l) for l in board.lanes],
            # Dependency graph
            "dependencies": [
                BoardSerializer.dependency_to_dict(d) for d in board.dependencies
            ],
            # Sync point integration
            "active_sync_points": board.active_sync_points,
            # Timestamps
            "created_at": BoardSerializer._datetime_to_str(board.created_at),
            "last_updated": BoardSerializer._datetime_to_str(board.last_updated),
            # Configuration
            "auto_sync": board.auto_sync,
            "update_interval_seconds": board.update_interval_seconds,
        }

    @staticmethod
    def board_from_dict(data: Dict[str, Any]) -> SharedBoard:
        """
        Create SharedBoard from dictionary.

        Args:
            data: Dictionary with board data

        Returns:
            SharedBoard instance
        """
        return SharedBoard(
            id=data["id"],
            name=data["name"],
            phase=data["phase"],
            # Team lanes
            lanes=[BoardSerializer.lane_from_dict(l) for l in data.get("lanes", [])],
            # Dependency graph
            dependencies=[
                BoardSerializer.dependency_from_dict(d)
                for d in data.get("dependencies", [])
            ],
            # Sync point integration
            active_sync_points=data.get("active_sync_points", []),
            # Timestamps
            created_at=BoardSerializer._str_to_datetime(data["created_at"]),
            last_updated=BoardSerializer._str_to_datetime(data["last_updated"]),
            # Configuration
            auto_sync=data.get("auto_sync", True),
            update_interval_seconds=data.get("update_interval_seconds", 60),
        )

    # ==========================================================================
    # JSON Serialization
    # ==========================================================================

    @staticmethod
    def to_json(board: SharedBoard, indent: int = 2) -> str:
        """
        Serialize SharedBoard to JSON string.

        Args:
            board: SharedBoard instance
            indent: JSON indentation level (default: 2)

        Returns:
            JSON string representation
        """
        return json.dumps(
            BoardSerializer.board_to_dict(board),
            indent=indent,
            ensure_ascii=False,
        )

    @staticmethod
    def from_json(json_str: str) -> SharedBoard:
        """
        Deserialize SharedBoard from JSON string.

        Args:
            json_str: JSON string to parse

        Returns:
            SharedBoard instance
        """
        data = json.loads(json_str)
        return BoardSerializer.board_from_dict(data)

    # ==========================================================================
    # Batch Serialization
    # ==========================================================================

    @staticmethod
    def boards_to_dict(boards: List[SharedBoard]) -> List[Dict[str, Any]]:
        """
        Convert list of SharedBoards to list of dictionaries.

        Args:
            boards: List of SharedBoard instances

        Returns:
            List of dictionary representations
        """
        return [BoardSerializer.board_to_dict(b) for b in boards]

    @staticmethod
    def boards_from_dict(data_list: List[Dict[str, Any]]) -> List[SharedBoard]:
        """
        Create list of SharedBoards from list of dictionaries.

        Args:
            data_list: List of dictionaries

        Returns:
            List of SharedBoard instances
        """
        return [BoardSerializer.board_from_dict(d) for d in data_list]
