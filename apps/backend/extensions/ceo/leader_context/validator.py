"""
Leader Context Validator
========================

Provides validation for LeaderContext and its component models.
"""

from typing import List

from .models import LeaderContext


class ContextValidator:
    """
    Validator for LeaderContext instances.

    Provides validation methods to ensure context data meets
    required constraints and business rules.
    """

    # Valid status values for Goal
    VALID_GOAL_STATUSES = {'active', 'completed', 'deferred'}

    # Valid priority range for Goal
    MIN_PRIORITY = 1
    MAX_PRIORITY = 5

    # Valid impact values for Mistake
    VALID_IMPACTS = {'low', 'medium', 'high'}

    # Valid severity values for Risk
    VALID_SEVERITIES = {'low', 'medium', 'high', 'critical'}

    # Valid likelihood values for Risk
    VALID_LIKELIHOODS = {'low', 'medium', 'high'}

    # Valid status values for Risk
    VALID_RISK_STATUSES = {'open', 'mitigated', 'accepted'}

    @staticmethod
    def validate(context: LeaderContext) -> List[str]:
        """
        Validate a LeaderContext instance.

        Checks all required fields and value constraints.

        Args:
            context: LeaderContext instance to validate

        Returns:
            List of error messages. Empty list if valid.
        """
        errors: List[str] = []

        # Validate project_id
        if not context.project_id:
            errors.append("project_id is required and cannot be empty")
        elif not isinstance(context.project_id, str):
            errors.append("project_id must be a string")

        # Validate phase
        if not isinstance(context.phase, int):
            errors.append("phase must be an integer")
        elif context.phase < 0:
            errors.append("phase must be a non-negative integer")

        # Validate goals
        for i, goal in enumerate(context.goals):
            goal_errors = ContextValidator._validate_goal(goal, i)
            errors.extend(goal_errors)

        # Validate decisions
        for i, decision in enumerate(context.decisions):
            decision_errors = ContextValidator._validate_decision(decision, i)
            errors.extend(decision_errors)

        # Validate patterns
        for i, pattern in enumerate(context.patterns):
            pattern_errors = ContextValidator._validate_pattern(pattern, i)
            errors.extend(pattern_errors)

        # Validate mistakes
        for i, mistake in enumerate(context.mistakes):
            mistake_errors = ContextValidator._validate_mistake(mistake, i)
            errors.extend(mistake_errors)

        # Validate file_map
        for i, file_mapping in enumerate(context.file_map):
            mapping_errors = ContextValidator._validate_file_mapping(file_mapping, i)
            errors.extend(mapping_errors)

        # Validate dependencies
        for i, dependency in enumerate(context.dependencies):
            dep_errors = ContextValidator._validate_dependency(dependency, i)
            errors.extend(dep_errors)

        # Validate risks
        for i, risk in enumerate(context.risks):
            risk_errors = ContextValidator._validate_risk(risk, i)
            errors.extend(risk_errors)

        return errors

    @staticmethod
    def _validate_goal(goal, index: int) -> List[str]:
        """Validate a Goal instance."""
        errors = []
        prefix = f"goals[{index}]"

        if not goal.id:
            errors.append(f"{prefix}.id is required")

        if not goal.description:
            errors.append(f"{prefix}.description is required")

        if not isinstance(goal.priority, int):
            errors.append(f"{prefix}.priority must be an integer")
        elif not (ContextValidator.MIN_PRIORITY <= goal.priority <= ContextValidator.MAX_PRIORITY):
            errors.append(
                f"{prefix}.priority must be between "
                f"{ContextValidator.MIN_PRIORITY} and {ContextValidator.MAX_PRIORITY}"
            )

        if goal.status not in ContextValidator.VALID_GOAL_STATUSES:
            errors.append(
                f"{prefix}.status must be one of: "
                f"{', '.join(sorted(ContextValidator.VALID_GOAL_STATUSES))}"
            )

        return errors

    @staticmethod
    def _validate_decision(decision, index: int) -> List[str]:
        """Validate a Decision instance."""
        errors = []
        prefix = f"decisions[{index}]"

        if not decision.id:
            errors.append(f"{prefix}.id is required")

        if not decision.description:
            errors.append(f"{prefix}.description is required")

        if not decision.rationale:
            errors.append(f"{prefix}.rationale is required")

        return errors

    @staticmethod
    def _validate_pattern(pattern, index: int) -> List[str]:
        """Validate a Pattern instance."""
        errors = []
        prefix = f"patterns[{index}]"

        if not pattern.id:
            errors.append(f"{prefix}.id is required")

        if not pattern.name:
            errors.append(f"{prefix}.name is required")

        if not isinstance(pattern.frequency, int) or pattern.frequency < 0:
            errors.append(f"{prefix}.frequency must be a non-negative integer")

        return errors

    @staticmethod
    def _validate_mistake(mistake, index: int) -> List[str]:
        """Validate a Mistake instance."""
        errors = []
        prefix = f"mistakes[{index}]"

        if not mistake.id:
            errors.append(f"{prefix}.id is required")

        if not mistake.description:
            errors.append(f"{prefix}.description is required")

        if mistake.impact not in ContextValidator.VALID_IMPACTS:
            errors.append(
                f"{prefix}.impact must be one of: "
                f"{', '.join(sorted(ContextValidator.VALID_IMPACTS))}"
            )

        return errors

    @staticmethod
    def _validate_file_mapping(file_mapping, index: int) -> List[str]:
        """Validate a FileMapping instance."""
        errors = []
        prefix = f"file_map[{index}]"

        if not file_mapping.path:
            errors.append(f"{prefix}.path is required")

        if not file_mapping.purpose:
            errors.append(f"{prefix}.purpose is required")

        return errors

    @staticmethod
    def _validate_dependency(dependency, index: int) -> List[str]:
        """Validate a Dependency instance."""
        errors = []
        prefix = f"dependencies[{index}]"

        if not dependency.name:
            errors.append(f"{prefix}.name is required")

        if not dependency.purpose:
            errors.append(f"{prefix}.purpose is required")

        return errors

    @staticmethod
    def _validate_risk(risk, index: int) -> List[str]:
        """Validate a Risk instance."""
        errors = []
        prefix = f"risks[{index}]"

        if not risk.id:
            errors.append(f"{prefix}.id is required")

        if not risk.description:
            errors.append(f"{prefix}.description is required")

        if risk.severity not in ContextValidator.VALID_SEVERITIES:
            errors.append(
                f"{prefix}.severity must be one of: "
                f"{', '.join(sorted(ContextValidator.VALID_SEVERITIES))}"
            )

        if risk.likelihood not in ContextValidator.VALID_LIKELIHOODS:
            errors.append(
                f"{prefix}.likelihood must be one of: "
                f"{', '.join(sorted(ContextValidator.VALID_LIKELIHOODS))}"
            )

        if risk.status not in ContextValidator.VALID_RISK_STATUSES:
            errors.append(
                f"{prefix}.status must be one of: "
                f"{', '.join(sorted(ContextValidator.VALID_RISK_STATUSES))}"
            )

        return errors

    @staticmethod
    def is_valid(context: LeaderContext) -> bool:
        """
        Check if a LeaderContext instance is valid.

        Args:
            context: LeaderContext instance to validate

        Returns:
            True if valid, False otherwise
        """
        return len(ContextValidator.validate(context)) == 0
