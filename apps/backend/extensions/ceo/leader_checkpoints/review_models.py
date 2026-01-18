"""
Review Models
=============

Data models for the review and learning points system including review types,
rating criteria, learning point extraction, and review data structures.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ReviewType(Enum):
    """
    Review trigger types.

    Defines what type of review is being performed:
    - SUBTASK: Review after subtask completion
    - PHASE: Summary review at phase completion
    - ERROR_RESOLUTION: Lessons learned from error fixes
    - DECISION: Decision retrospective review
    - MANUAL: User-requested manual review
    """
    SUBTASK = "subtask"
    PHASE = "phase"
    ERROR_RESOLUTION = "error"
    DECISION = "decision"
    MANUAL = "manual"


class ReviewRating(Enum):
    """
    Review rating levels.

    Defines the quality assessment scale:
    - EXCELLENT: Exceptional quality, above expectations
    - GOOD: Good quality, meets expectations
    - ACCEPTABLE: Acceptable quality, minimum standard met
    - NEEDS_IMPROVEMENT: Below expectations, improvement needed
    - POOR: Significant issues, requires rework
    """
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"


@dataclass
class ReviewCriteria:
    """
    Review criteria ratings.

    Captures ratings across multiple quality dimensions to provide
    a comprehensive assessment of work quality.

    Attributes:
        code_quality: Rating for code quality (complexity, readability, tests)
        decision_quality: Rating for decision appropriateness
        efficiency: Rating for time and resource efficiency
        reusability: Rating for pattern extraction and reusability
        risk_management: Rating for handling of potential issues
        notes: Additional notes per criteria (key: criteria name)
    """
    code_quality: Optional[ReviewRating] = None
    decision_quality: Optional[ReviewRating] = None
    efficiency: Optional[ReviewRating] = None
    reusability: Optional[ReviewRating] = None
    risk_management: Optional[ReviewRating] = None
    notes: Dict[str, str] = field(default_factory=dict)


@dataclass
class LearningPoint:
    """
    Learning point extracted from reviews.

    Represents a piece of knowledge that can be applied to future work.
    Learning points are automatically integrated into LeaderContext.

    Attributes:
        id: Unique learning point identifier (e.g., "lp-a1b2c3d4")
        type: Learning point type ('pattern', 'mistake', 'insight')
        description: Detailed description of the learning
        source_review_id: ID of the review that generated this learning point
        confidence: Confidence level for applying this learning (0-1)
        applied: Whether this has been applied to LeaderContext
        created_at: When this learning point was created
        tags: Tags for categorization
    """
    id: str
    type: str  # 'pattern', 'mistake', 'insight'
    description: str
    source_review_id: str
    confidence: float = 0.8
    applied: bool = False
    created_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Set created_at if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Review:
    """
    Review entry.

    Represents a complete review with ratings, learning points,
    and improvement suggestions.

    Attributes:
        id: Unique review identifier (e.g., "rev-a1b2c3d4")
        phase: Phase number when review was created
        review_type: Type of review being performed
        timestamp: When the review was created
        subject: Review subject identifier (subtask_id, phase_id, etc.)
        subject_description: Human-readable description of what is being reviewed
        criteria: Ratings per review criteria
        overall_rating: Overall quality rating
        summary: Brief summary of the review
        learning_points: Extracted learning points from this review
        improvements: Suggested improvements for future work
        action_items: Concrete action items to address
        checkpoint_id: Associated checkpoint ID if any
        error_ids: Related error IDs
        decision_ids: Related decision IDs
        auto_generated: Whether review was automatically generated
        reviewed_by: Who performed the review (system, user, agent)
        metadata: Additional metadata for the review
    """
    id: str
    phase: int
    review_type: ReviewType
    timestamp: datetime
    subject: str
    subject_description: str

    # Ratings
    criteria: ReviewCriteria = field(default_factory=ReviewCriteria)
    overall_rating: Optional[ReviewRating] = None
    summary: str = ""

    # Learning points
    learning_points: List[LearningPoint] = field(default_factory=list)

    # Improvements
    improvements: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)

    # References
    checkpoint_id: Optional[str] = None
    error_ids: List[str] = field(default_factory=list)
    decision_ids: List[str] = field(default_factory=list)

    # Metadata
    auto_generated: bool = True
    reviewed_by: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)
