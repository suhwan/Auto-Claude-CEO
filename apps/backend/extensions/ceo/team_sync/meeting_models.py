"""
Meeting Models
==============

Data models for Leader Meeting automation system.

This module provides:
- MeetingType: Types of meetings (standup, sync, escalation, review, etc.)
- MeetingStatus: Meeting lifecycle states
- AgendaItem: Agenda items with discussion tracking
- ActionItem: Action items with assignee and due date
- MeetingParticipant: Meeting participants with attendance tracking
- MeetingMinutes: Meeting notes and decisions
- Meeting: Complete meeting entity
- MeetingSchedule: Recurring meeting schedules
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MeetingType(Enum):
    """Meeting types."""

    STANDUP = "standup"  # Daily status sharing
    SYNC = "sync"  # Regular synchronization
    ESCALATION = "escalation"  # Blocker resolution
    REVIEW = "review"  # Phase review
    KICKOFF = "kickoff"  # Phase start
    RETROSPECTIVE = "retro"  # Retrospective


class MeetingStatus(Enum):
    """Meeting lifecycle status."""

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class AgendaItem:
    """Agenda item for a meeting."""

    id: str
    title: str
    description: str = ""
    presenter: Optional[str] = None
    time_minutes: int = 5
    status: str = "pending"  # pending, discussed, skipped
    notes: str = ""
    decisions: List[str] = field(default_factory=list)


@dataclass
class ActionItem:
    """Action item created during a meeting."""

    id: str
    title: str
    assignee: str
    due_date: Optional[datetime] = None
    status: str = "pending"  # pending, in_progress, completed
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class MeetingParticipant:
    """Meeting participant with attendance tracking."""

    team_id: str
    team_name: str
    role: str = "attendee"  # facilitator, attendee, optional
    attended: bool = False
    joined_at: Optional[datetime] = None


@dataclass
class MeetingMinutes:
    """Meeting minutes and decisions."""

    summary: str = ""
    key_decisions: List[str] = field(default_factory=list)
    concerns_raised: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    recorded_by: Optional[str] = None


@dataclass
class Meeting:
    """Complete meeting entity."""

    id: str
    title: str
    meeting_type: MeetingType
    status: MeetingStatus = MeetingStatus.SCHEDULED

    # Schedule
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_minutes: int = 30

    # Participants
    participants: List[MeetingParticipant] = field(default_factory=list)
    facilitator: Optional[str] = None

    # Agenda
    agenda: List[AgendaItem] = field(default_factory=list)
    auto_generated_agenda: bool = True

    # Results
    action_items: List[ActionItem] = field(default_factory=list)
    minutes: MeetingMinutes = field(default_factory=MeetingMinutes)

    # Context
    phase: int = 0
    related_sync_point_id: Optional[str] = None
    related_blocker_ids: List[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MeetingSchedule:
    """Recurring meeting schedule."""

    id: str
    meeting_type: MeetingType
    recurrence: str = "none"  # none, daily, weekly, phase_start, phase_end
    teams: List[str] = field(default_factory=list)
    default_duration_minutes: int = 30
    default_agenda_template: List[str] = field(default_factory=list)
    enabled: bool = True
    next_occurrence: Optional[datetime] = None
