"""
Leader Context Models
=====================

Data classes for storing leader agent execution context.
These models capture goals, decisions, patterns, mistakes,
file mappings, dependencies, risks, and overall progress.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Goal:
    """
    Represents a goal or objective for the leader agent.

    Attributes:
        id: Unique identifier for the goal
        description: Human-readable description of the goal
        priority: Priority level from 1 (highest) to 5 (lowest)
        status: Current status ('active', 'completed', 'deferred')
        created_at: When the goal was created
        completed_at: When the goal was completed (if applicable)
    """
    id: str
    description: str
    priority: int  # 1-5, where 1 is highest priority
    status: str  # 'active', 'completed', 'deferred'
    created_at: datetime
    completed_at: Optional[datetime] = None


@dataclass
class Decision:
    """
    Represents a decision made by the leader agent.

    Attributes:
        id: Unique identifier for the decision
        description: What was decided
        rationale: Why this decision was made
        made_at: When the decision was made
        related_goals: List of goal IDs this decision relates to
    """
    id: str
    description: str
    rationale: str
    made_at: datetime
    related_goals: List[str] = field(default_factory=list)


@dataclass
class Pattern:
    """
    Represents a discovered pattern or best practice.

    Attributes:
        id: Unique identifier for the pattern
        name: Short name for the pattern
        description: Detailed description of the pattern
        frequency: Number of times this pattern has been observed
        first_seen: When the pattern was first discovered
        last_seen: When the pattern was last observed
    """
    id: str
    name: str
    description: str
    frequency: int  # Number of times discovered
    first_seen: datetime
    last_seen: datetime


@dataclass
class Mistake:
    """
    Represents an error or mistake that occurred.

    Attributes:
        id: Unique identifier for the mistake
        description: What went wrong
        impact: Severity of impact ('low', 'medium', 'high')
        resolution: How the mistake was resolved (if applicable)
        occurred_at: When the mistake occurred
        resolved_at: When the mistake was resolved (if applicable)
    """
    id: str
    description: str
    impact: str  # 'low', 'medium', 'high'
    occurred_at: datetime
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None


@dataclass
class FileMapping:
    """
    Represents a mapping of an important file in the project.

    Attributes:
        path: File path relative to project root
        purpose: Description of the file's purpose
        last_modified: When the file was last modified
        related_goals: List of goal IDs this file relates to
    """
    path: str
    purpose: str
    last_modified: datetime
    related_goals: List[str] = field(default_factory=list)


@dataclass
class Dependency:
    """
    Represents a project dependency.

    Attributes:
        name: Name of the dependency
        version: Version string (if known)
        purpose: Why this dependency is needed
        required: Whether this dependency is required or optional
    """
    name: str
    purpose: str
    version: Optional[str] = None
    required: bool = True


@dataclass
class Risk:
    """
    Represents a risk or concern.

    Attributes:
        id: Unique identifier for the risk
        description: Description of the risk
        severity: How severe the risk is ('low', 'medium', 'high', 'critical')
        likelihood: How likely the risk is to occur ('low', 'medium', 'high')
        mitigation: Planned or implemented mitigation strategy
        status: Current status ('open', 'mitigated', 'accepted')
    """
    id: str
    description: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    likelihood: str  # 'low', 'medium', 'high'
    mitigation: Optional[str] = None
    status: str = 'open'  # 'open', 'mitigated', 'accepted'


@dataclass
class LeaderContext:
    """
    Main context model for leader agent execution.

    This model captures all contextual information needed for
    a leader agent to maintain state across sessions and make
    informed decisions.

    Attributes:
        project_id: Unique identifier for the project
        phase: Current phase number
        goals: List of goals and objectives
        constraints: List of constraint descriptions
        decisions: List of decisions made
        patterns: List of discovered patterns
        mistakes: List of mistakes and errors
        file_map: List of important file mappings
        dependencies: List of project dependencies
        risks: List of risks and concerns
        progress: Dictionary of progress metrics
        domain: Dictionary of domain-specific knowledge
        created_at: When the context was created
        updated_at: When the context was last updated
    """
    project_id: str
    phase: int
    goals: List[Goal] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    decisions: List[Decision] = field(default_factory=list)
    patterns: List[Pattern] = field(default_factory=list)
    mistakes: List[Mistake] = field(default_factory=list)
    file_map: List[FileMapping] = field(default_factory=list)
    dependencies: List[Dependency] = field(default_factory=list)
    risks: List[Risk] = field(default_factory=list)
    progress: Dict[str, Any] = field(default_factory=dict)
    domain: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
