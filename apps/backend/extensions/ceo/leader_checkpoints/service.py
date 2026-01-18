"""
Leader Checkpoint Service
=========================

Unified service integrating checkpoints, error logging, and reviews.
Provides a single entry point for all checkpoint-related operations.
"""

from typing import Any, Dict, Optional

from ..leader_context.service import LeaderContextService
from .error_logger import ErrorLogger
from .error_models import ErrorCategory, ErrorContext, ErrorSeverity
from .manager import CheckpointManager
from .models import Checkpoint, CheckpointConfig, CheckpointTrigger
from .review_generator import ReviewGenerator


class LeaderCheckpointService:
    """
    Unified leader checkpoint service.

    Integrates CheckpointManager, ErrorLogger, and ReviewGenerator to provide
    a single API for checkpoint operations, error logging, and review generation.

    Attributes:
        project_path: Path to the project root
        phase: Current phase number
        context_service: LeaderContextService instance
        checkpoint_manager: CheckpointManager instance
        error_logger: ErrorLogger instance
        review_generator: ReviewGenerator instance
    """

    def __init__(
        self,
        project_path: str,
        phase: int,
        config: Optional[CheckpointConfig] = None,
    ):
        """
        Initialize LeaderCheckpointService.

        Args:
            project_path: Path to the project root
            phase: Current phase number
            config: Optional checkpoint configuration
        """
        self.project_path = project_path
        self.phase = phase

        # Initialize context service
        self.context_service = LeaderContextService(project_path)
        self.context_service.load_or_create(phase)

        # Initialize checkpoint manager
        self.checkpoint_manager = CheckpointManager(project_path, config)

        # Initialize error logger
        self.error_logger = ErrorLogger(project_path, phase)

        # Initialize review generator
        self.review_generator = ReviewGenerator(
            project_path,
            self.checkpoint_manager,
            self.error_logger,
            self.context_service,
        )

    # ==========================================================================
    # Phase Lifecycle
    # ==========================================================================

    def start_phase(self) -> Optional[Checkpoint]:
        """
        Start a phase and create initial checkpoint.

        Returns:
            Created Checkpoint or None
        """
        return self.checkpoint_manager.create_checkpoint(
            CheckpointTrigger.PHASE_START,
            {"phase": self.phase},
        )

    def end_phase(self) -> Dict[str, Any]:
        """
        End a phase with final checkpoint and summary review.

        Returns:
            Dictionary containing:
            - checkpoint: Final checkpoint
            - review: Phase summary review
            - error_summary: Error statistics
            - improvement_summary: Learning point statistics
        """
        # Create end checkpoint
        checkpoint = self.checkpoint_manager.create_checkpoint(
            CheckpointTrigger.PHASE_END,
            {"phase": self.phase},
        )

        # Generate phase review
        review = self.review_generator.review_phase(self.phase)

        # Save context
        self.context_service.save()

        return {
            "checkpoint": checkpoint,
            "review": review,
            "error_summary": self.error_logger.get_error_summary(),
            "improvement_summary": self.review_generator.get_improvement_summary(),
        }

    # ==========================================================================
    # Subtask Operations
    # ==========================================================================

    def complete_subtask(
        self,
        subtask_id: str,
        description: str,
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Handle subtask completion with checkpoint and review.

        Args:
            subtask_id: ID of the completed subtask
            description: Description of the subtask
            result: Result data from the subtask execution

        Returns:
            Dictionary containing:
            - checkpoint: Created checkpoint (if any)
            - review: Generated review
        """
        # Create checkpoint
        checkpoint = self.checkpoint_manager.on_subtask_complete(
            subtask_id,
            "success",
        )

        # Generate review
        review = self.review_generator.review_subtask(
            subtask_id,
            description,
            result,
            checkpoint.id if checkpoint else None,
        )

        return {
            "checkpoint": checkpoint,
            "review": review,
        }

    # ==========================================================================
    # Error Operations
    # ==========================================================================

    def log_error(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        stack_trace: Optional[str] = None,
        context: Optional[ErrorContext] = None,
    ) -> Dict[str, Any]:
        """
        Log an error with checkpoint creation.

        Args:
            message: Error message description
            severity: Error severity level
            category: Error category type
            stack_trace: Full stack trace if available
            context: Execution context when error occurred

        Returns:
            Dictionary containing:
            - checkpoint: Created checkpoint (if any)
            - error: Logged error entry
        """
        # Create checkpoint
        checkpoint = self.checkpoint_manager.on_error(
            message,
            category.value,
        )

        # Log error
        error = self.error_logger.log_error(
            message,
            severity,
            category,
            stack_trace,
            context,
            checkpoint.id if checkpoint else None,
        )

        return {
            "checkpoint": checkpoint,
            "error": error,
        }

    def resolve_error(self, error_id: str, resolution: str) -> Dict[str, Any]:
        """
        Resolve an error and generate lessons learned review.

        Args:
            error_id: ID of the error to resolve
            resolution: Description of how the error was fixed

        Returns:
            Dictionary containing:
            - success: Whether the error was resolved
            - review: Lessons learned review (if error found)
        """
        # Mark error as resolved
        success = self.error_logger.resolve_error(error_id, resolution)

        if not success:
            return {"success": False, "review": None}

        # Generate lessons learned review
        review = self.review_generator.review_error_resolution(error_id, resolution)

        return {
            "success": True,
            "review": review,
        }

    # ==========================================================================
    # Decision Operations
    # ==========================================================================

    def record_decision(
        self,
        description: str,
        rationale: str,
    ) -> Dict[str, Any]:
        """
        Record a decision with checkpoint creation.

        Args:
            description: What was decided
            rationale: Why this decision was made

        Returns:
            Dictionary containing:
            - decision: Created decision
            - checkpoint: Created checkpoint (if any)
        """
        # Add decision to context
        decision = self.context_service.add_decision(description, rationale)

        # Create checkpoint
        checkpoint = self.checkpoint_manager.on_decision(
            decision.id,
            description,
        )

        return {
            "decision": decision,
            "checkpoint": checkpoint,
        }

    def review_decision(
        self,
        decision_id: str,
        description: str,
        rationale: str,
        outcome: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create retrospective review for a decision.

        Args:
            decision_id: ID of the decision
            description: What was decided
            rationale: Why this decision was made
            outcome: Optional outcome description

        Returns:
            Dictionary containing:
            - review: Decision review
        """
        review = self.review_generator.review_decision(
            decision_id,
            description,
            rationale,
            outcome,
        )

        return {"review": review}

    # ==========================================================================
    # Status and Queries
    # ==========================================================================

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of checkpoint system.

        Returns:
            Dictionary containing:
            - phase: Current phase number
            - checkpoints: Number of checkpoints for this phase
            - errors: Error summary statistics
            - reviews: Number of reviews for this phase
            - learning_points: Number of learning points
        """
        return {
            "phase": self.phase,
            "checkpoints": len(self.checkpoint_manager.list_checkpoints(self.phase)),
            "errors": self.error_logger.get_error_summary(),
            "reviews": len(self.review_generator.get_reviews(self.phase)),
            "learning_points": len(self.review_generator.get_all_learning_points()),
            "checkpoint_stats": self.checkpoint_manager.get_stats(),
        }

    def get_latest_checkpoint(self) -> Optional[Checkpoint]:
        """
        Get the most recent checkpoint.

        Returns:
            Latest Checkpoint or None
        """
        return self.checkpoint_manager.get_latest_checkpoint(self.phase)

    def get_unresolved_errors(self):
        """
        Get all unresolved errors.

        Returns:
            List of unresolved error logs
        """
        return self.error_logger.get_unresolved_errors()

    def get_learning_points(self, applied_only: bool = False):
        """
        Get all learning points.

        Args:
            applied_only: If True, only return applied learning points

        Returns:
            List of learning points
        """
        return self.review_generator.get_all_learning_points(applied_only)

    def get_improvement_summary(self) -> Dict[str, Any]:
        """
        Get improvement and learning summary.

        Returns:
            Dictionary with improvement statistics
        """
        return self.review_generator.get_improvement_summary()

    # ==========================================================================
    # Checkpoint Restoration
    # ==========================================================================

    def restore_from_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Restore context from a checkpoint.

        Args:
            checkpoint_id: ID of the checkpoint to restore from

        Returns:
            True if restoration was successful
        """
        return self.checkpoint_manager.restore_from_checkpoint(checkpoint_id)

    def create_explicit_checkpoint(self, reason: str = "") -> Optional[Checkpoint]:
        """
        Create an explicit/manual checkpoint.

        Args:
            reason: Optional reason for creating checkpoint

        Returns:
            Created Checkpoint or None
        """
        return self.checkpoint_manager.create_explicit_checkpoint(reason)
