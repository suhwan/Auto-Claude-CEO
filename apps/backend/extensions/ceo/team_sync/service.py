"""
Team Sync Service
=================

Integrated service for team synchronization.

This module provides TeamSyncService which integrates:
- SyncPointManager: Sync point management
- SharedBoardManager: Shared board management
- MeetingManager: Leader meeting management

Key Features:
- Phase lifecycle management (start, end)
- Team dashboard with unified status
- Urgent sync creation
- Phase overview and reporting
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .board_manager import SharedBoardManager
from .meeting_manager import MeetingManager
from .meeting_models import MeetingStatus
from .sync_manager import SyncPointManager


class TeamSyncService:
    """
    Team Sync Integration Service.

    Provides a unified interface for all team synchronization features
    including sync points, shared boards, and leader meetings.

    Attributes:
        project_path: Root project directory
        sync_manager: SyncPointManager instance
        board_manager: SharedBoardManager instance
        meeting_manager: MeetingManager instance
    """

    def __init__(self, project_path: str):
        """
        Initialize the TeamSyncService.

        Args:
            project_path: Root project directory path
        """
        self.project_path = project_path

        # Initialize components
        self.sync_manager = SyncPointManager(project_path)
        self.board_manager = SharedBoardManager(project_path, self.sync_manager)
        self.meeting_manager = MeetingManager(
            project_path, self.sync_manager, self.board_manager
        )

    # ==========================================================================
    # Phase Lifecycle
    # ==========================================================================

    def start_phase(self, phase: int, teams: List[str]) -> Dict[str, Any]:
        """
        Start a new phase.

        Creates all necessary artifacts for phase kickoff:
        - Shared board for team coordination
        - Kickoff meeting for phase planning
        - Sync point for phase start barrier

        Args:
            phase: Phase number to start
            teams: List of participating team IDs

        Returns:
            Dictionary with created board, meeting, and sync point
        """
        # 1. Create board
        board = self.board_manager.create_board(f"Phase {phase}", phase, teams)

        # 2. Create kickoff meeting
        meeting = self.meeting_manager.create_phase_kickoff(phase, teams)

        # 3. Create phase start sync point
        sync_point = self.sync_manager.create_barrier(
            f"Phase {phase} Start",
            teams,
            phase=phase,
        )

        return {
            "board": board,
            "kickoff_meeting": meeting,
            "sync_point": sync_point,
        }

    def end_phase(self, phase: int, teams: List[str]) -> Dict[str, Any]:
        """
        End a phase.

        Creates necessary artifacts for phase closure:
        - Review meeting for phase retrospective
        - Sync point for phase end barrier
        - Board summary with final status

        Args:
            phase: Phase number to end
            teams: List of participating team IDs

        Returns:
            Dictionary with meeting, sync point, and board summary
        """
        # 1. Create review meeting
        meeting = self.meeting_manager.create_phase_review(phase, teams)

        # 2. Create phase end sync point
        sync_point = self.sync_manager.create_barrier(
            f"Phase {phase} End",
            teams,
            phase=phase,
        )

        # 3. Get board summary
        board = self.board_manager.get_board_by_phase(phase)
        summary = self.board_manager.get_board_summary(board.id) if board else {}

        return {
            "review_meeting": meeting,
            "sync_point": sync_point,
            "board_summary": summary,
        }

    # ==========================================================================
    # Team Status
    # ==========================================================================

    def get_team_dashboard(
        self, team_id: str, phase: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get unified team dashboard.

        Aggregates data from all managers to provide a complete
        team status overview.

        Args:
            team_id: Team ID
            phase: Optional phase number for context

        Returns:
            Dictionary with team status, sync points, meetings, and actions
        """
        result = {
            "team_id": team_id,
            "waiting_sync_points": [],
            "board_status": None,
            "pending_meetings": [],
            "pending_actions": [],
        }

        # Waiting sync points
        result["waiting_sync_points"] = [
            {"id": sp.id, "name": sp.name, "status": sp.status.value}
            for sp in self.sync_manager.list_waiting_for_team(team_id)
        ]

        # Board status
        if phase:
            board = self.board_manager.get_board_by_phase(phase)
            if board:
                result["board_status"] = self.board_manager.get_team_status(
                    board.id, team_id
                )

        # Pending meetings
        scheduled_meetings = self.meeting_manager.list_meetings(
            phase=phase, status=MeetingStatus.SCHEDULED
        )
        result["pending_meetings"] = [
            {
                "id": m.id,
                "title": m.title,
                "scheduled_at": (
                    m.scheduled_at.isoformat() if m.scheduled_at else None
                ),
            }
            for m in scheduled_meetings
            if any(p.team_id == team_id for p in m.participants)
        ]

        # Pending actions
        result["pending_actions"] = self.meeting_manager.get_pending_actions(team_id)

        return result

    # ==========================================================================
    # Urgent Sync
    # ==========================================================================

    def create_urgent_sync(
        self,
        title: str,
        teams: List[str],
        blocker_ids: Optional[List[str]] = None,
        phase: int = 0,
    ) -> Dict[str, Any]:
        """
        Create an urgent synchronization.

        Creates an escalation meeting and sync point for
        urgent blocker resolution.

        Args:
            title: Title for the urgent sync
            teams: List of team IDs to involve
            blocker_ids: Optional list of blocker IDs
            phase: Associated phase number

        Returns:
            Dictionary with meeting and sync point
        """
        # 1. Create escalation meeting
        meeting = self.meeting_manager.create_escalation_meeting(
            blocker_ids or [],
            teams,
            phase,
        )

        # 2. Create sync point with short timeout
        sync_point = self.sync_manager.create_barrier(
            f"Urgent: {title}",
            teams,
            phase=phase,
            timeout_minutes=60,
        )

        return {
            "meeting": meeting,
            "sync_point": sync_point,
        }

    # ==========================================================================
    # Phase Overview
    # ==========================================================================

    def get_phase_overview(self, phase: int) -> Dict[str, Any]:
        """
        Get comprehensive phase overview.

        Aggregates all phase data including board summary,
        sync points, blockers, and meetings.

        Args:
            phase: Phase number

        Returns:
            Dictionary with complete phase status
        """
        board = self.board_manager.get_board_by_phase(phase)

        return {
            "phase": phase,
            "board_summary": (
                self.board_manager.get_board_summary(board.id) if board else None
            ),
            "active_sync_points": len(self.sync_manager.list_active(phase)),
            "blockers": (
                self.board_manager.get_blockers_summary(board.id) if board else []
            ),
            "upcoming_meetings": [
                {"id": m.id, "title": m.title, "type": m.meeting_type.value}
                for m in self.meeting_manager.list_meetings(
                    phase=phase, status=MeetingStatus.SCHEDULED
                )
            ],
            "dependency_graph": (
                self.board_manager.get_dependency_graph(board.id) if board else None
            ),
        }

    # ==========================================================================
    # Action Items
    # ==========================================================================

    def get_all_pending_actions(self) -> List[Dict[str, Any]]:
        """
        Get all pending action items across meetings.

        Returns:
            List of all pending action items
        """
        return self.meeting_manager.get_pending_actions()

    # ==========================================================================
    # Schedule Management
    # ==========================================================================

    def setup_regular_syncs(
        self,
        teams: List[str],
        standup_enabled: bool = True,
        weekly_sync_enabled: bool = True,
    ) -> Dict[str, Any]:
        """
        Set up regular sync schedules.

        Args:
            teams: List of team IDs to include
            standup_enabled: Whether to enable daily standups
            weekly_sync_enabled: Whether to enable weekly syncs

        Returns:
            Dictionary with created schedule IDs
        """
        from .meeting_models import MeetingType

        schedules = {}

        if standup_enabled:
            standup = self.meeting_manager.create_schedule(
                meeting_type=MeetingType.STANDUP,
                teams=teams,
                recurrence="daily",
                duration_minutes=15,
            )
            schedules["standup"] = standup.id

        if weekly_sync_enabled:
            weekly = self.meeting_manager.create_schedule(
                meeting_type=MeetingType.SYNC,
                teams=teams,
                recurrence="weekly",
                duration_minutes=30,
            )
            schedules["weekly_sync"] = weekly.id

        return schedules

    def check_scheduled_meetings(self) -> List[Dict[str, Any]]:
        """
        Check and create scheduled meetings.

        Returns:
            List of newly created meeting summaries
        """
        meetings = self.meeting_manager.check_and_create_scheduled_meetings()
        return [
            {
                "id": m.id,
                "title": m.title,
                "type": m.meeting_type.value,
                "scheduled_at": (
                    m.scheduled_at.isoformat() if m.scheduled_at else None
                ),
            }
            for m in meetings
        ]

    # ==========================================================================
    # Cross-Team Sync
    # ==========================================================================

    def create_cross_team_sync(
        self,
        title: str,
        producer_team: str,
        consumer_teams: List[str],
        phase: int = 0,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Create a cross-team synchronization point.

        One team produces output that other teams consume.

        Args:
            title: Sync point title
            producer_team: Team producing the deliverable
            consumer_teams: Teams waiting for the deliverable
            phase: Associated phase number
            description: Detailed description

        Returns:
            Dictionary with sync point details
        """
        sync_point = self.sync_manager.create_signal(
            name=title,
            sender=producer_team,
            receivers=consumer_teams,
            phase=phase,
            description=description,
        )

        return {
            "sync_point": sync_point,
            "producer": producer_team,
            "consumers": consumer_teams,
        }

    # ==========================================================================
    # Reporting
    # ==========================================================================

    def get_sync_health_report(self, phase: Optional[int] = None) -> Dict[str, Any]:
        """
        Get synchronization health report.

        Args:
            phase: Optional phase filter

        Returns:
            Dictionary with sync health metrics
        """
        active_syncs = self.sync_manager.list_active(phase)
        ready_syncs = self.sync_manager.list_ready()

        pending_meetings = self.meeting_manager.list_meetings(
            phase=phase, status=MeetingStatus.SCHEDULED
        )
        in_progress_meetings = self.meeting_manager.list_meetings(
            phase=phase, status=MeetingStatus.IN_PROGRESS
        )

        pending_actions = self.meeting_manager.get_pending_actions()
        overdue_actions = [a for a in pending_actions if a.get("overdue", False)]

        return {
            "sync_points": {
                "active": len(active_syncs),
                "ready": len(ready_syncs),
                "details": [
                    {
                        "id": sp.id,
                        "name": sp.name,
                        "type": sp.sync_type.value,
                        "status": sp.status.value,
                    }
                    for sp in active_syncs
                ],
            },
            "meetings": {
                "scheduled": len(pending_meetings),
                "in_progress": len(in_progress_meetings),
            },
            "action_items": {
                "pending": len(pending_actions),
                "overdue": len(overdue_actions),
            },
            "health_score": self._calculate_health_score(
                active_syncs, pending_actions, overdue_actions
            ),
            "generated_at": datetime.now().isoformat(),
        }

    def _calculate_health_score(
        self,
        active_syncs: list,
        pending_actions: list,
        overdue_actions: list,
    ) -> int:
        """
        Calculate sync health score (0-100).

        Args:
            active_syncs: List of active sync points
            pending_actions: List of pending actions
            overdue_actions: List of overdue actions

        Returns:
            Health score as integer
        """
        score = 100

        # Deduct for stuck sync points (more than expected)
        if len(active_syncs) > 5:
            score -= min(20, (len(active_syncs) - 5) * 5)

        # Deduct for overdue actions
        if overdue_actions:
            score -= min(30, len(overdue_actions) * 10)

        # Deduct for too many pending actions
        if len(pending_actions) > 10:
            score -= min(15, (len(pending_actions) - 10) * 3)

        return max(0, score)

    # ==========================================================================
    # Cleanup
    # ==========================================================================

    def clear_all(self) -> None:
        """Clear all data (for testing)."""
        self.sync_manager.clear()
        self.board_manager.clear()
        self.meeting_manager.clear()
