"""
Shared Board Models
===================

Data models for the Shared Board system.

The Shared Board provides a visual representation of:
- Team task lanes with progress tracking
- Cross-team dependencies
- Blockers and their resolution status
- Sync point integration

Storage Location: `.planning/team_sync/shared_board/`
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(Enum):
    """
    Task status in the board.

    Defines the lifecycle state of a task:
    - NOT_STARTED: Task has not begun
    - IN_PROGRESS: Task is actively being worked on
    - BLOCKED: Task is blocked by a blocker
    - WAITING: Task is waiting for a dependency
    - COMPLETED: Task has been finished
    """
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    WAITING = "waiting"
    COMPLETED = "completed"


class BlockerType(Enum):
    """
    Blocker type classification.

    Categories of blockers that can impede task progress:
    - DEPENDENCY: Waiting for another team's work
    - TECHNICAL: Technical issue needs resolution
    - RESOURCE: Resource availability problem
    - DECISION: Awaiting decision or approval
    - EXTERNAL: External factor outside team control
    """
    DEPENDENCY = "dependency"
    TECHNICAL = "technical"
    RESOURCE = "resource"
    DECISION = "decision"
    EXTERNAL = "external"


@dataclass
class BoardTask:
    """
    Board task item.

    Represents a task displayed on the shared board within a team lane.

    Attributes:
        id: Unique task identifier
        team_id: Team owning this task
        title: Task title
        description: Detailed task description
        status: Current task status
        progress: Progress percentage (0-100)

        depends_on: List of task IDs this task depends on
        blocking: List of task IDs this task is blocking

        assignee: Optional assignee name/ID
        priority: Priority level (1=highest, 5=lowest)

        created_at: When the task was created
        started_at: When work began
        completed_at: When the task was finished

        metadata: Additional task metadata
    """
    id: str
    team_id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.NOT_STARTED
    progress: int = 0  # 0-100

    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    blocking: List[str] = field(default_factory=list)

    # Assignment
    assignee: Optional[str] = None
    priority: int = 3  # 1-5 (1=highest)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Blocker:
    """
    Blocker item.

    Represents an impediment blocking task progress.

    Attributes:
        id: Unique blocker identifier
        team_id: Team affected by this blocker
        blocker_type: Category of blocker
        title: Blocker title
        description: Detailed description

        related_task_id: Task affected by this blocker
        blocking_team_id: Team causing the block (if applicable)

        resolved: Whether the blocker has been resolved
        resolved_at: When the blocker was resolved
        resolution: Description of how it was resolved

        created_at: When the blocker was created
        priority: Priority level (low, medium, high, critical)
    """
    id: str
    team_id: str
    blocker_type: BlockerType
    title: str
    description: str = ""

    # Related items
    related_task_id: Optional[str] = None
    blocking_team_id: Optional[str] = None

    # Resolution status
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None

    # Timestamps and priority
    created_at: datetime = field(default_factory=datetime.now)
    priority: str = "medium"  # low, medium, high, critical


@dataclass
class TeamLane:
    """
    Team lane in the board.

    Represents a swimlane for a specific team showing their tasks and status.

    Attributes:
        team_id: Unique team identifier
        team_name: Human-readable team name
        display_order: Order in which to display this lane

        tasks: List of tasks in this lane
        blockers: List of blockers affecting this team

        total_tasks: Total number of tasks
        completed_tasks: Number of completed tasks
        in_progress_tasks: Number of in-progress tasks
        blocked_tasks: Number of blocked tasks

        current_focus: Title of the currently focused task
        last_updated: When this lane was last updated
    """
    team_id: str
    team_name: str
    display_order: int = 0

    # Tasks and blockers
    tasks: List[BoardTask] = field(default_factory=list)
    blockers: List[Blocker] = field(default_factory=list)

    # Statistics
    total_tasks: int = 0
    completed_tasks: int = 0
    in_progress_tasks: int = 0
    blocked_tasks: int = 0

    # Current state
    current_focus: Optional[str] = None
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class DependencyEdge:
    """
    Dependency edge between tasks.

    Represents a directed dependency from one task to another across teams.

    Attributes:
        from_team: Team ID of the source task
        from_task: Task ID of the source
        to_team: Team ID of the dependent task
        to_task: Task ID that depends on the source
        status: Dependency status (pending, satisfied, blocked)
    """
    from_team: str
    from_task: str
    to_team: str
    to_task: str
    status: str = "pending"  # pending, satisfied, blocked


@dataclass
class SharedBoard:
    """
    Shared board for team coordination.

    Central dashboard showing all teams' work and their interdependencies.

    Attributes:
        id: Unique board identifier
        name: Board name
        phase: Associated phase number

        lanes: List of team lanes
        dependencies: Cross-team dependency graph

        active_sync_points: IDs of active sync points related to this board

        created_at: When the board was created
        last_updated: When the board was last modified

        auto_sync: Whether to automatically sync with sync points
        update_interval_seconds: How often to update (in seconds)
    """
    id: str
    name: str
    phase: int

    # Team lanes
    lanes: List[TeamLane] = field(default_factory=list)

    # Dependency graph
    dependencies: List[DependencyEdge] = field(default_factory=list)

    # Sync point integration
    active_sync_points: List[str] = field(default_factory=list)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    # Configuration
    auto_sync: bool = True
    update_interval_seconds: int = 60
