"""
Leader Context Service
======================

Provides a unified service interface for managing LeaderContext.
Combines storage, query, and initialization functionality into
a single easy-to-use API.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from .initializer import ContextInitializer
from .models import (
    Decision,
    Dependency,
    FileMapping,
    Goal,
    LeaderContext,
    Mistake,
    Pattern,
    Risk,
)
from .query import ContextQuery
from .storage import ContextStorage


class LeaderContextService:
    """
    Unified service for LeaderContext management.

    Provides a high-level API for:
    - Loading and saving context
    - Querying context data
    - Adding and updating context items
    - Managing goals, decisions, patterns, mistakes, risks, and files

    Attributes:
        project_path: Path to the project root directory
        storage: ContextStorage instance for persistence
    """

    def __init__(self, project_path: str):
        """
        Initialize LeaderContextService.

        Args:
            project_path: Path to the project root directory
        """
        self.project_path = project_path
        self.storage = ContextStorage(project_path)
        self._context: Optional[LeaderContext] = None
        self._query: Optional[ContextQuery] = None

    # ==========================================================================
    # Properties
    # ==========================================================================

    @property
    def context(self) -> Optional[LeaderContext]:
        """
        Get the currently loaded context.

        Returns:
            LeaderContext if loaded, None otherwise
        """
        return self._context

    @property
    def query(self) -> Optional[ContextQuery]:
        """
        Get the query interface for the loaded context.

        Lazily creates the ContextQuery instance when first accessed.

        Returns:
            ContextQuery if context is loaded, None otherwise
        """
        if self._context and not self._query:
            self._query = ContextQuery(self._context)
        return self._query

    # ==========================================================================
    # Core Operations
    # ==========================================================================

    def load(self, phase: Optional[int] = None) -> bool:
        """
        Load context from storage.

        Args:
            phase: Specific phase to load, or None for latest

        Returns:
            True if context was loaded successfully
        """
        self._context = self.storage.load(phase)
        self._query = None  # Reset query instance
        return self._context is not None

    def load_or_create(self, phase: int) -> LeaderContext:
        """
        Load context or create a new empty context.

        Args:
            phase: Phase number to load or create

        Returns:
            LeaderContext instance (loaded or newly created)
        """
        if not self.load(phase):
            self._context = ContextInitializer.create_empty(
                project_id=Path(self.project_path).name,
                phase=phase
            )
            self._query = None
        return self._context

    def save(self) -> bool:
        """
        Save the current context to storage.

        Returns:
            True if save was successful
        """
        if self._context:
            return self.storage.save(self._context)
        return False

    def create_from_project(self, project_md_path: str) -> LeaderContext:
        """
        Create context from PROJECT.md file.

        Args:
            project_md_path: Path to PROJECT.md

        Returns:
            LeaderContext initialized from PROJECT.md
        """
        self._context = ContextInitializer.from_project_md(project_md_path)
        self._query = None
        return self._context

    def create_from_state(self, state_md_path: str) -> LeaderContext:
        """
        Create context from STATE.md file.

        Args:
            state_md_path: Path to STATE.md

        Returns:
            LeaderContext initialized from STATE.md
        """
        self._context = ContextInitializer.from_state_md(state_md_path)
        self._query = None
        return self._context

    def inherit_from_phase(self, previous_phase: int) -> LeaderContext:
        """
        Create new context by inheriting from previous phase.

        Args:
            previous_phase: Phase number to inherit from

        Returns:
            LeaderContext with inherited data

        Raises:
            ValueError: If previous phase context not found
        """
        self._context = ContextInitializer.inherit_from_phase(
            self.storage, previous_phase
        )
        self._query = None
        return self._context

    # ==========================================================================
    # Goal Management
    # ==========================================================================

    def add_goal(
        self,
        description: str,
        priority: int = 3,
        status: str = 'active'
    ) -> Goal:
        """
        Add a new goal to the context.

        Args:
            description: Goal description
            priority: Priority level (1-5, where 1 is highest)
            status: Initial status ('active', 'deferred')

        Returns:
            The newly created Goal

        Raises:
            ValueError: If no context is loaded
        """
        self._ensure_context_loaded()

        goal = Goal(
            id=f"goal-{uuid.uuid4().hex[:8]}",
            description=description,
            priority=priority,
            status=status,
            created_at=datetime.now(),
        )
        self._context.goals.append(goal)
        self._update_timestamp()
        return goal

    def complete_goal(self, goal_id: str) -> bool:
        """
        Mark a goal as completed.

        Args:
            goal_id: The goal ID to complete

        Returns:
            True if goal was found and completed
        """
        self._ensure_context_loaded()

        for goal in self._context.goals:
            if goal.id == goal_id:
                goal.status = 'completed'
                goal.completed_at = datetime.now()
                self._update_timestamp()
                return True
        return False

    def defer_goal(self, goal_id: str) -> bool:
        """
        Mark a goal as deferred.

        Args:
            goal_id: The goal ID to defer

        Returns:
            True if goal was found and deferred
        """
        self._ensure_context_loaded()

        for goal in self._context.goals:
            if goal.id == goal_id:
                goal.status = 'deferred'
                self._update_timestamp()
                return True
        return False

    def update_goal_priority(self, goal_id: str, priority: int) -> bool:
        """
        Update a goal's priority.

        Args:
            goal_id: The goal ID to update
            priority: New priority level (1-5)

        Returns:
            True if goal was found and updated
        """
        self._ensure_context_loaded()

        for goal in self._context.goals:
            if goal.id == goal_id:
                goal.priority = priority
                self._update_timestamp()
                return True
        return False

    # ==========================================================================
    # Decision Management
    # ==========================================================================

    def add_decision(
        self,
        description: str,
        rationale: str,
        related_goals: Optional[List[str]] = None
    ) -> Decision:
        """
        Add a new decision to the context.

        Args:
            description: What was decided
            rationale: Why this decision was made
            related_goals: List of related goal IDs

        Returns:
            The newly created Decision

        Raises:
            ValueError: If no context is loaded
        """
        self._ensure_context_loaded()

        decision = Decision(
            id=f"dec-{uuid.uuid4().hex[:8]}",
            description=description,
            rationale=rationale,
            made_at=datetime.now(),
            related_goals=related_goals or [],
        )
        self._context.decisions.append(decision)
        self._update_timestamp()
        return decision

    # ==========================================================================
    # Pattern Management
    # ==========================================================================

    def record_pattern(self, name: str, description: str) -> Pattern:
        """
        Record a pattern (creates or updates frequency).

        If a pattern with the same name exists, its frequency is incremented.
        Otherwise, a new pattern is created.

        Args:
            name: Short name for the pattern
            description: Detailed description

        Returns:
            The Pattern (existing or new)

        Raises:
            ValueError: If no context is loaded
        """
        self._ensure_context_loaded()

        # Check for existing pattern with same name
        for pattern in self._context.patterns:
            if pattern.name == name:
                pattern.frequency += 1
                pattern.last_seen = datetime.now()
                self._update_timestamp()
                return pattern

        # Create new pattern
        pattern = Pattern(
            id=f"pat-{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            frequency=1,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
        )
        self._context.patterns.append(pattern)
        self._update_timestamp()
        return pattern

    # ==========================================================================
    # Mistake Management
    # ==========================================================================

    def record_mistake(
        self,
        description: str,
        impact: str = 'medium'
    ) -> Mistake:
        """
        Record a mistake.

        Args:
            description: What went wrong
            impact: Severity of impact ('low', 'medium', 'high')

        Returns:
            The newly created Mistake

        Raises:
            ValueError: If no context is loaded
        """
        self._ensure_context_loaded()

        mistake = Mistake(
            id=f"mis-{uuid.uuid4().hex[:8]}",
            description=description,
            impact=impact,
            occurred_at=datetime.now(),
        )
        self._context.mistakes.append(mistake)
        self._update_timestamp()
        return mistake

    def resolve_mistake(self, mistake_id: str, resolution: str) -> bool:
        """
        Mark a mistake as resolved.

        Args:
            mistake_id: The mistake ID to resolve
            resolution: How the mistake was resolved

        Returns:
            True if mistake was found and resolved
        """
        self._ensure_context_loaded()

        for mistake in self._context.mistakes:
            if mistake.id == mistake_id:
                mistake.resolution = resolution
                mistake.resolved_at = datetime.now()
                self._update_timestamp()
                return True
        return False

    # ==========================================================================
    # Risk Management
    # ==========================================================================

    def add_risk(
        self,
        description: str,
        severity: str = 'medium',
        likelihood: str = 'medium',
        mitigation: Optional[str] = None
    ) -> Risk:
        """
        Add a new risk to the context.

        Args:
            description: Description of the risk
            severity: Severity level ('low', 'medium', 'high', 'critical')
            likelihood: Likelihood ('low', 'medium', 'high')
            mitigation: Optional mitigation strategy

        Returns:
            The newly created Risk

        Raises:
            ValueError: If no context is loaded
        """
        self._ensure_context_loaded()

        risk = Risk(
            id=f"risk-{uuid.uuid4().hex[:8]}",
            description=description,
            severity=severity,
            likelihood=likelihood,
            mitigation=mitigation,
            status='open',
        )
        self._context.risks.append(risk)
        self._update_timestamp()
        return risk

    def mitigate_risk(self, risk_id: str, mitigation: str) -> bool:
        """
        Record mitigation for a risk.

        Args:
            risk_id: The risk ID to mitigate
            mitigation: The mitigation strategy applied

        Returns:
            True if risk was found and mitigated
        """
        self._ensure_context_loaded()

        for risk in self._context.risks:
            if risk.id == risk_id:
                risk.mitigation = mitigation
                risk.status = 'mitigated'
                self._update_timestamp()
                return True
        return False

    def accept_risk(self, risk_id: str) -> bool:
        """
        Mark a risk as accepted.

        Args:
            risk_id: The risk ID to accept

        Returns:
            True if risk was found and accepted
        """
        self._ensure_context_loaded()

        for risk in self._context.risks:
            if risk.id == risk_id:
                risk.status = 'accepted'
                self._update_timestamp()
                return True
        return False

    # ==========================================================================
    # File Tracking
    # ==========================================================================

    def track_file(
        self,
        path: str,
        purpose: str,
        related_goals: Optional[List[str]] = None
    ) -> FileMapping:
        """
        Track a file in the context.

        If the file is already tracked, updates its purpose and related goals.

        Args:
            path: File path (relative to project root)
            purpose: Description of the file's purpose
            related_goals: List of related goal IDs

        Returns:
            The FileMapping (existing or new)

        Raises:
            ValueError: If no context is loaded
        """
        self._ensure_context_loaded()

        # Check for existing file mapping
        for fm in self._context.file_map:
            if fm.path == path:
                fm.purpose = purpose
                fm.last_modified = datetime.now()
                if related_goals:
                    # Merge related goals
                    existing_goals = set(fm.related_goals)
                    existing_goals.update(related_goals)
                    fm.related_goals = sorted(existing_goals)
                self._update_timestamp()
                return fm

        # Create new file mapping
        fm = FileMapping(
            path=path,
            purpose=purpose,
            last_modified=datetime.now(),
            related_goals=related_goals or [],
        )
        self._context.file_map.append(fm)
        self._update_timestamp()
        return fm

    def untrack_file(self, path: str) -> bool:
        """
        Remove a file from tracking.

        Args:
            path: File path to untrack

        Returns:
            True if file was found and removed
        """
        self._ensure_context_loaded()

        for i, fm in enumerate(self._context.file_map):
            if fm.path == path:
                del self._context.file_map[i]
                self._update_timestamp()
                return True
        return False

    # ==========================================================================
    # Dependency Management
    # ==========================================================================

    def add_dependency(
        self,
        name: str,
        purpose: str,
        version: Optional[str] = None,
        required: bool = True
    ) -> Dependency:
        """
        Add a dependency to the context.

        Args:
            name: Dependency name
            purpose: Why this dependency is needed
            version: Version string
            required: Whether the dependency is required

        Returns:
            The newly created Dependency

        Raises:
            ValueError: If no context is loaded
        """
        self._ensure_context_loaded()

        dependency = Dependency(
            name=name,
            purpose=purpose,
            version=version,
            required=required,
        )
        self._context.dependencies.append(dependency)
        self._update_timestamp()
        return dependency

    def update_dependency_version(self, name: str, version: str) -> bool:
        """
        Update a dependency's version.

        Args:
            name: Dependency name
            version: New version string

        Returns:
            True if dependency was found and updated
        """
        self._ensure_context_loaded()

        for dep in self._context.dependencies:
            if dep.name.lower() == name.lower():
                dep.version = version
                self._update_timestamp()
                return True
        return False

    # ==========================================================================
    # Constraint Management
    # ==========================================================================

    def add_constraint(self, constraint: str) -> None:
        """
        Add a constraint to the context.

        Args:
            constraint: The constraint description
        """
        self._ensure_context_loaded()

        if constraint not in self._context.constraints:
            self._context.constraints.append(constraint)
            self._update_timestamp()

    def remove_constraint(self, constraint: str) -> bool:
        """
        Remove a constraint from the context.

        Args:
            constraint: The constraint to remove

        Returns:
            True if constraint was found and removed
        """
        self._ensure_context_loaded()

        if constraint in self._context.constraints:
            self._context.constraints.remove(constraint)
            self._update_timestamp()
            return True
        return False

    # ==========================================================================
    # Progress and Domain Updates
    # ==========================================================================

    def update_progress(self, key: str, value: Any) -> None:
        """
        Update a progress metric.

        Args:
            key: Progress metric key
            value: Progress metric value
        """
        self._ensure_context_loaded()
        self._context.progress[key] = value
        self._update_timestamp()

    def update_domain(self, key: str, value: Any) -> None:
        """
        Update domain knowledge.

        Args:
            key: Domain knowledge key
            value: Domain knowledge value
        """
        self._ensure_context_loaded()
        self._context.domain[key] = value
        self._update_timestamp()

    def get_progress(self, key: str, default: Any = None) -> Any:
        """
        Get a progress metric value.

        Args:
            key: Progress metric key
            default: Default value if key not found

        Returns:
            Progress metric value
        """
        self._ensure_context_loaded()
        return self._context.progress.get(key, default)

    def get_domain(self, key: str, default: Any = None) -> Any:
        """
        Get domain knowledge value.

        Args:
            key: Domain knowledge key
            default: Default value if key not found

        Returns:
            Domain knowledge value
        """
        self._ensure_context_loaded()
        return self._context.domain.get(key, default)

    # ==========================================================================
    # Helper Methods
    # ==========================================================================

    def _ensure_context_loaded(self) -> None:
        """Ensure a context is loaded, raise if not."""
        if self._context is None:
            raise ValueError("No context loaded. Call load() or load_or_create() first.")

    def _update_timestamp(self) -> None:
        """Update the context's updated_at timestamp."""
        if self._context:
            self._context.updated_at = datetime.now()
