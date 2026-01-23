"""
Review Generator
================

Automated review generation for subtasks, phases, and error resolutions.
Extracts learning points and applies them to LeaderContext.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..leader_context.service import LeaderContextService
from .error_logger import ErrorLogger
from .manager import CheckpointManager
from .review_models import (
    LearningPoint,
    Review,
    ReviewCriteria,
    ReviewRating,
    ReviewType,
)


class ReviewGenerator:
    """
    Automated review generator.

    Generates reviews for subtasks, phases, and error resolutions.
    Extracts learning points and automatically applies them to LeaderContext.

    Attributes:
        project_path: Path to the project root
        checkpoint_manager: CheckpointManager instance
        error_logger: ErrorLogger instance
        context_service: LeaderContextService instance
        reviews_dir: Directory for storing review files
    """

    def __init__(
        self,
        project_path: str,
        checkpoint_manager: CheckpointManager,
        error_logger: ErrorLogger,
        context_service: LeaderContextService,
    ):
        """
        Initialize ReviewGenerator.

        Args:
            project_path: Path to the project root
            checkpoint_manager: CheckpointManager for checkpoint access
            error_logger: ErrorLogger for error data access
            context_service: LeaderContextService for applying learning points
        """
        self.project_path = project_path
        self.checkpoint_manager = checkpoint_manager
        self.error_logger = error_logger
        self.context_service = context_service
        self.reviews_dir = Path(project_path) / ".planning" / "leader_context" / "reviews"
        self.reviews_dir.mkdir(parents=True, exist_ok=True)

        self._reviews: List[Review] = []
        self._load_reviews()

    # ==========================================================================
    # Review Generation
    # ==========================================================================

    def review_subtask(
        self,
        subtask_id: str,
        description: str,
        result: Dict[str, Any],
        checkpoint_id: Optional[str] = None,
    ) -> Review:
        """
        Generate review for a completed subtask.

        Args:
            subtask_id: ID of the completed subtask
            description: Description of the subtask
            result: Result data from the subtask execution
            checkpoint_id: Associated checkpoint ID if any

        Returns:
            Generated Review
        """
        current_phase = 0
        if self.context_service.context:
            current_phase = self.context_service.context.phase

        review = Review(
            id=f"rev-{uuid.uuid4().hex[:8]}",
            phase=current_phase,
            review_type=ReviewType.SUBTASK,
            timestamp=datetime.now(),
            subject=subtask_id,
            subject_description=description,
            checkpoint_id=checkpoint_id,
        )

        # Auto-evaluate based on result
        review.criteria = self._evaluate_subtask(result)
        review.overall_rating = self._calculate_overall_rating(review.criteria)
        review.summary = self._generate_summary(review)

        # Extract learning points
        review.learning_points = self._extract_learning_points(result, review.id)

        # Generate improvement suggestions
        review.improvements = self._suggest_improvements(review)

        self._reviews.append(review)
        self._apply_learning_points(review)
        self._save_reviews()

        return review

    def review_phase(self, phase: int) -> Review:
        """
        Generate summary review for a completed phase.

        Args:
            phase: Phase number to review

        Returns:
            Generated Review
        """
        # Get all reviews for this phase
        phase_reviews = [r for r in self._reviews if r.phase == phase]
        errors = self.error_logger.get_error_summary()
        checkpoints = self.checkpoint_manager.list_checkpoints(phase)

        review = Review(
            id=f"rev-phase-{phase}-{uuid.uuid4().hex[:8]}",
            phase=phase,
            review_type=ReviewType.PHASE,
            timestamp=datetime.now(),
            subject=f"phase-{phase}",
            subject_description=f"Phase {phase} completion summary",
        )

        # Aggregate criteria from all phase reviews
        review.criteria = self._aggregate_criteria(phase_reviews)
        review.overall_rating = self._calculate_overall_rating(review.criteria)
        review.summary = self._generate_phase_summary(phase, phase_reviews, errors)

        # Aggregate and deduplicate learning points
        all_learning = []
        for r in phase_reviews:
            all_learning.extend(r.learning_points)
        review.learning_points = self._deduplicate_learning_points(all_learning)

        # Generate phase-level improvements
        review.improvements = self._suggest_phase_improvements(phase_reviews, errors)
        review.action_items = self._generate_action_items(review)

        # Add metadata
        review.metadata = {
            "subtask_reviews": len(phase_reviews),
            "total_errors": errors.get("total_errors", 0),
            "total_checkpoints": len(checkpoints),
        }

        self._reviews.append(review)
        self._save_reviews()

        return review

    def review_error_resolution(
        self,
        error_id: str,
        resolution: str,
    ) -> Optional[Review]:
        """
        Generate review for an error resolution (lessons learned).

        Args:
            error_id: ID of the resolved error
            resolution: Description of how the error was resolved

        Returns:
            Generated Review or None if error not found
        """
        error = self.error_logger.get_error_by_id(error_id)
        if not error:
            return None

        review = Review(
            id=f"rev-err-{uuid.uuid4().hex[:8]}",
            phase=error.phase,
            review_type=ReviewType.ERROR_RESOLUTION,
            timestamp=datetime.now(),
            subject=error_id,
            subject_description=f"Error resolution: {error.message[:50]}...",
            error_ids=[error_id],
        )

        # Create learning point from error resolution
        learning = LearningPoint(
            id=f"lp-{uuid.uuid4().hex[:8]}",
            type="mistake",
            description=f"Error: {error.message}\nCategory: {error.category.value}\nResolution: {resolution}",
            source_review_id=review.id,
            tags=[error.category.value, "error-resolution"],
        )
        review.learning_points = [learning]

        # Suggest prevention measures
        review.improvements = self._suggest_prevention(error, resolution)
        review.summary = f"Error '{error.message[:30]}...' resolved: {resolution[:50]}..."

        # Set rating based on error severity
        if error.severity.value == "critical":
            review.overall_rating = ReviewRating.NEEDS_IMPROVEMENT
        elif error.severity.value == "error":
            review.overall_rating = ReviewRating.ACCEPTABLE
        else:
            review.overall_rating = ReviewRating.GOOD

        self._reviews.append(review)
        self._apply_learning_points(review)
        self._save_reviews()

        return review

    def review_decision(
        self,
        decision_id: str,
        description: str,
        rationale: str,
        outcome: Optional[str] = None,
    ) -> Review:
        """
        Generate retrospective review for a decision.

        Args:
            decision_id: ID of the decision
            description: What was decided
            rationale: Why this decision was made
            outcome: Optional outcome description

        Returns:
            Generated Review
        """
        current_phase = 0
        if self.context_service.context:
            current_phase = self.context_service.context.phase

        review = Review(
            id=f"rev-dec-{uuid.uuid4().hex[:8]}",
            phase=current_phase,
            review_type=ReviewType.DECISION,
            timestamp=datetime.now(),
            subject=decision_id,
            subject_description=f"Decision: {description[:50]}...",
            decision_ids=[decision_id],
        )

        # Evaluate decision quality
        review.criteria = ReviewCriteria(
            decision_quality=self._evaluate_decision(rationale, outcome),
        )
        review.overall_rating = review.criteria.decision_quality
        review.summary = f"Decision review: {description[:80]}..."

        # Extract learning if outcome provided
        if outcome:
            learning = LearningPoint(
                id=f"lp-{uuid.uuid4().hex[:8]}",
                type="insight",
                description=f"Decision: {description}\nRationale: {rationale}\nOutcome: {outcome}",
                source_review_id=review.id,
                tags=["decision"],
            )
            review.learning_points = [learning]
            self._apply_learning_points(review)

        self._reviews.append(review)
        self._save_reviews()

        return review

    # ==========================================================================
    # Query Methods
    # ==========================================================================

    def get_reviews(
        self,
        phase: Optional[int] = None,
        review_type: Optional[ReviewType] = None,
    ) -> List[Review]:
        """
        Get reviews with optional filtering.

        Args:
            phase: Filter by phase number
            review_type: Filter by review type

        Returns:
            List of matching reviews
        """
        result = self._reviews

        if phase is not None:
            result = [r for r in result if r.phase == phase]

        if review_type is not None:
            result = [r for r in result if r.review_type == review_type]

        return result

    def get_all_learning_points(self, applied_only: bool = False) -> List[LearningPoint]:
        """
        Get all learning points across reviews.

        Args:
            applied_only: If True, only return applied learning points

        Returns:
            List of learning points
        """
        all_points = []
        for review in self._reviews:
            for lp in review.learning_points:
                if not applied_only or lp.applied:
                    all_points.append(lp)
        return all_points

    def get_improvement_summary(self) -> Dict[str, Any]:
        """
        Get summary of improvements and learning points.

        Returns:
            Dictionary containing improvement statistics
        """
        all_learning = self.get_all_learning_points()

        return {
            "total_reviews": len(self._reviews),
            "learning_points": len(all_learning),
            "applied_patterns": sum(
                1 for lp in all_learning if lp.type == "pattern" and lp.applied
            ),
            "recorded_mistakes": sum(
                1 for lp in all_learning if lp.type == "mistake" and lp.applied
            ),
            "insights": sum(
                1 for lp in all_learning if lp.type == "insight"
            ),
            "pending_action_items": self._count_pending_actions(),
            "reviews_by_type": {
                rt.value: len([r for r in self._reviews if r.review_type == rt])
                for rt in ReviewType
            },
        }

    # ==========================================================================
    # Evaluation Methods
    # ==========================================================================

    def _evaluate_subtask(self, result: Dict[str, Any]) -> ReviewCriteria:
        """
        Evaluate subtask result and assign ratings.

        Args:
            result: Subtask execution result

        Returns:
            ReviewCriteria with ratings
        """
        criteria = ReviewCriteria()

        # Evaluate code quality based on result indicators
        files_changed = result.get("files_changed", 0)
        tests_passed = result.get("tests_passed", False)
        has_errors = result.get("errors", [])

        if tests_passed and not has_errors:
            criteria.code_quality = ReviewRating.GOOD
        elif not has_errors:
            criteria.code_quality = ReviewRating.ACCEPTABLE
        else:
            criteria.code_quality = ReviewRating.NEEDS_IMPROVEMENT

        # Evaluate efficiency based on time/resources
        execution_time = result.get("execution_time_seconds", 0)
        if execution_time > 0:
            if execution_time < 60:
                criteria.efficiency = ReviewRating.EXCELLENT
            elif execution_time < 300:
                criteria.efficiency = ReviewRating.GOOD
            else:
                criteria.efficiency = ReviewRating.ACCEPTABLE

        # Add notes
        if files_changed > 0:
            criteria.notes["files_changed"] = str(files_changed)
        if tests_passed:
            criteria.notes["tests_passed"] = "true"

        return criteria

    def _calculate_overall_rating(self, criteria: ReviewCriteria) -> ReviewRating:
        """
        Calculate overall rating from criteria.

        Args:
            criteria: ReviewCriteria with individual ratings

        Returns:
            Overall ReviewRating
        """
        ratings = []

        if criteria.code_quality:
            ratings.append(criteria.code_quality)
        if criteria.decision_quality:
            ratings.append(criteria.decision_quality)
        if criteria.efficiency:
            ratings.append(criteria.efficiency)
        if criteria.reusability:
            ratings.append(criteria.reusability)
        if criteria.risk_management:
            ratings.append(criteria.risk_management)

        if not ratings:
            return ReviewRating.ACCEPTABLE

        # Convert to numeric scale for averaging
        rating_values = {
            ReviewRating.EXCELLENT: 5,
            ReviewRating.GOOD: 4,
            ReviewRating.ACCEPTABLE: 3,
            ReviewRating.NEEDS_IMPROVEMENT: 2,
            ReviewRating.POOR: 1,
        }

        avg = sum(rating_values[r] for r in ratings) / len(ratings)

        if avg >= 4.5:
            return ReviewRating.EXCELLENT
        elif avg >= 3.5:
            return ReviewRating.GOOD
        elif avg >= 2.5:
            return ReviewRating.ACCEPTABLE
        elif avg >= 1.5:
            return ReviewRating.NEEDS_IMPROVEMENT
        else:
            return ReviewRating.POOR

    def _generate_summary(self, review: Review) -> str:
        """
        Generate summary text for a review.

        Args:
            review: Review to summarize

        Returns:
            Summary string
        """
        rating_text = review.overall_rating.value if review.overall_rating else "not rated"
        return f"Review of {review.subject_description}: {rating_text}"

    def _extract_learning_points(
        self,
        result: Dict[str, Any],
        review_id: str,
    ) -> List[LearningPoint]:
        """
        Extract learning points from subtask result.

        Args:
            result: Subtask execution result
            review_id: ID of the parent review

        Returns:
            List of extracted LearningPoints
        """
        points = []

        # Extract patterns from successful results
        if result.get("tests_passed", False):
            patterns = result.get("patterns_discovered", [])
            for pattern in patterns:
                point = LearningPoint(
                    id=f"lp-{uuid.uuid4().hex[:8]}",
                    type="pattern",
                    description=str(pattern),
                    source_review_id=review_id,
                    tags=["auto-discovered"],
                )
                points.append(point)

        # Extract insights from metrics
        metrics = result.get("metrics", {})
        if metrics.get("complexity_reduced", False):
            point = LearningPoint(
                id=f"lp-{uuid.uuid4().hex[:8]}",
                type="insight",
                description="Complexity was successfully reduced in this subtask",
                source_review_id=review_id,
                confidence=0.7,
            )
            points.append(point)

        # Extract mistakes from errors
        errors = result.get("errors", [])
        for error in errors[:3]:  # Limit to first 3 errors
            point = LearningPoint(
                id=f"lp-{uuid.uuid4().hex[:8]}",
                type="mistake",
                description=str(error),
                source_review_id=review_id,
                tags=["error"],
            )
            points.append(point)

        return points

    def _suggest_improvements(self, review: Review) -> List[str]:
        """
        Generate improvement suggestions based on review.

        Args:
            review: Review to analyze

        Returns:
            List of improvement suggestions
        """
        improvements = []

        if review.overall_rating == ReviewRating.NEEDS_IMPROVEMENT:
            improvements.append("Consider breaking down complex tasks into smaller subtasks")

        if review.criteria.code_quality == ReviewRating.NEEDS_IMPROVEMENT:
            improvements.append("Add more unit tests to improve code quality")
            improvements.append("Review code for complexity and refactor if needed")

        if review.criteria.efficiency == ReviewRating.NEEDS_IMPROVEMENT:
            improvements.append("Optimize execution time by caching or parallel processing")

        return improvements

    def _evaluate_decision(
        self,
        rationale: str,
        outcome: Optional[str],
    ) -> ReviewRating:
        """
        Evaluate decision quality.

        Args:
            rationale: Decision rationale
            outcome: Optional outcome description

        Returns:
            ReviewRating for the decision
        """
        # Basic heuristics for decision evaluation
        if outcome and "success" in outcome.lower():
            return ReviewRating.GOOD
        elif outcome and ("fail" in outcome.lower() or "error" in outcome.lower()):
            return ReviewRating.NEEDS_IMPROVEMENT
        elif len(rationale) > 100:  # Well-documented rationale
            return ReviewRating.GOOD
        else:
            return ReviewRating.ACCEPTABLE

    # ==========================================================================
    # Aggregation Methods
    # ==========================================================================

    def _aggregate_criteria(self, reviews: List[Review]) -> ReviewCriteria:
        """
        Aggregate criteria from multiple reviews.

        Args:
            reviews: List of reviews to aggregate

        Returns:
            Aggregated ReviewCriteria
        """
        if not reviews:
            return ReviewCriteria()

        # Collect all non-None ratings for each criteria
        code_ratings = [r.criteria.code_quality for r in reviews if r.criteria.code_quality]
        decision_ratings = [r.criteria.decision_quality for r in reviews if r.criteria.decision_quality]
        efficiency_ratings = [r.criteria.efficiency for r in reviews if r.criteria.efficiency]

        criteria = ReviewCriteria()

        if code_ratings:
            criteria.code_quality = self._average_rating(code_ratings)
        if decision_ratings:
            criteria.decision_quality = self._average_rating(decision_ratings)
        if efficiency_ratings:
            criteria.efficiency = self._average_rating(efficiency_ratings)

        return criteria

    def _average_rating(self, ratings: List[ReviewRating]) -> ReviewRating:
        """
        Calculate average of multiple ratings.

        Args:
            ratings: List of ratings to average

        Returns:
            Average ReviewRating
        """
        rating_values = {
            ReviewRating.EXCELLENT: 5,
            ReviewRating.GOOD: 4,
            ReviewRating.ACCEPTABLE: 3,
            ReviewRating.NEEDS_IMPROVEMENT: 2,
            ReviewRating.POOR: 1,
        }

        avg = sum(rating_values[r] for r in ratings) / len(ratings)

        if avg >= 4.5:
            return ReviewRating.EXCELLENT
        elif avg >= 3.5:
            return ReviewRating.GOOD
        elif avg >= 2.5:
            return ReviewRating.ACCEPTABLE
        elif avg >= 1.5:
            return ReviewRating.NEEDS_IMPROVEMENT
        else:
            return ReviewRating.POOR

    def _generate_phase_summary(
        self,
        phase: int,
        reviews: List[Review],
        errors: Dict[str, Any],
    ) -> str:
        """
        Generate summary for phase completion.

        Args:
            phase: Phase number
            reviews: Reviews from this phase
            errors: Error summary

        Returns:
            Phase summary string
        """
        total_reviews = len(reviews)
        total_errors = errors.get("total_errors", 0)
        unresolved = errors.get("unresolved", 0)

        return (
            f"Phase {phase} completed with {total_reviews} reviews. "
            f"Errors: {total_errors} total, {unresolved} unresolved."
        )

    def _deduplicate_learning_points(
        self,
        points: List[LearningPoint],
    ) -> List[LearningPoint]:
        """
        Deduplicate learning points by description similarity.

        Args:
            points: List of learning points

        Returns:
            Deduplicated list
        """
        seen_descriptions = set()
        unique_points = []

        for point in points:
            # Simple deduplication by exact description
            desc_key = point.description[:100].lower()
            if desc_key not in seen_descriptions:
                seen_descriptions.add(desc_key)
                unique_points.append(point)

        return unique_points

    def _suggest_phase_improvements(
        self,
        reviews: List[Review],
        errors: Dict[str, Any],
    ) -> List[str]:
        """
        Generate phase-level improvement suggestions.

        Args:
            reviews: Reviews from the phase
            errors: Error summary

        Returns:
            List of improvement suggestions
        """
        improvements = []

        # High error rate
        if errors.get("total_errors", 0) > 5:
            improvements.append("Consider adding more validation before executing tasks")

        # Many reviews with needs_improvement
        poor_reviews = [
            r for r in reviews
            if r.overall_rating in (ReviewRating.NEEDS_IMPROVEMENT, ReviewRating.POOR)
        ]
        if len(poor_reviews) > len(reviews) / 3:
            improvements.append("Review task complexity and consider smaller iterations")

        # Critical errors
        if errors.get("critical", 0) > 0:
            improvements.append("Address critical errors before proceeding to next phase")

        return improvements

    def _generate_action_items(self, review: Review) -> List[str]:
        """
        Generate concrete action items from review.

        Args:
            review: Review to analyze

        Returns:
            List of action items
        """
        actions = []

        for improvement in review.improvements:
            if "test" in improvement.lower():
                actions.append("Add unit tests for uncovered code paths")
            if "refactor" in improvement.lower():
                actions.append("Schedule refactoring session for complex modules")

        return actions

    def _suggest_prevention(
        self,
        error: Any,
        resolution: str,
    ) -> List[str]:
        """
        Suggest prevention measures for an error.

        Args:
            error: Error log entry
            resolution: How the error was resolved

        Returns:
            List of prevention suggestions
        """
        suggestions = []

        # Category-based suggestions
        category = error.category.value if hasattr(error, "category") else "unknown"

        if category == "syntax":
            suggestions.append("Add linting to catch syntax errors early")
        elif category == "runtime":
            suggestions.append("Add input validation to prevent runtime errors")
        elif category == "integration":
            suggestions.append("Add integration tests for external service calls")
        elif category == "configuration":
            suggestions.append("Validate configuration files on startup")

        # Resolution-based suggestions
        if "missing" in resolution.lower():
            suggestions.append("Check for missing dependencies before execution")
        if "timeout" in resolution.lower():
            suggestions.append("Add retry logic with exponential backoff")

        return suggestions

    def _count_pending_actions(self) -> int:
        """
        Count pending action items across all reviews.

        Returns:
            Number of pending action items
        """
        total = 0
        for review in self._reviews:
            total += len(review.action_items)
        return total

    # ==========================================================================
    # Learning Point Application
    # ==========================================================================

    def _apply_learning_points(self, review: Review) -> None:
        """
        Apply learning points to LeaderContext.

        Args:
            review: Review containing learning points to apply
        """
        if not self.context_service.context:
            return

        for lp in review.learning_points:
            if lp.applied:
                continue

            try:
                if lp.type == "pattern":
                    self.context_service.record_pattern(
                        name=f"Pattern from {review.subject}",
                        description=lp.description,
                    )
                    lp.applied = True
                elif lp.type == "mistake":
                    self.context_service.record_mistake(
                        description=lp.description,
                        impact="medium",
                    )
                    lp.applied = True
                elif lp.type == "insight":
                    # Store insights in domain knowledge
                    self.context_service.update_domain(
                        f"insight_{lp.id}",
                        lp.description,
                    )
                    lp.applied = True
            except Exception:
                # Continue if context service fails
                pass

        self.context_service.save()

    # ==========================================================================
    # Persistence
    # ==========================================================================

    def _load_reviews(self) -> None:
        """Load reviews from storage."""
        reviews_file = self.reviews_dir / "reviews.json"
        if not reviews_file.exists():
            self._reviews = []
            return

        try:
            with open(reviews_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._reviews = []
            for item in data.get("reviews", []):
                review = self._review_from_dict(item)
                if review:
                    self._reviews.append(review)
        except (json.JSONDecodeError, KeyError):
            self._reviews = []

    def _save_reviews(self) -> None:
        """Save reviews to storage."""
        reviews_file = self.reviews_dir / "reviews.json"

        data = {
            "last_updated": datetime.now().isoformat(),
            "reviews": [self._review_to_dict(r) for r in self._reviews],
        }

        with open(reviews_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _review_to_dict(self, review: Review) -> Dict[str, Any]:
        """Convert Review to dictionary."""
        return {
            "id": review.id,
            "phase": review.phase,
            "review_type": review.review_type.value,
            "timestamp": review.timestamp.isoformat(),
            "subject": review.subject,
            "subject_description": review.subject_description,
            "criteria": {
                "code_quality": review.criteria.code_quality.value if review.criteria.code_quality else None,
                "decision_quality": review.criteria.decision_quality.value if review.criteria.decision_quality else None,
                "efficiency": review.criteria.efficiency.value if review.criteria.efficiency else None,
                "reusability": review.criteria.reusability.value if review.criteria.reusability else None,
                "risk_management": review.criteria.risk_management.value if review.criteria.risk_management else None,
                "notes": review.criteria.notes,
            },
            "overall_rating": review.overall_rating.value if review.overall_rating else None,
            "summary": review.summary,
            "learning_points": [
                {
                    "id": lp.id,
                    "type": lp.type,
                    "description": lp.description,
                    "source_review_id": lp.source_review_id,
                    "confidence": lp.confidence,
                    "applied": lp.applied,
                    "created_at": lp.created_at.isoformat() if lp.created_at else None,
                    "tags": lp.tags,
                }
                for lp in review.learning_points
            ],
            "improvements": review.improvements,
            "action_items": review.action_items,
            "checkpoint_id": review.checkpoint_id,
            "error_ids": review.error_ids,
            "decision_ids": review.decision_ids,
            "auto_generated": review.auto_generated,
            "reviewed_by": review.reviewed_by,
            "metadata": review.metadata,
        }

    def _review_from_dict(self, data: Dict[str, Any]) -> Optional[Review]:
        """Convert dictionary to Review."""
        try:
            # Parse criteria
            criteria_data = data.get("criteria", {})
            criteria = ReviewCriteria(
                code_quality=ReviewRating(criteria_data["code_quality"]) if criteria_data.get("code_quality") else None,
                decision_quality=ReviewRating(criteria_data["decision_quality"]) if criteria_data.get("decision_quality") else None,
                efficiency=ReviewRating(criteria_data["efficiency"]) if criteria_data.get("efficiency") else None,
                reusability=ReviewRating(criteria_data["reusability"]) if criteria_data.get("reusability") else None,
                risk_management=ReviewRating(criteria_data["risk_management"]) if criteria_data.get("risk_management") else None,
                notes=criteria_data.get("notes", {}),
            )

            # Parse learning points
            learning_points = []
            for lp_data in data.get("learning_points", []):
                lp = LearningPoint(
                    id=lp_data["id"],
                    type=lp_data["type"],
                    description=lp_data["description"],
                    source_review_id=lp_data["source_review_id"],
                    confidence=lp_data.get("confidence", 0.8),
                    applied=lp_data.get("applied", False),
                    created_at=datetime.fromisoformat(lp_data["created_at"]) if lp_data.get("created_at") else None,
                    tags=lp_data.get("tags", []),
                )
                learning_points.append(lp)

            return Review(
                id=data["id"],
                phase=data["phase"],
                review_type=ReviewType(data["review_type"]),
                timestamp=datetime.fromisoformat(data["timestamp"]),
                subject=data["subject"],
                subject_description=data["subject_description"],
                criteria=criteria,
                overall_rating=ReviewRating(data["overall_rating"]) if data.get("overall_rating") else None,
                summary=data.get("summary", ""),
                learning_points=learning_points,
                improvements=data.get("improvements", []),
                action_items=data.get("action_items", []),
                checkpoint_id=data.get("checkpoint_id"),
                error_ids=data.get("error_ids", []),
                decision_ids=data.get("decision_ids", []),
                auto_generated=data.get("auto_generated", True),
                reviewed_by=data.get("reviewed_by", "system"),
                metadata=data.get("metadata", {}),
            )
        except (KeyError, ValueError):
            return None
