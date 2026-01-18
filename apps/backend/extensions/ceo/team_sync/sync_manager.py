"""
Sync Point Manager
==================

Manages creation, participation, and completion of synchronization points.
Provides file-based persistence using JSON storage.
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .models import (
    SyncCondition,
    SyncEvent,
    SyncParticipant,
    SyncPoint,
    SyncStatus,
    SyncType,
)
from .serializer import SyncPointSerializer


class SyncPointManager:
    """
    Sync Point Manager.

    Manages the lifecycle of synchronization points including creation,
    participation tracking, condition checking, and completion.

    Attributes:
        project_path: Root project directory
        sync_dir: Directory for sync point storage
    """

    def __init__(self, project_path: str):
        """
        Initialize the SyncPointManager.

        Args:
            project_path: Root project directory path
        """
        self.project_path = project_path
        self.sync_dir = Path(project_path) / ".planning" / "team_sync" / "sync_points"
        self.sync_dir.mkdir(parents=True, exist_ok=True)

        self._sync_points: Dict[str, SyncPoint] = {}
        self._events: List[SyncEvent] = []
        self._callbacks: Dict[str, Callable] = {}
        self._load()

    # ==========================================================================
    # Creation Methods
    # ==========================================================================

    def create_barrier(
        self,
        name: str,
        teams: List[str],
        phase: int = 0,
        timeout_minutes: Optional[int] = None,
        description: str = "",
    ) -> SyncPoint:
        """
        Create a barrier synchronization point.

        All participating teams must arrive before proceeding.

        Args:
            name: Human-readable name for the sync point
            teams: List of team IDs that must participate
            phase: Associated phase number
            timeout_minutes: Optional timeout in minutes
            description: Detailed description

        Returns:
            Created SyncPoint instance
        """
        sync_point = SyncPoint(
            id=f"sync-{uuid.uuid4().hex[:8]}",
            name=name,
            sync_type=SyncType.BARRIER,
            phase=phase,
            description=description,
            participants=[
                SyncParticipant(team_id=t, team_name=t, role="required")
                for t in teams
            ],
            required_count=len(teams),
            conditions=[SyncCondition("all_arrived")],
        )

        if timeout_minutes:
            sync_point.timeout_at = datetime.now() + timedelta(minutes=timeout_minutes)
            sync_point.conditions.append(SyncCondition("timeout", timeout_minutes))

        self._sync_points[sync_point.id] = sync_point
        self._log_event(sync_point.id, "created")
        self._save()
        return sync_point

    def create_wait(
        self,
        name: str,
        wait_for_teams: List[str],
        waiting_team: str,
        phase: int = 0,
        description: str = "",
    ) -> SyncPoint:
        """
        Create a wait synchronization point.

        One team waits for specific other teams to complete.

        Args:
            name: Human-readable name for the sync point
            wait_for_teams: List of team IDs to wait for
            waiting_team: Team ID that is waiting
            phase: Associated phase number
            description: Detailed description

        Returns:
            Created SyncPoint instance
        """
        participants = [
            SyncParticipant(team_id=t, team_name=t, role="required")
            for t in wait_for_teams
        ]
        participants.append(
            SyncParticipant(team_id=waiting_team, team_name=waiting_team, role="observer")
        )

        sync_point = SyncPoint(
            id=f"sync-{uuid.uuid4().hex[:8]}",
            name=name,
            sync_type=SyncType.WAIT,
            phase=phase,
            description=description,
            participants=participants,
            required_count=len(wait_for_teams),
            conditions=[SyncCondition("specific_teams", wait_for_teams)],
        )

        self._sync_points[sync_point.id] = sync_point
        self._log_event(sync_point.id, "created")
        self._save()
        return sync_point

    def create_gate(
        self,
        name: str,
        approvers: List[str],
        min_approvals: int = 1,
        phase: int = 0,
        description: str = "",
    ) -> SyncPoint:
        """
        Create a gate synchronization point.

        Requires explicit approval from a minimum number of approvers.

        Args:
            name: Human-readable name for the sync point
            approvers: List of team IDs that can approve
            min_approvals: Minimum number of approvals required
            phase: Associated phase number
            description: Detailed description

        Returns:
            Created SyncPoint instance
        """
        sync_point = SyncPoint(
            id=f"sync-{uuid.uuid4().hex[:8]}",
            name=name,
            sync_type=SyncType.GATE,
            phase=phase,
            description=description,
            participants=[
                SyncParticipant(team_id=t, team_name=t, role="required")
                for t in approvers
            ],
            required_count=min_approvals,
            conditions=[SyncCondition("min_count", min_approvals)],
        )

        self._sync_points[sync_point.id] = sync_point
        self._log_event(sync_point.id, "created")
        self._save()
        return sync_point

    def create_signal(
        self,
        name: str,
        sender: str,
        receivers: List[str],
        phase: int = 0,
        description: str = "",
    ) -> SyncPoint:
        """
        Create a signal synchronization point.

        Notification-only sync (non-blocking).

        Args:
            name: Human-readable name for the sync point
            sender: Team ID sending the signal
            receivers: List of team IDs receiving the signal
            phase: Associated phase number
            description: Detailed description

        Returns:
            Created SyncPoint instance
        """
        participants = [
            SyncParticipant(team_id=sender, team_name=sender, role="required")
        ]
        participants.extend([
            SyncParticipant(team_id=r, team_name=r, role="observer")
            for r in receivers
        ])

        sync_point = SyncPoint(
            id=f"sync-{uuid.uuid4().hex[:8]}",
            name=name,
            sync_type=SyncType.SIGNAL,
            phase=phase,
            description=description,
            participants=participants,
            required_count=1,  # Only sender needs to arrive
            conditions=[SyncCondition("specific_teams", [sender])],
        )

        self._sync_points[sync_point.id] = sync_point
        self._log_event(sync_point.id, "created")
        self._save()
        return sync_point

    # ==========================================================================
    # Participation Methods
    # ==========================================================================

    def arrive(
        self,
        sync_point_id: str,
        team_id: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Register team arrival at a sync point.

        Args:
            sync_point_id: ID of the sync point
            team_id: ID of the arriving team
            data: Optional data brought by the team

        Returns:
            Result dictionary with success status and current state
        """
        sync_point = self._sync_points.get(sync_point_id)
        if not sync_point:
            return {"success": False, "error": "Sync point not found"}

        if sync_point.status in (SyncStatus.COMPLETED, SyncStatus.CANCELLED):
            return {"success": False, "error": f"Sync point is {sync_point.status.value}"}

        # Find participant and mark arrived
        found = False
        for participant in sync_point.participants:
            if participant.team_id == team_id:
                participant.arrived = True
                participant.arrived_at = datetime.now()
                participant.data = data or {}
                found = True
                break

        if not found:
            return {"success": False, "error": "Team not in participants"}

        self._log_event(sync_point_id, "participant_arrived", team_id)

        # Check conditions
        self._check_conditions(sync_point)

        self._save()

        return {
            "success": True,
            "status": sync_point.status.value,
            "waiting_for": self._get_waiting_teams(sync_point),
        }

    def check_ready(self, sync_point_id: str) -> bool:
        """
        Check if a sync point is ready.

        Args:
            sync_point_id: ID of the sync point

        Returns:
            True if ready to proceed
        """
        sync_point = self._sync_points.get(sync_point_id)
        if not sync_point:
            return False
        return sync_point.status == SyncStatus.READY

    def complete(self, sync_point_id: str) -> Dict[str, Any]:
        """
        Complete a sync point.

        Merges all participant data and marks as completed.

        Args:
            sync_point_id: ID of the sync point

        Returns:
            Result dictionary with merged data
        """
        sync_point = self._sync_points.get(sync_point_id)
        if not sync_point:
            return {"success": False, "error": "Sync point not found"}

        if sync_point.status != SyncStatus.READY:
            return {"success": False, "error": "Not ready yet"}

        # Merge participant data
        sync_point.result = self._merge_participant_data(sync_point)
        sync_point.status = SyncStatus.COMPLETED
        sync_point.completed_at = datetime.now()

        self._log_event(sync_point_id, "completed")
        self._save()

        # Execute callback if registered
        if sync_point.on_ready_callback and sync_point.on_ready_callback in self._callbacks:
            self._callbacks[sync_point.on_ready_callback](sync_point)

        return {
            "success": True,
            "result": sync_point.result,
        }

    def cancel(self, sync_point_id: str, reason: str = "") -> bool:
        """
        Cancel a sync point.

        Args:
            sync_point_id: ID of the sync point
            reason: Reason for cancellation

        Returns:
            True if cancelled successfully
        """
        sync_point = self._sync_points.get(sync_point_id)
        if not sync_point:
            return False

        if sync_point.status in (SyncStatus.COMPLETED, SyncStatus.CANCELLED):
            return False

        sync_point.status = SyncStatus.CANCELLED
        sync_point.result["cancelled_reason"] = reason
        self._log_event(sync_point_id, "cancelled", details={"reason": reason})
        self._save()
        return True

    # ==========================================================================
    # Query Methods
    # ==========================================================================

    def get(self, sync_point_id: str) -> Optional[SyncPoint]:
        """
        Get a sync point by ID.

        Args:
            sync_point_id: ID of the sync point

        Returns:
            SyncPoint instance or None
        """
        return self._sync_points.get(sync_point_id)

    def list_active(self, phase: Optional[int] = None) -> List[SyncPoint]:
        """
        List active sync points.

        Args:
            phase: Optional filter by phase

        Returns:
            List of active SyncPoint instances
        """
        result = [
            sp for sp in self._sync_points.values()
            if sp.status in (SyncStatus.PENDING, SyncStatus.WAITING)
        ]
        if phase is not None:
            result = [sp for sp in result if sp.phase == phase]
        return result

    def list_ready(self) -> List[SyncPoint]:
        """
        List sync points that are ready.

        Returns:
            List of ready SyncPoint instances
        """
        return [
            sp for sp in self._sync_points.values()
            if sp.status == SyncStatus.READY
        ]

    def list_by_team(self, team_id: str) -> List[SyncPoint]:
        """
        List all sync points for a team.

        Args:
            team_id: Team ID to filter by

        Returns:
            List of SyncPoint instances involving the team
        """
        return [
            sp for sp in self._sync_points.values()
            if any(p.team_id == team_id for p in sp.participants)
        ]

    def list_waiting_for_team(self, team_id: str) -> List[SyncPoint]:
        """
        List sync points waiting for a specific team.

        Args:
            team_id: Team ID

        Returns:
            List of SyncPoint instances waiting for the team
        """
        return [
            sp for sp in self._sync_points.values()
            if sp.status in (SyncStatus.PENDING, SyncStatus.WAITING)
            and any(
                p.team_id == team_id and not p.arrived and p.role == "required"
                for p in sp.participants
            )
        ]

    def get_events(self, sync_point_id: str) -> List[SyncEvent]:
        """
        Get events for a sync point.

        Args:
            sync_point_id: ID of the sync point

        Returns:
            List of SyncEvent instances
        """
        return [e for e in self._events if e.sync_point_id == sync_point_id]

    def get_all_events(self) -> List[SyncEvent]:
        """
        Get all events.

        Returns:
            List of all SyncEvent instances
        """
        return list(self._events)

    # ==========================================================================
    # Callback Management
    # ==========================================================================

    def register_callback(self, name: str, callback: Callable) -> None:
        """
        Register a callback function.

        Args:
            name: Callback name (referenced in SyncPoint)
            callback: Callable to execute
        """
        self._callbacks[name] = callback

    def unregister_callback(self, name: str) -> bool:
        """
        Unregister a callback function.

        Args:
            name: Callback name to remove

        Returns:
            True if removed successfully
        """
        if name in self._callbacks:
            del self._callbacks[name]
            return True
        return False

    # ==========================================================================
    # Internal Methods
    # ==========================================================================

    def _check_conditions(self, sync_point: SyncPoint) -> None:
        """
        Check if all conditions are met.

        Args:
            sync_point: SyncPoint to check
        """
        all_met = True

        for condition in sync_point.conditions:
            if condition.condition_type == "all_arrived":
                required = [p for p in sync_point.participants if p.role == "required"]
                condition.met = all(p.arrived for p in required)

            elif condition.condition_type == "min_count":
                arrived_count = sum(
                    1 for p in sync_point.participants
                    if p.arrived and p.role == "required"
                )
                condition.met = arrived_count >= condition.value

            elif condition.condition_type == "specific_teams":
                condition.met = all(
                    any(p.team_id == t and p.arrived for p in sync_point.participants)
                    for t in condition.value
                )

            elif condition.condition_type == "timeout":
                if sync_point.timeout_at and datetime.now() > sync_point.timeout_at:
                    sync_point.status = SyncStatus.TIMEOUT
                    self._log_event(sync_point.id, "timeout")
                    # Execute timeout callback if registered
                    if (
                        sync_point.on_timeout_callback
                        and sync_point.on_timeout_callback in self._callbacks
                    ):
                        self._callbacks[sync_point.on_timeout_callback](sync_point)
                    return

            if condition.met and not condition.met_at:
                condition.met_at = datetime.now()
                self._log_event(
                    sync_point.id,
                    "condition_met",
                    details={"type": condition.condition_type},
                )

            if not condition.met and condition.condition_type != "timeout":
                all_met = False

        if all_met:
            sync_point.status = SyncStatus.READY
        elif any(p.arrived for p in sync_point.participants):
            sync_point.status = SyncStatus.WAITING

    def _get_waiting_teams(self, sync_point: SyncPoint) -> List[str]:
        """
        Get list of teams that haven't arrived yet.

        Args:
            sync_point: SyncPoint to check

        Returns:
            List of team IDs
        """
        return [
            p.team_id for p in sync_point.participants
            if p.role == "required" and not p.arrived
        ]

    def _merge_participant_data(self, sync_point: SyncPoint) -> Dict[str, Any]:
        """
        Merge data from all participants.

        Args:
            sync_point: SyncPoint with participant data

        Returns:
            Merged dictionary with team_id as keys
        """
        merged = {}
        for participant in sync_point.participants:
            if participant.data:
                merged[participant.team_id] = participant.data
        return merged

    def _log_event(
        self,
        sync_point_id: str,
        event_type: str,
        team_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a sync point event.

        Args:
            sync_point_id: ID of the sync point
            event_type: Type of event
            team_id: Optional associated team
            details: Optional event details
        """
        event = SyncEvent(
            id=f"evt-{uuid.uuid4().hex[:8]}",
            sync_point_id=sync_point_id,
            event_type=event_type,
            timestamp=datetime.now(),
            team_id=team_id,
            details=details or {},
        )
        self._events.append(event)

    # ==========================================================================
    # Persistence Methods
    # ==========================================================================

    def _load(self) -> None:
        """Load sync points and events from disk."""
        # Load sync points
        sync_points_file = self.sync_dir / "sync_points.json"
        if sync_points_file.exists():
            try:
                with open(sync_points_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._sync_points = {
                        sp["id"]: SyncPointSerializer.sync_point_from_dict(sp)
                        for sp in data.get("sync_points", [])
                    }
            except (json.JSONDecodeError, KeyError) as e:
                # Log error but continue with empty state
                self._sync_points = {}

        # Load events
        events_file = self.sync_dir / "events.json"
        if events_file.exists():
            try:
                with open(events_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._events = SyncPointSerializer.events_from_dict(
                        data.get("events", [])
                    )
            except (json.JSONDecodeError, KeyError):
                self._events = []

    def _save(self) -> None:
        """Save sync points and events to disk."""
        # Save sync points
        sync_points_file = self.sync_dir / "sync_points.json"
        sync_points_data = {
            "sync_points": SyncPointSerializer.sync_points_to_dict(
                list(self._sync_points.values())
            )
        }
        with open(sync_points_file, "w", encoding="utf-8") as f:
            json.dump(sync_points_data, f, indent=2, ensure_ascii=False)

        # Save events
        events_file = self.sync_dir / "events.json"
        events_data = {
            "events": SyncPointSerializer.events_to_dict(self._events)
        }
        with open(events_file, "w", encoding="utf-8") as f:
            json.dump(events_data, f, indent=2, ensure_ascii=False)

    def clear(self) -> None:
        """Clear all sync points and events (for testing)."""
        self._sync_points = {}
        self._events = []
        self._save()
