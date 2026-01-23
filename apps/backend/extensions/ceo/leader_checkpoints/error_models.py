"""
Error Log Models
================

Data models for the error logging system including severity levels,
error categories, context, and pattern detection structures.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ErrorSeverity(Enum):
    """
    Error severity levels.

    Defines the impact level of an error:
    - WARNING: Non-critical issue that doesn't block execution
    - ERROR: Significant issue that may affect results
    - CRITICAL: Severe issue requiring immediate attention
    """
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """
    Error category types.

    Classifies errors by their nature for easier analysis:
    - SYNTAX: Code syntax errors
    - RUNTIME: Errors during execution
    - LOGIC: Logical errors in implementation
    - INTEGRATION: Issues with external service integration
    - CONFIGURATION: Configuration or setup errors
    - PERMISSION: Access or permission denied errors
    - NETWORK: Network connectivity issues
    - TIMEOUT: Operation timeout errors
    - UNKNOWN: Unclassified errors
    """
    SYNTAX = "syntax"
    RUNTIME = "runtime"
    LOGIC = "logic"
    INTEGRATION = "integration"
    CONFIGURATION = "configuration"
    PERMISSION = "permission"
    NETWORK = "network"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """
    Error occurrence context.

    Captures the execution context when an error occurred,
    including file location, function, and agent information.

    Attributes:
        file_path: Path to the file where error occurred
        function_name: Name of the function/method
        line_number: Line number in the source file
        subtask_id: ID of the subtask being executed
        agent_type: Type of agent that encountered the error
        command: Command being executed when error occurred
        input_data: Input data that triggered the error
    """
    file_path: Optional[str] = None
    function_name: Optional[str] = None
    line_number: Optional[int] = None
    subtask_id: Optional[str] = None
    agent_type: Optional[str] = None
    command: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None


@dataclass
class ErrorLog:
    """
    Error log entry.

    Represents a single error occurrence with full context,
    resolution status, and grouping information.

    Attributes:
        id: Unique error identifier (e.g., "err-a1b2c3d4")
        phase: Phase number when error occurred
        timestamp: When the error was logged
        severity: Error severity level
        category: Error category type
        message: Error message description
        stack_trace: Full stack trace if available
        context: Execution context when error occurred
        resolved: Whether the error has been resolved
        resolution: Description of how the error was fixed
        resolved_at: When the error was resolved
        error_hash: Hash for grouping similar errors
        occurrence_count: Number of times this error occurred
        first_seen: When this error was first encountered
        last_seen: When this error was last encountered
        checkpoint_id: Associated checkpoint ID if any
        related_error_ids: IDs of related errors
    """
    id: str
    phase: int
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    stack_trace: Optional[str] = None
    context: ErrorContext = field(default_factory=ErrorContext)

    # Resolution status
    resolved: bool = False
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None

    # Grouping information
    error_hash: Optional[str] = None
    occurrence_count: int = 1
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    # Related references
    checkpoint_id: Optional[str] = None
    related_error_ids: List[str] = field(default_factory=list)


@dataclass
class ErrorPattern:
    """
    Repeated error pattern.

    Tracks patterns of similar errors for analysis and
    automatic fix suggestions.

    Attributes:
        id: Unique pattern identifier (e.g., "pat-a1b2c3d4")
        error_hash: Hash identifying this pattern
        category: Error category for this pattern
        message_pattern: Representative error message
        occurrence_count: Total occurrences of this pattern
        first_seen: When pattern was first detected
        last_seen: When pattern was last seen
        example_error_ids: Sample error IDs belonging to this pattern
        suggested_fix: Suggested resolution based on past fixes
        auto_resolved: Whether this pattern typically auto-resolves
    """
    id: str
    error_hash: str
    category: ErrorCategory
    message_pattern: str
    occurrence_count: int
    first_seen: datetime
    last_seen: datetime
    example_error_ids: List[str] = field(default_factory=list)
    suggested_fix: Optional[str] = None
    auto_resolved: bool = False
