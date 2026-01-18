"""
Error Logger
============

Manages error logging, pattern detection, and resolution tracking.
"""

import hashlib
import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .error_models import (
    ErrorCategory,
    ErrorContext,
    ErrorLog,
    ErrorPattern,
    ErrorSeverity,
)
from .error_serializer import ErrorLogSerializer


class ErrorLogger:
    """
    Error log recording and management.

    Handles error logging with automatic pattern detection, grouping
    of similar errors, and resolution tracking. Errors are persisted
    to JSON files organized by phase.

    Attributes:
        project_path: Path to the project root
        phase: Current phase number
        errors_dir: Directory for error log files
    """

    def __init__(self, project_path: str, phase: int):
        """
        Initialize ErrorLogger.

        Args:
            project_path: Path to the project root
            phase: Current phase number
        """
        self.project_path = project_path
        self.phase = phase
        self.errors_dir = Path(project_path) / ".planning" / "leader_context" / "errors"
        self.errors_dir.mkdir(parents=True, exist_ok=True)

        self._errors: List[ErrorLog] = []
        self._patterns: Dict[str, ErrorPattern] = {}
        self._load_errors()

    def log_error(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        stack_trace: Optional[str] = None,
        context: Optional[ErrorContext] = None,
        checkpoint_id: Optional[str] = None,
    ) -> ErrorLog:
        """
        Record an error.

        If an identical error (same hash) already exists, increments
        the occurrence count instead of creating a new entry.

        Args:
            message: Error message description
            severity: Error severity level
            category: Error category type
            stack_trace: Full stack trace if available
            context: Execution context when error occurred
            checkpoint_id: Associated checkpoint ID if any

        Returns:
            The created or updated ErrorLog entry
        """
        error_hash = self._compute_error_hash(message, category)

        # Check for existing identical error
        existing = self._find_by_hash(error_hash)
        if existing:
            existing.occurrence_count += 1
            existing.last_seen = datetime.now()
            self._save_errors()
            return existing

        now = datetime.now()
        error = ErrorLog(
            id=f"err-{uuid.uuid4().hex[:8]}",
            phase=self.phase,
            timestamp=now,
            severity=severity,
            category=category,
            message=message,
            stack_trace=stack_trace,
            context=context or ErrorContext(),
            error_hash=error_hash,
            first_seen=now,
            last_seen=now,
            checkpoint_id=checkpoint_id,
        )

        self._errors.append(error)
        self._update_patterns(error)
        self._save_errors()

        return error

    def resolve_error(self, error_id: str, resolution: str) -> bool:
        """
        Mark an error as resolved.

        Args:
            error_id: ID of the error to resolve
            resolution: Description of how the error was fixed

        Returns:
            True if error was found and resolved, False otherwise
        """
        error = self._find_by_id(error_id)
        if error:
            error.resolved = True
            error.resolution = resolution
            error.resolved_at = datetime.now()

            # Update pattern with suggested fix
            if error.error_hash and error.error_hash in self._patterns:
                pattern = self._patterns[error.error_hash]
                if not pattern.suggested_fix:
                    pattern.suggested_fix = resolution

            self._save_errors()
            return True
        return False

    def get_unresolved_errors(self) -> List[ErrorLog]:
        """
        Get all unresolved errors.

        Returns:
            List of errors that haven't been resolved
        """
        return [e for e in self._errors if not e.resolved]

    def get_critical_errors(self) -> List[ErrorLog]:
        """
        Get all critical severity errors.

        Returns:
            List of errors with CRITICAL severity
        """
        return [e for e in self._errors if e.severity == ErrorSeverity.CRITICAL]

    def get_errors_by_category(self, category: ErrorCategory) -> List[ErrorLog]:
        """
        Get errors by category.

        Args:
            category: Error category to filter by

        Returns:
            List of errors in the specified category
        """
        return [e for e in self._errors if e.category == category]

    def get_frequent_errors(self, min_count: int = 2) -> List[ErrorLog]:
        """
        Get frequently occurring errors.

        Args:
            min_count: Minimum occurrence count (default: 2)

        Returns:
            List of errors that occurred at least min_count times
        """
        return [e for e in self._errors if e.occurrence_count >= min_count]

    def get_error_patterns(self) -> List[ErrorPattern]:
        """
        Get all detected error patterns.

        Returns:
            List of error patterns
        """
        return list(self._patterns.values())

    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get error statistics summary.

        Returns:
            Dictionary containing error statistics including:
            - total_errors: Total number of unique errors
            - unresolved: Count of unresolved errors
            - critical: Count of critical errors
            - by_category: Breakdown by category
            - by_severity: Breakdown by severity
            - patterns_detected: Number of patterns found
            - most_frequent: Top frequent errors
        """
        return {
            "total_errors": len(self._errors),
            "unresolved": len(self.get_unresolved_errors()),
            "critical": len(self.get_critical_errors()),
            "by_category": {
                cat.value: len(self.get_errors_by_category(cat))
                for cat in ErrorCategory
            },
            "by_severity": {
                sev.value: len([e for e in self._errors if e.severity == sev])
                for sev in ErrorSeverity
            },
            "patterns_detected": len(self._patterns),
            "most_frequent": self._get_most_frequent_errors(5),
        }

    def suggest_fixes(self, error_id: str) -> List[str]:
        """
        Suggest fixes for an error based on past resolutions.

        Args:
            error_id: ID of the error to get suggestions for

        Returns:
            List of suggested fix descriptions
        """
        error = self._find_by_id(error_id)
        if not error:
            return []

        suggestions = []

        # Check for pattern-based suggestion
        if error.error_hash and error.error_hash in self._patterns:
            pattern = self._patterns[error.error_hash]
            if pattern.suggested_fix:
                suggestions.append(pattern.suggested_fix)

        # Look for resolved errors in the same category
        for resolved in self._errors:
            if resolved.resolved and resolved.category == error.category:
                if resolved.resolution and resolved.resolution not in suggestions:
                    suggestions.append(resolved.resolution)

        # Return unique suggestions, limited to 5
        return suggestions[:5]

    def get_all_errors(self) -> List[ErrorLog]:
        """
        Get all logged errors.

        Returns:
            List of all error logs
        """
        return list(self._errors)

    def get_error_by_id(self, error_id: str) -> Optional[ErrorLog]:
        """
        Get a specific error by ID.

        Args:
            error_id: ID of the error to retrieve

        Returns:
            ErrorLog if found, None otherwise
        """
        return self._find_by_id(error_id)

    def _compute_error_hash(self, message: str, category: ErrorCategory) -> str:
        """
        Compute a hash for error grouping.

        Normalizes the message by replacing numbers and paths
        to group similar errors together.

        Args:
            message: Error message
            category: Error category

        Returns:
            12-character hash string
        """
        # Normalize message by replacing variable parts
        normalized = re.sub(r'[0-9]+', 'N', message)
        normalized = re.sub(r'/[^\s]+', '/PATH', normalized)
        normalized = re.sub(r'\\[^\s]+', r'\\PATH', normalized)
        normalized = re.sub(r'0x[a-fA-F0-9]+', '0xADDR', normalized)
        content = f"{category.value}:{normalized}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _update_patterns(self, error: ErrorLog) -> None:
        """
        Update error patterns based on new error.

        Args:
            error: New error log entry
        """
        if not error.error_hash:
            return

        if error.error_hash not in self._patterns:
            self._patterns[error.error_hash] = ErrorPattern(
                id=f"pat-{error.error_hash}",
                error_hash=error.error_hash,
                category=error.category,
                message_pattern=error.message,
                occurrence_count=1,
                first_seen=error.timestamp,
                last_seen=error.timestamp,
                example_error_ids=[error.id],
            )
        else:
            pattern = self._patterns[error.error_hash]
            pattern.occurrence_count += 1
            pattern.last_seen = error.timestamp
            if len(pattern.example_error_ids) < 5:
                pattern.example_error_ids.append(error.id)

    def _load_errors(self) -> None:
        """Load errors from file."""
        errors_file = self.errors_dir / f"errors_{self.phase}.json"
        if errors_file.exists():
            try:
                with open(errors_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._errors = [
                        ErrorLogSerializer.error_from_dict(e)
                        for e in data.get("errors", [])
                    ]
                    self._patterns = {
                        p["error_hash"]: ErrorLogSerializer.pattern_from_dict(p)
                        for p in data.get("patterns", [])
                    }
            except (json.JSONDecodeError, KeyError) as e:
                # If file is corrupted, start fresh
                self._errors = []
                self._patterns = {}

    def _save_errors(self) -> None:
        """Save errors to file."""
        errors_file = self.errors_dir / f"errors_{self.phase}.json"
        data = {
            "phase": self.phase,
            "last_updated": datetime.now().isoformat(),
            "errors": [ErrorLogSerializer.error_to_dict(e) for e in self._errors],
            "patterns": [
                ErrorLogSerializer.pattern_to_dict(p)
                for p in self._patterns.values()
            ],
        }
        with open(errors_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _find_by_id(self, error_id: str) -> Optional[ErrorLog]:
        """
        Find error by ID.

        Args:
            error_id: Error ID to search for

        Returns:
            ErrorLog if found, None otherwise
        """
        for error in self._errors:
            if error.id == error_id:
                return error
        return None

    def _find_by_hash(self, error_hash: str) -> Optional[ErrorLog]:
        """
        Find first unresolved error with matching hash.

        Args:
            error_hash: Hash to search for

        Returns:
            First matching unresolved ErrorLog, or None
        """
        for error in self._errors:
            if error.error_hash == error_hash and not error.resolved:
                return error
        return None

    def _get_most_frequent_errors(self, limit: int) -> List[Dict[str, Any]]:
        """
        Get the most frequently occurring errors.

        Args:
            limit: Maximum number of errors to return

        Returns:
            List of dictionaries with error info and count
        """
        sorted_errors = sorted(
            self._errors,
            key=lambda e: e.occurrence_count,
            reverse=True,
        )
        return [
            {
                "id": e.id,
                "message": e.message[:100],
                "category": e.category.value,
                "severity": e.severity.value,
                "count": e.occurrence_count,
            }
            for e in sorted_errors[:limit]
        ]
