"""
Shared Board Manager
====================

Manages creation, updates, and queries for the Shared Board system.
Provides file-based persistence using JSON storage.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
from .sync_manager import SyncPointManager


class SharedBoardManager:
    """
    Shared Board Manager.

    Manages the lifecycle of shared boards including creation,
    task management, blocker tracking, and cross-team dependencies.

    Attributes:
        project_path: Root project directory
        sync_manager: SyncPointManager for sync point integration
        board_dir: Directory for board storage
    """

    def __init__(
        self,
        project_path: str,
        sync_manager: Optional[SyncPointManager] = None,
    ):
        """
        Initialize the SharedBoardManager.

        Args:
            project_path: Root project directory path
            sync_manager: Optional SyncPointManager instance
        """
        self.project_path = project_path
        self.sync_manager = sync_manager or SyncPointManager(project_path)
        self.board_dir = Path(project_path) / ".planning" / "team_sync" / "shared_board"
        self.board_dir.mkdir(parents=True, exist_ok=True)

        self._boards: Dict[str, SharedBoard] = {}
        self._load()

    # ==========================================================================
    # Board Management
    # ==========================================================================

    def create_board(
        self,
        name: str,
        phase: int,
        teams: List[str],
    ) -> SharedBoard:
        """
        Create a new shared board.

        Args:
            name: Human-readable board name
            phase: Associated phase number
            teams: List of team IDs to include as lanes

        Returns:
            Created SharedBoard instance
        """
        board = SharedBoard(
            id=f"board-{uuid.uuid4().hex[:8]}",
            name=name,
            phase=phase,
            lanes=[
                TeamLane(team_id=t, team_name=t, display_order=i)
                for i, t in enumerate(teams)
            ],
        )
        self._boards[board.id] = board
        self._save()
        return board

    def get_board(self, board_id: str) -> Optional[SharedBoard]:
        """
        Get a board by ID.

        Args:
            board_id: Board ID to retrieve

        Returns:
            SharedBoard instance or None if not found
        """
        return self._boards.get(board_id)

    def get_board_by_phase(self, phase: int) -> Optional[SharedBoard]:
        """
        Get a board by phase number.

        Args:
            phase: Phase number to search for

        Returns:
            SharedBoard instance or None if not found
        """
        for board in self._boards.values():
            if board.phase == phase:
                return board
        return None

    def list_boards(self) -> List[SharedBoard]:
        """
        List all boards.

        Returns:
            List of all SharedBoard instances
        """
        return list(self._boards.values())

    def delete_board(self, board_id: str) -> bool:
        """
        Delete a board.

        Args:
            board_id: Board ID to delete

        Returns:
            True if deleted successfully
        """
        if board_id in self._boards:
            del self._boards[board_id]
            self._save()
            return True
        return False

    # ==========================================================================
    # Task Management
    # ==========================================================================

    def add_task(
        self,
        board_id: str,
        team_id: str,
        title: str,
        description: str = "",
        depends_on: Optional[List[str]] = None,
        priority: int = 3,
        assignee: Optional[str] = None,
    ) -> Optional[BoardTask]:
        """
        Add a task to a team lane.

        Args:
            board_id: Board ID
            team_id: Team ID for the lane
            title: Task title
            description: Task description
            depends_on: List of task IDs this task depends on
            priority: Priority level (1-5)
            assignee: Optional assignee name/ID

        Returns:
            Created BoardTask or None if board/lane not found
        """
        board = self._boards.get(board_id)
        if not board:
            return None

        lane = self._get_lane(board, team_id)
        if not lane:
            return None

        task = BoardTask(
            id=f"task-{uuid.uuid4().hex[:8]}",
            team_id=team_id,
            title=title,
            description=description,
            depends_on=depends_on or [],
            priority=priority,
            assignee=assignee,
        )
        lane.tasks.append(task)
        lane.total_tasks += 1

        # Create dependency edges
        if depends_on:
            for dep_id in depends_on:
                dep_task, dep_lane = self._find_task(board, dep_id)
                if dep_task and dep_lane:
                    board.dependencies.append(
                        DependencyEdge(
                            from_team=dep_lane.team_id,
                            from_task=dep_id,
                            to_team=team_id,
                            to_task=task.id,
                        )
                    )
                    # Update blocking list on the dependency
                    dep_task.blocking.append(task.id)

        self._update_lane_stats(lane)
        board.last_updated = datetime.now()
        self._save()
        return task

    def get_task(self, board_id: str, task_id: str) -> Optional[BoardTask]:
        """
        Get a task by ID.

        Args:
            board_id: Board ID
            task_id: Task ID

        Returns:
            BoardTask or None if not found
        """
        board = self._boards.get(board_id)
        if not board:
            return None
        task, _ = self._find_task(board, task_id)
        return task

    def update_task_status(
        self,
        board_id: str,
        task_id: str,
        status: TaskStatus,
        progress: Optional[int] = None,
    ) -> bool:
        """
        Update a task's status.

        Args:
            board_id: Board ID
            task_id: Task ID
            status: New status
            progress: Optional new progress percentage

        Returns:
            True if updated successfully
        """
        board = self._boards.get(board_id)
        if not board:
            return False

        task, lane = self._find_task(board, task_id)
        if not task or not lane:
            return False

        old_status = task.status
        task.status = status

        if progress is not None:
            task.progress = max(0, min(100, progress))

        # Handle status transitions
        if status == TaskStatus.IN_PROGRESS and old_status == TaskStatus.NOT_STARTED:
            task.started_at = datetime.now()
            lane.current_focus = task.title
        elif status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now()
            task.progress = 100
            self._update_dependencies(board, task_id)
            # Clear current focus if this was the focused task
            if lane.current_focus == task.title:
                lane.current_focus = None

        self._update_lane_stats(lane)
        board.last_updated = datetime.now()
        lane.last_updated = datetime.now()
        self._save()
        return True

    def update_task(
        self,
        board_id: str,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        assignee: Optional[str] = None,
    ) -> bool:
        """
        Update task attributes.

        Args:
            board_id: Board ID
            task_id: Task ID
            title: New title (optional)
            description: New description (optional)
            priority: New priority (optional)
            assignee: New assignee (optional)

        Returns:
            True if updated successfully
        """
        board = self._boards.get(board_id)
        if not board:
            return False

        task, lane = self._find_task(board, task_id)
        if not task or not lane:
            return False

        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if priority is not None:
            task.priority = max(1, min(5, priority))
        if assignee is not None:
            task.assignee = assignee

        board.last_updated = datetime.now()
        lane.last_updated = datetime.now()
        self._save()
        return True

    def delete_task(self, board_id: str, task_id: str) -> bool:
        """
        Delete a task.

        Args:
            board_id: Board ID
            task_id: Task ID

        Returns:
            True if deleted successfully
        """
        board = self._boards.get(board_id)
        if not board:
            return False

        task, lane = self._find_task(board, task_id)
        if not task or not lane:
            return False

        # Remove from lane
        lane.tasks = [t for t in lane.tasks if t.id != task_id]

        # Remove dependency edges
        board.dependencies = [
            d
            for d in board.dependencies
            if d.from_task != task_id and d.to_task != task_id
        ]

        # Remove from blocking lists
        for other_lane in board.lanes:
            for other_task in other_lane.tasks:
                if task_id in other_task.blocking:
                    other_task.blocking.remove(task_id)
                if task_id in other_task.depends_on:
                    other_task.depends_on.remove(task_id)

        self._update_lane_stats(lane)
        board.last_updated = datetime.now()
        self._save()
        return True

    # ==========================================================================
    # Blocker Management
    # ==========================================================================

    def add_blocker(
        self,
        board_id: str,
        team_id: str,
        blocker_type: BlockerType,
        title: str,
        description: str = "",
        related_task_id: Optional[str] = None,
        blocking_team_id: Optional[str] = None,
        priority: str = "medium",
    ) -> Optional[Blocker]:
        """
        Add a blocker.

        Args:
            board_id: Board ID
            team_id: Team affected by the blocker
            blocker_type: Type of blocker
            title: Blocker title
            description: Detailed description
            related_task_id: Task affected by this blocker
            blocking_team_id: Team causing the block
            priority: Priority level (low, medium, high, critical)

        Returns:
            Created Blocker or None if board/lane not found
        """
        board = self._boards.get(board_id)
        if not board:
            return None

        lane = self._get_lane(board, team_id)
        if not lane:
            return None

        blocker = Blocker(
            id=f"blocker-{uuid.uuid4().hex[:8]}",
            team_id=team_id,
            blocker_type=blocker_type,
            title=title,
            description=description,
            related_task_id=related_task_id,
            blocking_team_id=blocking_team_id,
            priority=priority,
        )
        lane.blockers.append(blocker)

        # Update related task status
        if related_task_id:
            self.update_task_status(board_id, related_task_id, TaskStatus.BLOCKED)

        board.last_updated = datetime.now()
        self._save()
        return blocker

    def get_blocker(self, board_id: str, blocker_id: str) -> Optional[Blocker]:
        """
        Get a blocker by ID.

        Args:
            board_id: Board ID
            blocker_id: Blocker ID

        Returns:
            Blocker or None if not found
        """
        board = self._boards.get(board_id)
        if not board:
            return None

        for lane in board.lanes:
            for blocker in lane.blockers:
                if blocker.id == blocker_id:
                    return blocker
        return None

    def resolve_blocker(
        self,
        board_id: str,
        blocker_id: str,
        resolution: str = "",
    ) -> bool:
        """
        Resolve a blocker.

        Args:
            board_id: Board ID
            blocker_id: Blocker ID
            resolution: Description of how it was resolved

        Returns:
            True if resolved successfully
        """
        board = self._boards.get(board_id)
        if not board:
            return False

        for lane in board.lanes:
            for blocker in lane.blockers:
                if blocker.id == blocker_id:
                    blocker.resolved = True
                    blocker.resolved_at = datetime.now()
                    blocker.resolution = resolution

                    # Restore related task status
                    if blocker.related_task_id:
                        self.update_task_status(
                            board_id,
                            blocker.related_task_id,
                            TaskStatus.IN_PROGRESS,
                        )

                    board.last_updated = datetime.now()
                    self._save()
                    return True
        return False

    def delete_blocker(self, board_id: str, blocker_id: str) -> bool:
        """
        Delete a blocker.

        Args:
            board_id: Board ID
            blocker_id: Blocker ID

        Returns:
            True if deleted successfully
        """
        board = self._boards.get(board_id)
        if not board:
            return False

        for lane in board.lanes:
            for blocker in lane.blockers:
                if blocker.id == blocker_id:
                    lane.blockers.remove(blocker)
                    board.last_updated = datetime.now()
                    self._save()
                    return True
        return False

    # ==========================================================================
    # Query Methods
    # ==========================================================================

    def get_team_status(self, board_id: str, team_id: str) -> Dict[str, Any]:
        """
        Get team status summary.

        Args:
            board_id: Board ID
            team_id: Team ID

        Returns:
            Dictionary with team status details
        """
        board = self._boards.get(board_id)
        if not board:
            return {}

        lane = self._get_lane(board, team_id)
        if not lane:
            return {}

        active_blockers = [b for b in lane.blockers if not b.resolved]

        return {
            "team_id": lane.team_id,
            "team_name": lane.team_name,
            "total_tasks": lane.total_tasks,
            "completed": lane.completed_tasks,
            "in_progress": lane.in_progress_tasks,
            "blocked": lane.blocked_tasks,
            "progress_percent": (
                (lane.completed_tasks / lane.total_tasks * 100)
                if lane.total_tasks > 0
                else 0
            ),
            "current_focus": lane.current_focus,
            "active_blockers": len(active_blockers),
            "blocker_details": [
                {
                    "id": b.id,
                    "type": b.blocker_type.value,
                    "title": b.title,
                    "priority": b.priority,
                }
                for b in active_blockers
            ],
            "last_updated": lane.last_updated.isoformat(),
        }

    def get_board_summary(self, board_id: str) -> Dict[str, Any]:
        """
        Get board summary.

        Args:
            board_id: Board ID

        Returns:
            Dictionary with board summary
        """
        board = self._boards.get(board_id)
        if not board:
            return {}

        total_tasks = sum(l.total_tasks for l in board.lanes)
        completed_tasks = sum(l.completed_tasks for l in board.lanes)
        blocked_count = sum(
            len([b for b in l.blockers if not b.resolved]) for l in board.lanes
        )

        return {
            "board_id": board.id,
            "name": board.name,
            "phase": board.phase,
            "teams": [l.team_id for l in board.lanes],
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "progress_percent": (
                (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            ),
            "active_blockers": blocked_count,
            "pending_sync_points": len(board.active_sync_points),
            "dependency_count": len(board.dependencies),
            "last_updated": board.last_updated.isoformat(),
        }

    def get_dependency_graph(self, board_id: str) -> Dict[str, Any]:
        """
        Get dependency graph for visualization.

        Args:
            board_id: Board ID

        Returns:
            Dictionary with nodes and edges for the graph
        """
        board = self._boards.get(board_id)
        if not board:
            return {}

        return {
            "nodes": [
                {
                    "id": l.team_id,
                    "name": l.team_name,
                    "tasks": len(l.tasks),
                    "progress": (
                        (l.completed_tasks / l.total_tasks * 100)
                        if l.total_tasks > 0
                        else 0
                    ),
                }
                for l in board.lanes
            ],
            "edges": [
                {
                    "from": d.from_team,
                    "to": d.to_team,
                    "status": d.status,
                    "task_from": d.from_task,
                    "task_to": d.to_task,
                }
                for d in board.dependencies
            ],
        }

    def get_blockers_summary(self, board_id: str) -> List[Dict[str, Any]]:
        """
        Get all active blockers summary.

        Args:
            board_id: Board ID

        Returns:
            List of blocker summaries sorted by priority
        """
        board = self._boards.get(board_id)
        if not board:
            return []

        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        blockers = []

        for lane in board.lanes:
            for b in lane.blockers:
                if not b.resolved:
                    blockers.append(
                        {
                            "id": b.id,
                            "team": lane.team_id,
                            "type": b.blocker_type.value,
                            "title": b.title,
                            "description": b.description,
                            "blocking_team": b.blocking_team_id,
                            "related_task": b.related_task_id,
                            "priority": b.priority,
                            "created_at": b.created_at.isoformat(),
                        }
                    )

        return sorted(blockers, key=lambda x: priority_order.get(x["priority"], 2))

    def get_tasks_by_status(
        self,
        board_id: str,
        status: TaskStatus,
    ) -> List[Dict[str, Any]]:
        """
        Get all tasks with a specific status.

        Args:
            board_id: Board ID
            status: Status to filter by

        Returns:
            List of task summaries
        """
        board = self._boards.get(board_id)
        if not board:
            return []

        tasks = []
        for lane in board.lanes:
            for task in lane.tasks:
                if task.status == status:
                    tasks.append(
                        {
                            "id": task.id,
                            "team": lane.team_id,
                            "title": task.title,
                            "progress": task.progress,
                            "priority": task.priority,
                            "assignee": task.assignee,
                        }
                    )

        return sorted(tasks, key=lambda x: x["priority"])

    # ==========================================================================
    # Sync Point Integration
    # ==========================================================================

    def link_sync_point(self, board_id: str, sync_point_id: str) -> bool:
        """
        Link a sync point to the board.

        Args:
            board_id: Board ID
            sync_point_id: Sync point ID to link

        Returns:
            True if linked successfully
        """
        board = self._boards.get(board_id)
        if not board:
            return False

        if sync_point_id not in board.active_sync_points:
            board.active_sync_points.append(sync_point_id)
            board.last_updated = datetime.now()
            self._save()
        return True

    def unlink_sync_point(self, board_id: str, sync_point_id: str) -> bool:
        """
        Unlink a sync point from the board.

        Args:
            board_id: Board ID
            sync_point_id: Sync point ID to unlink

        Returns:
            True if unlinked successfully
        """
        board = self._boards.get(board_id)
        if not board:
            return False

        if sync_point_id in board.active_sync_points:
            board.active_sync_points.remove(sync_point_id)
            board.last_updated = datetime.now()
            self._save()
        return True

    # ==========================================================================
    # Internal Methods
    # ==========================================================================

    def _get_lane(self, board: SharedBoard, team_id: str) -> Optional[TeamLane]:
        """
        Get team lane from board.

        Args:
            board: SharedBoard instance
            team_id: Team ID to find

        Returns:
            TeamLane or None if not found
        """
        for lane in board.lanes:
            if lane.team_id == team_id:
                return lane
        return None

    def _find_task(
        self,
        board: SharedBoard,
        task_id: str,
    ) -> Tuple[Optional[BoardTask], Optional[TeamLane]]:
        """
        Find a task in the board.

        Args:
            board: SharedBoard instance
            task_id: Task ID to find

        Returns:
            Tuple of (BoardTask, TeamLane) or (None, None) if not found
        """
        for lane in board.lanes:
            for task in lane.tasks:
                if task.id == task_id:
                    return task, lane
        return None, None

    def _update_lane_stats(self, lane: TeamLane) -> None:
        """
        Update lane statistics.

        Args:
            lane: TeamLane to update
        """
        lane.total_tasks = len(lane.tasks)
        lane.completed_tasks = sum(
            1 for t in lane.tasks if t.status == TaskStatus.COMPLETED
        )
        lane.in_progress_tasks = sum(
            1 for t in lane.tasks if t.status == TaskStatus.IN_PROGRESS
        )
        lane.blocked_tasks = sum(
            1 for t in lane.tasks if t.status == TaskStatus.BLOCKED
        )

    def _update_dependencies(self, board: SharedBoard, completed_task_id: str) -> None:
        """
        Update dependency statuses when a task is completed.

        Args:
            board: SharedBoard instance
            completed_task_id: ID of the completed task
        """
        for dep in board.dependencies:
            if dep.from_task == completed_task_id:
                dep.status = "satisfied"

    # ==========================================================================
    # Persistence Methods
    # ==========================================================================

    def _load(self) -> None:
        """Load boards from disk."""
        boards_file = self.board_dir / "boards.json"
        if boards_file.exists():
            try:
                with open(boards_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._boards = {
                        b["id"]: BoardSerializer.board_from_dict(b)
                        for b in data.get("boards", [])
                    }
            except (json.JSONDecodeError, KeyError):
                # Log error but continue with empty state
                self._boards = {}

    def _save(self) -> None:
        """Save boards to disk."""
        boards_file = self.board_dir / "boards.json"
        boards_data = {
            "boards": BoardSerializer.boards_to_dict(list(self._boards.values()))
        }
        with open(boards_file, "w", encoding="utf-8") as f:
            json.dump(boards_data, f, indent=2, ensure_ascii=False)

    def clear(self) -> None:
        """Clear all boards (for testing)."""
        self._boards = {}
        self._save()
