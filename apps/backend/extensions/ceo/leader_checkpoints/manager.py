"""
Checkpoint Manager
==================

Manages the lifecycle of checkpoints including creation, storage,
retrieval, and cleanup of LeaderContext snapshots.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..leader_context.serializer import LeaderContextSerializer
from ..leader_context.service import LeaderContextService
from .models import Checkpoint, CheckpointConfig, CheckpointTrigger
from .serializer import CheckpointSerializer


class CheckpointManager:
    """
    Manages checkpoint creation and lifecycle.

    Creates checkpoints based on configured triggers, stores them to disk,
    and provides retrieval and restoration functionality.

    Attributes:
        project_path: Path to the project root
        config: CheckpointConfig instance
        checkpoint_dir: Directory where checkpoints are stored
        context_service: LeaderContextService for context access
    """

    def __init__(self, project_path: str, config: Optional[CheckpointConfig] = None):
        """
        Initialize CheckpointManager.

        Args:
            project_path: Path to the project root directory
            config: Optional CheckpointConfig (uses defaults if not provided)
        """
        self.project_path = project_path
        self.config = config or CheckpointConfig()
        self.checkpoint_dir = Path(project_path) / ".planning" / "leader_context" / "checkpoints"
        self.context_service = LeaderContextService(project_path)

        # Cumulative counters
        self._subtask_count = 0
        self._error_count = 0
        self._decision_count = 0
        self._periodic_counter = 0

        # Ensure checkpoint directory exists
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # ==========================================================================
    # Checkpoint Creation
    # ==========================================================================

    def should_create_checkpoint(self, trigger: CheckpointTrigger) -> bool:
        """
        Determine if a checkpoint should be created for the given trigger.

        Args:
            trigger: The checkpoint trigger type

        Returns:
            True if checkpoint should be created
        """
        if not self.config.enabled:
            return False

        if trigger == CheckpointTrigger.PERIODIC:
            return self._periodic_counter >= self.config.periodic_interval
        elif trigger == CheckpointTrigger.SUBTASK_COMPLETE:
            return self.config.on_subtask_complete
        elif trigger == CheckpointTrigger.ERROR_OCCURRED:
            return self.config.on_error
        elif trigger == CheckpointTrigger.DECISION_MADE:
            return self.config.on_decision
        else:
            # EXPLICIT, PHASE_START, PHASE_END always create checkpoints
            return True

    def create_checkpoint(
        self,
        trigger: CheckpointTrigger,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[Checkpoint]:
        """
        Create a checkpoint snapshot.

        Args:
            trigger: What triggered this checkpoint
            details: Additional trigger-specific information

        Returns:
            Created Checkpoint or None if checkpoint was not created
        """
        if not self.should_create_checkpoint(trigger):
            return None

        # Get or load context
        context = self.context_service.context
        if context is None:
            self.context_service.load()
            context = self.context_service.context

        # Create checkpoint
        checkpoint = Checkpoint(
            id=f"cp-{uuid.uuid4().hex[:8]}",
            phase=context.phase if context else 0,
            trigger=trigger,
            timestamp=datetime.now(),
            context_snapshot=LeaderContextSerializer.to_dict(context) if context else {},
            trigger_details=details or {},
            subtask_count=self._subtask_count,
            error_count=self._error_count,
            decision_count=self._decision_count,
        )

        # Save checkpoint
        self._save_checkpoint(checkpoint)

        # Reset periodic counter after checkpoint creation
        self._reset_periodic_counter()

        # Cleanup old checkpoints if configured
        if self.config.auto_cleanup:
            self._cleanup_old_checkpoints()

        return checkpoint

    # ==========================================================================
    # Trigger Handlers
    # ==========================================================================

    def on_subtask_complete(
        self,
        subtask_id: str,
        result: str = "success"
    ) -> Optional[Checkpoint]:
        """
        Handle subtask completion event.

        Args:
            subtask_id: ID of the completed subtask
            result: Result status (e.g., "success", "partial")

        Returns:
            Created Checkpoint or None
        """
        self._subtask_count += 1
        self._periodic_counter += 1

        return self.create_checkpoint(
            CheckpointTrigger.SUBTASK_COMPLETE,
            {"subtask_id": subtask_id, "result": result}
        )

    def on_error(
        self,
        error_message: str,
        error_type: str = "unknown"
    ) -> Optional[Checkpoint]:
        """
        Handle error occurrence event.

        Args:
            error_message: Description of the error
            error_type: Type/category of the error

        Returns:
            Created Checkpoint or None
        """
        self._error_count += 1

        return self.create_checkpoint(
            CheckpointTrigger.ERROR_OCCURRED,
            {"error_message": error_message, "error_type": error_type}
        )

    def on_decision(
        self,
        decision_id: str,
        description: str
    ) -> Optional[Checkpoint]:
        """
        Handle decision recording event.

        Args:
            decision_id: ID of the decision
            description: Description of what was decided

        Returns:
            Created Checkpoint or None
        """
        self._decision_count += 1

        return self.create_checkpoint(
            CheckpointTrigger.DECISION_MADE,
            {"decision_id": decision_id, "description": description}
        )

    def check_periodic(self) -> Optional[Checkpoint]:
        """
        Check if a periodic checkpoint should be created.

        Called periodically to create checkpoints based on operation count.

        Returns:
            Created Checkpoint or None
        """
        if self._periodic_counter >= self.config.periodic_interval:
            return self.create_checkpoint(CheckpointTrigger.PERIODIC)
        return None

    def on_phase_start(self, phase: int) -> Optional[Checkpoint]:
        """
        Handle phase start event.

        Args:
            phase: Phase number that is starting

        Returns:
            Created Checkpoint or None
        """
        return self.create_checkpoint(
            CheckpointTrigger.PHASE_START,
            {"phase": phase}
        )

    def on_phase_end(self, phase: int) -> Optional[Checkpoint]:
        """
        Handle phase end event.

        Args:
            phase: Phase number that is ending

        Returns:
            Created Checkpoint or None
        """
        return self.create_checkpoint(
            CheckpointTrigger.PHASE_END,
            {"phase": phase}
        )

    def create_explicit_checkpoint(
        self,
        reason: str = ""
    ) -> Optional[Checkpoint]:
        """
        Create an explicit/manual checkpoint.

        Args:
            reason: Optional reason for creating checkpoint

        Returns:
            Created Checkpoint or None
        """
        return self.create_checkpoint(
            CheckpointTrigger.EXPLICIT,
            {"reason": reason} if reason else {}
        )

    # ==========================================================================
    # Checkpoint Retrieval
    # ==========================================================================

    def list_checkpoints(self, phase: Optional[int] = None) -> List[Checkpoint]:
        """
        List all checkpoints, optionally filtered by phase.

        Args:
            phase: Optional phase number to filter by

        Returns:
            List of Checkpoint objects sorted by timestamp (newest first)
        """
        checkpoints = []

        if not self.checkpoint_dir.exists():
            return checkpoints

        for file_path in self.checkpoint_dir.glob("checkpoint_*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                checkpoint = CheckpointSerializer.from_dict(data)

                if phase is None or checkpoint.phase == phase:
                    checkpoints.append(checkpoint)
            except (json.JSONDecodeError, KeyError, ValueError):
                # Skip invalid checkpoint files
                continue

        # Sort by timestamp, newest first
        checkpoints.sort(key=lambda cp: cp.timestamp, reverse=True)
        return checkpoints

    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """
        Get a specific checkpoint by ID.

        Args:
            checkpoint_id: The checkpoint ID to retrieve

        Returns:
            Checkpoint if found, None otherwise
        """
        if not self.checkpoint_dir.exists():
            return None

        for file_path in self.checkpoint_dir.glob("checkpoint_*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if data.get('id') == checkpoint_id:
                    return CheckpointSerializer.from_dict(data)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

        return None

    def get_latest_checkpoint(self, phase: Optional[int] = None) -> Optional[Checkpoint]:
        """
        Get the most recent checkpoint.

        Args:
            phase: Optional phase number to filter by

        Returns:
            Most recent Checkpoint or None
        """
        checkpoints = self.list_checkpoints(phase)
        return checkpoints[0] if checkpoints else None

    # ==========================================================================
    # Checkpoint Restoration
    # ==========================================================================

    def restore_from_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Restore LeaderContext from a checkpoint.

        Loads the context snapshot from the checkpoint and saves it
        as the current context.

        Args:
            checkpoint_id: ID of the checkpoint to restore from

        Returns:
            True if restoration was successful
        """
        checkpoint = self.get_checkpoint(checkpoint_id)
        if checkpoint is None:
            return False

        if not checkpoint.context_snapshot:
            return False

        # Restore context from snapshot
        context = LeaderContextSerializer.from_dict(checkpoint.context_snapshot)
        self.context_service._context = context
        self.context_service._query = None

        # Save restored context
        success = self.context_service.save()

        if success:
            # Restore counters from checkpoint
            self._subtask_count = checkpoint.subtask_count
            self._error_count = checkpoint.error_count
            self._decision_count = checkpoint.decision_count
            self._periodic_counter = 0

        return success

    # ==========================================================================
    # Internal Methods
    # ==========================================================================

    def _save_checkpoint(self, checkpoint: Checkpoint) -> None:
        """
        Save a checkpoint to disk.

        Args:
            checkpoint: Checkpoint to save
        """
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Create filename with phase and timestamp for easy sorting
        timestamp_str = checkpoint.timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"checkpoint_{checkpoint.phase:02d}_{timestamp_str}_{checkpoint.id}.json"
        file_path = self.checkpoint_dir / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(
                CheckpointSerializer.to_dict(checkpoint),
                f,
                indent=2,
                ensure_ascii=False
            )

    def _cleanup_old_checkpoints(self) -> None:
        """
        Remove old checkpoints beyond the configured maximum.

        Keeps the most recent checkpoints up to max_checkpoints.
        """
        if not self.checkpoint_dir.exists():
            return

        # Get all checkpoint files sorted by modification time
        checkpoint_files = sorted(
            self.checkpoint_dir.glob("checkpoint_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        # Remove files beyond the limit
        for file_path in checkpoint_files[self.config.max_checkpoints:]:
            try:
                file_path.unlink()
            except OSError:
                # Ignore errors during cleanup
                pass

    def _reset_periodic_counter(self) -> None:
        """Reset the periodic checkpoint counter."""
        self._periodic_counter = 0

    # ==========================================================================
    # Statistics
    # ==========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """
        Get checkpoint statistics.

        Returns:
            Dictionary containing checkpoint statistics
        """
        checkpoints = self.list_checkpoints()

        trigger_counts = {}
        for cp in checkpoints:
            trigger_name = cp.trigger.value
            trigger_counts[trigger_name] = trigger_counts.get(trigger_name, 0) + 1

        return {
            "total_checkpoints": len(checkpoints),
            "trigger_counts": trigger_counts,
            "subtask_count": self._subtask_count,
            "error_count": self._error_count,
            "decision_count": self._decision_count,
            "periodic_counter": self._periodic_counter,
            "config": {
                "enabled": self.config.enabled,
                "periodic_interval": self.config.periodic_interval,
                "max_checkpoints": self.config.max_checkpoints,
            }
        }
