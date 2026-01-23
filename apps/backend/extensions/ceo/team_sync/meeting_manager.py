"""
Meeting Manager
===============

Manages creation, lifecycle, and persistence of Leader Meetings.

This module provides:
- Meeting creation (standup, sync, escalation, kickoff, review)
- Meeting lifecycle (start, end, cancel)
- Agenda management and auto-generation
- Action item tracking
- Recurring schedule management
- File-based JSON persistence

Storage Location: `.planning/team_sync/meetings/`
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .board_manager import SharedBoardManager
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
from .sync_manager import SyncPointManager


class MeetingManager:
    """
    Leader Meeting Manager.

    Manages the lifecycle of leader meetings including creation,
    agenda generation, action item tracking, and scheduling.

    Attributes:
        project_path: Root project directory
        sync_manager: SyncPointManager for sync point integration
        board_manager: SharedBoardManager for board integration
        meetings_dir: Directory for meeting storage
    """

    def __init__(
        self,
        project_path: str,
        sync_manager: Optional[SyncPointManager] = None,
        board_manager: Optional[SharedBoardManager] = None,
    ):
        """
        Initialize the MeetingManager.

        Args:
            project_path: Root project directory path
            sync_manager: Optional SyncPointManager instance
            board_manager: Optional SharedBoardManager instance
        """
        self.project_path = project_path
        self.sync_manager = sync_manager or SyncPointManager(project_path)
        self.board_manager = board_manager or SharedBoardManager(
            project_path, self.sync_manager
        )
        self.meetings_dir = Path(project_path) / ".planning" / "team_sync" / "meetings"
        self.meetings_dir.mkdir(parents=True, exist_ok=True)

        self._meetings: Dict[str, Meeting] = {}
        self._schedules: Dict[str, MeetingSchedule] = {}
        self._load()

    # ==========================================================================
    # Meeting Creation
    # ==========================================================================

    def create_meeting(
        self,
        title: str,
        meeting_type: MeetingType,
        teams: List[str],
        phase: int = 0,
        duration_minutes: int = 30,
        scheduled_at: Optional[datetime] = None,
    ) -> Meeting:
        """
        Create a new meeting.

        Args:
            title: Meeting title
            meeting_type: Type of meeting
            teams: List of participating team IDs
            phase: Associated phase number
            duration_minutes: Expected duration in minutes
            scheduled_at: Scheduled start time (defaults to now)

        Returns:
            Created Meeting instance
        """
        meeting = Meeting(
            id=f"meeting-{uuid.uuid4().hex[:8]}",
            title=title,
            meeting_type=meeting_type,
            phase=phase,
            duration_minutes=duration_minutes,
            scheduled_at=scheduled_at or datetime.now(),
            participants=[
                MeetingParticipant(team_id=t, team_name=t) for t in teams
            ],
        )

        # Auto-generate agenda
        meeting.agenda = self._generate_agenda(meeting_type, phase, teams)

        self._meetings[meeting.id] = meeting
        self._save()
        return meeting

    def create_escalation_meeting(
        self,
        blocker_ids: List[str],
        teams: List[str],
        phase: int = 0,
    ) -> Meeting:
        """
        Create an escalation meeting for blocker resolution.

        Args:
            blocker_ids: List of blocker IDs to address
            teams: List of participating team IDs
            phase: Associated phase number

        Returns:
            Created Meeting instance
        """
        meeting = self.create_meeting(
            title="Blocker Resolution Meeting",
            meeting_type=MeetingType.ESCALATION,
            teams=teams,
            phase=phase,
            duration_minutes=45,
        )
        meeting.related_blocker_ids = blocker_ids

        # Add blocker-specific agenda items
        for blocker_id in blocker_ids:
            meeting.agenda.append(
                AgendaItem(
                    id=f"agenda-{blocker_id}",
                    title=f"Blocker: {blocker_id}",
                    time_minutes=10,
                )
            )

        self._save()
        return meeting

    def create_phase_kickoff(self, phase: int, teams: List[str]) -> Meeting:
        """
        Create a phase kickoff meeting.

        Args:
            phase: Phase number to kick off
            teams: List of participating team IDs

        Returns:
            Created Meeting instance
        """
        meeting = self.create_meeting(
            title=f"Phase {phase} Kickoff",
            meeting_type=MeetingType.KICKOFF,
            teams=teams,
            phase=phase,
            duration_minutes=60,
        )

        meeting.agenda = [
            AgendaItem(id="1", title="Phase 목표 공유", time_minutes=15),
            AgendaItem(id="2", title="팀별 계획 발표", time_minutes=20),
            AgendaItem(id="3", title="의존성 및 리스크 논의", time_minutes=15),
            AgendaItem(id="4", title="Sync Points 합의", time_minutes=10),
        ]

        self._save()
        return meeting

    def create_phase_review(self, phase: int, teams: List[str]) -> Meeting:
        """
        Create a phase review meeting.

        Args:
            phase: Phase number to review
            teams: List of participating team IDs

        Returns:
            Created Meeting instance
        """
        meeting = self.create_meeting(
            title=f"Phase {phase} Review",
            meeting_type=MeetingType.REVIEW,
            teams=teams,
            phase=phase,
            duration_minutes=60,
        )

        meeting.agenda = [
            AgendaItem(id="1", title="목표 달성 현황", time_minutes=15),
            AgendaItem(id="2", title="팀별 성과 공유", time_minutes=20),
            AgendaItem(id="3", title="배운 점/개선점", time_minutes=15),
            AgendaItem(id="4", title="다음 Phase 준비", time_minutes=10),
        ]

        self._save()
        return meeting

    # ==========================================================================
    # Meeting Lifecycle
    # ==========================================================================

    def start_meeting(self, meeting_id: str) -> Dict[str, Any]:
        """
        Start a meeting.

        Args:
            meeting_id: Meeting ID to start

        Returns:
            Result dictionary with success status and meeting details
        """
        meeting = self._meetings.get(meeting_id)
        if not meeting:
            return {"success": False, "error": "Meeting not found"}

        meeting.status = MeetingStatus.IN_PROGRESS
        meeting.started_at = datetime.now()
        self._save()

        return {
            "success": True,
            "meeting": meeting,
            "agenda": meeting.agenda,
        }

    def record_attendance(self, meeting_id: str, team_id: str) -> bool:
        """
        Record team attendance at a meeting.

        Args:
            meeting_id: Meeting ID
            team_id: Team ID to mark as attended

        Returns:
            True if attendance was recorded successfully
        """
        meeting = self._meetings.get(meeting_id)
        if not meeting:
            return False

        for participant in meeting.participants:
            if participant.team_id == team_id:
                participant.attended = True
                participant.joined_at = datetime.now()
                self._save()
                return True
        return False

    def update_agenda_item(
        self,
        meeting_id: str,
        agenda_item_id: str,
        status: str,
        notes: str = "",
        decisions: Optional[List[str]] = None,
    ) -> bool:
        """
        Update an agenda item.

        Args:
            meeting_id: Meeting ID
            agenda_item_id: Agenda item ID to update
            status: New status (pending, discussed, skipped)
            notes: Notes for the agenda item
            decisions: List of decisions made

        Returns:
            True if updated successfully
        """
        meeting = self._meetings.get(meeting_id)
        if not meeting:
            return False

        for item in meeting.agenda:
            if item.id == agenda_item_id:
                item.status = status
                item.notes = notes
                if decisions:
                    item.decisions = decisions
                self._save()
                return True
        return False

    def add_action_item(
        self,
        meeting_id: str,
        title: str,
        assignee: str,
        due_date: Optional[datetime] = None,
    ) -> Optional[ActionItem]:
        """
        Add an action item to a meeting.

        Args:
            meeting_id: Meeting ID
            title: Action item title
            assignee: Team/person responsible
            due_date: Optional due date

        Returns:
            Created ActionItem or None if meeting not found
        """
        meeting = self._meetings.get(meeting_id)
        if not meeting:
            return None

        action = ActionItem(
            id=f"action-{uuid.uuid4().hex[:8]}",
            title=title,
            assignee=assignee,
            due_date=due_date,
        )
        meeting.action_items.append(action)
        self._save()
        return action

    def end_meeting(
        self,
        meeting_id: str,
        summary: str = "",
        key_decisions: Optional[List[str]] = None,
        next_steps: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        End a meeting.

        Args:
            meeting_id: Meeting ID to end
            summary: Meeting summary
            key_decisions: List of key decisions made
            next_steps: List of next steps

        Returns:
            Result dictionary with success status and meeting summary
        """
        meeting = self._meetings.get(meeting_id)
        if not meeting:
            return {"success": False, "error": "Meeting not found"}

        meeting.status = MeetingStatus.COMPLETED
        meeting.ended_at = datetime.now()

        # Update minutes
        meeting.minutes.summary = summary
        meeting.minutes.key_decisions = key_decisions or []
        meeting.minutes.next_steps = next_steps or []

        # Auto-generate summary if not provided
        if not summary:
            meeting.minutes.summary = self._generate_summary(meeting)

        self._save()

        actual_duration = 0
        if meeting.started_at and meeting.ended_at:
            actual_duration = (meeting.ended_at - meeting.started_at).seconds // 60

        return {
            "success": True,
            "duration_actual": actual_duration,
            "decisions_count": len(meeting.minutes.key_decisions),
            "action_items_count": len(meeting.action_items),
        }

    def cancel_meeting(self, meeting_id: str, reason: str = "") -> bool:
        """
        Cancel a meeting.

        Args:
            meeting_id: Meeting ID to cancel
            reason: Reason for cancellation

        Returns:
            True if cancelled successfully
        """
        meeting = self._meetings.get(meeting_id)
        if not meeting:
            return False

        if meeting.status in (MeetingStatus.COMPLETED, MeetingStatus.CANCELLED):
            return False

        meeting.status = MeetingStatus.CANCELLED
        meeting.metadata["cancelled_reason"] = reason
        self._save()
        return True

    # ==========================================================================
    # Action Item Management
    # ==========================================================================

    def update_action_item(
        self,
        meeting_id: str,
        action_id: str,
        status: str,
        notes: str = "",
    ) -> bool:
        """
        Update an action item's status.

        Args:
            meeting_id: Meeting ID
            action_id: Action item ID to update
            status: New status (pending, in_progress, completed)
            notes: Optional notes

        Returns:
            True if updated successfully
        """
        meeting = self._meetings.get(meeting_id)
        if not meeting:
            return False

        for action in meeting.action_items:
            if action.id == action_id:
                action.status = status
                action.notes = notes
                if status == "completed":
                    action.completed_at = datetime.now()
                self._save()
                return True
        return False

    def get_pending_actions(
        self, team_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending action items.

        Args:
            team_id: Optional team ID to filter by

        Returns:
            List of pending action item details sorted by due date
        """
        actions = []
        for meeting in self._meetings.values():
            for action in meeting.action_items:
                if action.status != "completed":
                    if team_id is None or action.assignee == team_id:
                        actions.append(
                            {
                                "meeting_id": meeting.id,
                                "meeting_title": meeting.title,
                                "action": action,
                                "overdue": (
                                    action.due_date is not None
                                    and action.due_date < datetime.now()
                                ),
                            }
                        )
        return sorted(
            actions, key=lambda x: x["action"].due_date or datetime.max
        )

    # ==========================================================================
    # Schedule Management
    # ==========================================================================

    def create_schedule(
        self,
        meeting_type: MeetingType,
        teams: List[str],
        recurrence: str = "weekly",
        duration_minutes: int = 30,
    ) -> MeetingSchedule:
        """
        Create a recurring meeting schedule.

        Args:
            meeting_type: Type of recurring meeting
            teams: List of participating team IDs
            recurrence: Recurrence pattern (none, daily, weekly, phase_start, phase_end)
            duration_minutes: Default duration in minutes

        Returns:
            Created MeetingSchedule instance
        """
        schedule = MeetingSchedule(
            id=f"sched-{uuid.uuid4().hex[:8]}",
            meeting_type=meeting_type,
            recurrence=recurrence,
            teams=teams,
            default_duration_minutes=duration_minutes,
            next_occurrence=self._calculate_next_occurrence(recurrence),
        )
        self._schedules[schedule.id] = schedule
        self._save()
        return schedule

    def get_schedule(self, schedule_id: str) -> Optional[MeetingSchedule]:
        """
        Get a schedule by ID.

        Args:
            schedule_id: Schedule ID

        Returns:
            MeetingSchedule or None if not found
        """
        return self._schedules.get(schedule_id)

    def list_schedules(self) -> List[MeetingSchedule]:
        """
        List all schedules.

        Returns:
            List of all MeetingSchedule instances
        """
        return list(self._schedules.values())

    def update_schedule(
        self,
        schedule_id: str,
        enabled: Optional[bool] = None,
        recurrence: Optional[str] = None,
    ) -> bool:
        """
        Update a schedule.

        Args:
            schedule_id: Schedule ID
            enabled: Whether the schedule is enabled
            recurrence: New recurrence pattern

        Returns:
            True if updated successfully
        """
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return False

        if enabled is not None:
            schedule.enabled = enabled
        if recurrence is not None:
            schedule.recurrence = recurrence
            schedule.next_occurrence = self._calculate_next_occurrence(recurrence)

        self._save()
        return True

    def delete_schedule(self, schedule_id: str) -> bool:
        """
        Delete a schedule.

        Args:
            schedule_id: Schedule ID to delete

        Returns:
            True if deleted successfully
        """
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            self._save()
            return True
        return False

    def check_and_create_scheduled_meetings(self) -> List[Meeting]:
        """
        Check schedules and create meetings as needed.

        Returns:
            List of newly created meetings
        """
        created = []
        now = datetime.now()

        for schedule in self._schedules.values():
            if not schedule.enabled:
                continue

            if schedule.next_occurrence and schedule.next_occurrence <= now:
                meeting = self.create_meeting(
                    title=f"{schedule.meeting_type.value.title()} Meeting",
                    meeting_type=schedule.meeting_type,
                    teams=schedule.teams,
                    duration_minutes=schedule.default_duration_minutes,
                    scheduled_at=schedule.next_occurrence,
                )
                created.append(meeting)

                schedule.next_occurrence = self._calculate_next_occurrence(
                    schedule.recurrence, from_date=schedule.next_occurrence
                )

        if created:
            self._save()
        return created

    # ==========================================================================
    # Query Methods
    # ==========================================================================

    def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        """
        Get a meeting by ID.

        Args:
            meeting_id: Meeting ID

        Returns:
            Meeting or None if not found
        """
        return self._meetings.get(meeting_id)

    def list_meetings(
        self,
        phase: Optional[int] = None,
        status: Optional[MeetingStatus] = None,
        meeting_type: Optional[MeetingType] = None,
    ) -> List[Meeting]:
        """
        List meetings with optional filters.

        Args:
            phase: Optional phase number filter
            status: Optional status filter
            meeting_type: Optional meeting type filter

        Returns:
            List of matching meetings sorted by scheduled date
        """
        result = list(self._meetings.values())

        if phase is not None:
            result = [m for m in result if m.phase == phase]
        if status is not None:
            result = [m for m in result if m.status == status]
        if meeting_type is not None:
            result = [m for m in result if m.meeting_type == meeting_type]

        return sorted(
            result, key=lambda m: m.scheduled_at or datetime.min, reverse=True
        )

    def get_meeting_history(self, team_id: str) -> List[Dict[str, Any]]:
        """
        Get meeting history for a team.

        Args:
            team_id: Team ID

        Returns:
            List of meeting summaries for the team
        """
        history = []
        for meeting in self._meetings.values():
            if any(p.team_id == team_id for p in meeting.participants):
                history.append(
                    {
                        "id": meeting.id,
                        "title": meeting.title,
                        "type": meeting.meeting_type.value,
                        "status": meeting.status.value,
                        "date": (
                            meeting.scheduled_at.isoformat()
                            if meeting.scheduled_at
                            else None
                        ),
                        "attended": any(
                            p.team_id == team_id and p.attended
                            for p in meeting.participants
                        ),
                    }
                )
        return sorted(history, key=lambda x: x["date"] or "", reverse=True)

    # ==========================================================================
    # Internal Methods
    # ==========================================================================

    def _generate_agenda(
        self,
        meeting_type: MeetingType,
        phase: int,
        teams: List[str],
    ) -> List[AgendaItem]:
        """
        Generate agenda items based on meeting type.

        Args:
            meeting_type: Type of meeting
            phase: Phase number
            teams: List of participating teams

        Returns:
            List of generated AgendaItem instances
        """
        agenda = []

        if meeting_type == MeetingType.STANDUP:
            for i, team in enumerate(teams):
                agenda.append(
                    AgendaItem(
                        id=f"standup-{i}",
                        title=f"{team} 상태 공유",
                        presenter=team,
                        time_minutes=3,
                    )
                )

        elif meeting_type == MeetingType.SYNC:
            agenda = [
                AgendaItem(id="1", title="진행 상황 공유", time_minutes=10),
                AgendaItem(id="2", title="블로커 논의", time_minutes=10),
                AgendaItem(id="3", title="다음 주 계획", time_minutes=10),
            ]

        elif meeting_type == MeetingType.RETROSPECTIVE:
            agenda = [
                AgendaItem(id="1", title="잘한 점", time_minutes=10),
                AgendaItem(id="2", title="개선할 점", time_minutes=10),
                AgendaItem(id="3", title="액션 아이템", time_minutes=10),
            ]

        return agenda

    def _generate_summary(self, meeting: Meeting) -> str:
        """
        Generate an auto-summary for a meeting.

        Args:
            meeting: Meeting to summarize

        Returns:
            Summary string
        """
        discussed = [a.title for a in meeting.agenda if a.status == "discussed"]
        actions = len(meeting.action_items)
        return f"Discussed: {', '.join(discussed) if discussed else 'None'}. Created {actions} action items."

    def _calculate_next_occurrence(
        self,
        recurrence: str,
        from_date: Optional[datetime] = None,
    ) -> Optional[datetime]:
        """
        Calculate next occurrence for a schedule.

        Args:
            recurrence: Recurrence pattern
            from_date: Base date to calculate from

        Returns:
            Next occurrence datetime or None
        """
        base = from_date or datetime.now()

        if recurrence == "daily":
            return base + timedelta(days=1)
        elif recurrence == "weekly":
            return base + timedelta(weeks=1)
        elif recurrence == "none":
            return None
        return None

    # ==========================================================================
    # Serialization
    # ==========================================================================

    def _serialize_meeting(self, meeting: Meeting) -> Dict[str, Any]:
        """Serialize a meeting to dictionary."""
        return {
            "id": meeting.id,
            "title": meeting.title,
            "meeting_type": meeting.meeting_type.value,
            "status": meeting.status.value,
            "scheduled_at": (
                meeting.scheduled_at.isoformat() if meeting.scheduled_at else None
            ),
            "started_at": (
                meeting.started_at.isoformat() if meeting.started_at else None
            ),
            "ended_at": meeting.ended_at.isoformat() if meeting.ended_at else None,
            "duration_minutes": meeting.duration_minutes,
            "participants": [
                {
                    "team_id": p.team_id,
                    "team_name": p.team_name,
                    "role": p.role,
                    "attended": p.attended,
                    "joined_at": p.joined_at.isoformat() if p.joined_at else None,
                }
                for p in meeting.participants
            ],
            "facilitator": meeting.facilitator,
            "agenda": [
                {
                    "id": a.id,
                    "title": a.title,
                    "description": a.description,
                    "presenter": a.presenter,
                    "time_minutes": a.time_minutes,
                    "status": a.status,
                    "notes": a.notes,
                    "decisions": a.decisions,
                }
                for a in meeting.agenda
            ],
            "auto_generated_agenda": meeting.auto_generated_agenda,
            "action_items": [
                {
                    "id": ai.id,
                    "title": ai.title,
                    "assignee": ai.assignee,
                    "due_date": ai.due_date.isoformat() if ai.due_date else None,
                    "status": ai.status,
                    "notes": ai.notes,
                    "created_at": ai.created_at.isoformat(),
                    "completed_at": (
                        ai.completed_at.isoformat() if ai.completed_at else None
                    ),
                }
                for ai in meeting.action_items
            ],
            "minutes": {
                "summary": meeting.minutes.summary,
                "key_decisions": meeting.minutes.key_decisions,
                "concerns_raised": meeting.minutes.concerns_raised,
                "next_steps": meeting.minutes.next_steps,
                "recorded_by": meeting.minutes.recorded_by,
            },
            "phase": meeting.phase,
            "related_sync_point_id": meeting.related_sync_point_id,
            "related_blocker_ids": meeting.related_blocker_ids,
            "created_at": meeting.created_at.isoformat(),
            "metadata": meeting.metadata,
        }

    def _deserialize_meeting(self, data: Dict[str, Any]) -> Meeting:
        """Deserialize a meeting from dictionary."""
        participants = [
            MeetingParticipant(
                team_id=p["team_id"],
                team_name=p["team_name"],
                role=p.get("role", "attendee"),
                attended=p.get("attended", False),
                joined_at=(
                    datetime.fromisoformat(p["joined_at"]) if p.get("joined_at") else None
                ),
            )
            for p in data.get("participants", [])
        ]

        agenda = [
            AgendaItem(
                id=a["id"],
                title=a["title"],
                description=a.get("description", ""),
                presenter=a.get("presenter"),
                time_minutes=a.get("time_minutes", 5),
                status=a.get("status", "pending"),
                notes=a.get("notes", ""),
                decisions=a.get("decisions", []),
            )
            for a in data.get("agenda", [])
        ]

        action_items = [
            ActionItem(
                id=ai["id"],
                title=ai["title"],
                assignee=ai["assignee"],
                due_date=(
                    datetime.fromisoformat(ai["due_date"]) if ai.get("due_date") else None
                ),
                status=ai.get("status", "pending"),
                notes=ai.get("notes", ""),
                created_at=(
                    datetime.fromisoformat(ai["created_at"])
                    if ai.get("created_at")
                    else datetime.now()
                ),
                completed_at=(
                    datetime.fromisoformat(ai["completed_at"])
                    if ai.get("completed_at")
                    else None
                ),
            )
            for ai in data.get("action_items", [])
        ]

        minutes_data = data.get("minutes", {})
        minutes = MeetingMinutes(
            summary=minutes_data.get("summary", ""),
            key_decisions=minutes_data.get("key_decisions", []),
            concerns_raised=minutes_data.get("concerns_raised", []),
            next_steps=minutes_data.get("next_steps", []),
            recorded_by=minutes_data.get("recorded_by"),
        )

        return Meeting(
            id=data["id"],
            title=data["title"],
            meeting_type=MeetingType(data["meeting_type"]),
            status=MeetingStatus(data.get("status", "scheduled")),
            scheduled_at=(
                datetime.fromisoformat(data["scheduled_at"])
                if data.get("scheduled_at")
                else None
            ),
            started_at=(
                datetime.fromisoformat(data["started_at"])
                if data.get("started_at")
                else None
            ),
            ended_at=(
                datetime.fromisoformat(data["ended_at"])
                if data.get("ended_at")
                else None
            ),
            duration_minutes=data.get("duration_minutes", 30),
            participants=participants,
            facilitator=data.get("facilitator"),
            agenda=agenda,
            auto_generated_agenda=data.get("auto_generated_agenda", True),
            action_items=action_items,
            minutes=minutes,
            phase=data.get("phase", 0),
            related_sync_point_id=data.get("related_sync_point_id"),
            related_blocker_ids=data.get("related_blocker_ids", []),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else datetime.now()
            ),
            metadata=data.get("metadata", {}),
        )

    def _serialize_schedule(self, schedule: MeetingSchedule) -> Dict[str, Any]:
        """Serialize a schedule to dictionary."""
        return {
            "id": schedule.id,
            "meeting_type": schedule.meeting_type.value,
            "recurrence": schedule.recurrence,
            "teams": schedule.teams,
            "default_duration_minutes": schedule.default_duration_minutes,
            "default_agenda_template": schedule.default_agenda_template,
            "enabled": schedule.enabled,
            "next_occurrence": (
                schedule.next_occurrence.isoformat()
                if schedule.next_occurrence
                else None
            ),
        }

    def _deserialize_schedule(self, data: Dict[str, Any]) -> MeetingSchedule:
        """Deserialize a schedule from dictionary."""
        return MeetingSchedule(
            id=data["id"],
            meeting_type=MeetingType(data["meeting_type"]),
            recurrence=data.get("recurrence", "none"),
            teams=data.get("teams", []),
            default_duration_minutes=data.get("default_duration_minutes", 30),
            default_agenda_template=data.get("default_agenda_template", []),
            enabled=data.get("enabled", True),
            next_occurrence=(
                datetime.fromisoformat(data["next_occurrence"])
                if data.get("next_occurrence")
                else None
            ),
        )

    # ==========================================================================
    # Persistence Methods
    # ==========================================================================

    def _load(self) -> None:
        """Load meetings and schedules from disk."""
        # Load meetings
        meetings_file = self.meetings_dir / "meetings.json"
        if meetings_file.exists():
            try:
                with open(meetings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._meetings = {
                        m["id"]: self._deserialize_meeting(m)
                        for m in data.get("meetings", [])
                    }
            except (json.JSONDecodeError, KeyError):
                self._meetings = {}

        # Load schedules
        schedules_file = self.meetings_dir / "schedules.json"
        if schedules_file.exists():
            try:
                with open(schedules_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._schedules = {
                        s["id"]: self._deserialize_schedule(s)
                        for s in data.get("schedules", [])
                    }
            except (json.JSONDecodeError, KeyError):
                self._schedules = {}

    def _save(self) -> None:
        """Save meetings and schedules to disk."""
        # Save meetings
        meetings_file = self.meetings_dir / "meetings.json"
        meetings_data = {
            "meetings": [
                self._serialize_meeting(m) for m in self._meetings.values()
            ]
        }
        with open(meetings_file, "w", encoding="utf-8") as f:
            json.dump(meetings_data, f, indent=2, ensure_ascii=False)

        # Save schedules
        schedules_file = self.meetings_dir / "schedules.json"
        schedules_data = {
            "schedules": [
                self._serialize_schedule(s) for s in self._schedules.values()
            ]
        }
        with open(schedules_file, "w", encoding="utf-8") as f:
            json.dump(schedules_data, f, indent=2, ensure_ascii=False)

    def clear(self) -> None:
        """Clear all meetings and schedules (for testing)."""
        self._meetings = {}
        self._schedules = {}
        self._save()
