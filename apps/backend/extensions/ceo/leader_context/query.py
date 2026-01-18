"""
Leader Context Query
====================

Provides query interfaces for LeaderContext instances.
Enables efficient retrieval and search of goals, decisions,
patterns, mistakes, files, risks, and dependencies.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

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


@dataclass
class QueryFilter:
    """
    Filter criteria for context queries.

    Attributes:
        status: Filter by status value
        priority_min: Minimum priority (inclusive)
        priority_max: Maximum priority (inclusive)
        severity: Filter by severity level
        date_from: Filter items from this date (inclusive)
        date_to: Filter items to this date (inclusive)
        keywords: List of keywords to search for
    """
    status: Optional[str] = None
    priority_min: Optional[int] = None
    priority_max: Optional[int] = None
    severity: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    keywords: Optional[List[str]] = None


class ContextQuery:
    """
    Query interface for LeaderContext.

    Provides methods to query and search all aspects of a LeaderContext,
    including goals, decisions, patterns, mistakes, files, risks,
    and dependencies.

    Attributes:
        context: The LeaderContext instance to query
    """

    def __init__(self, context: LeaderContext):
        """
        Initialize ContextQuery.

        Args:
            context: LeaderContext instance to query
        """
        self.context = context

    # ==========================================================================
    # Goal Queries
    # ==========================================================================

    def get_active_goals(self) -> List[Goal]:
        """
        Get all active goals.

        Returns:
            List of goals with status 'active'
        """
        return [g for g in self.context.goals if g.status == 'active']

    def get_goals_by_priority(self, min_priority: int = 1) -> List[Goal]:
        """
        Get goals by priority threshold.

        Args:
            min_priority: Minimum priority level (1 is highest)

        Returns:
            List of goals with priority >= min_priority, sorted by priority
        """
        return sorted(
            [g for g in self.context.goals if g.priority >= min_priority],
            key=lambda g: g.priority,
            reverse=True
        )

    def find_goals(self, keyword: str) -> List[Goal]:
        """
        Search goals by keyword.

        Args:
            keyword: Search term to match in goal descriptions

        Returns:
            List of goals containing the keyword
        """
        keyword_lower = keyword.lower()
        return [
            g for g in self.context.goals
            if keyword_lower in g.description.lower()
        ]

    def get_goal_by_id(self, goal_id: str) -> Optional[Goal]:
        """
        Get a specific goal by ID.

        Args:
            goal_id: The goal ID to find

        Returns:
            Goal if found, None otherwise
        """
        for goal in self.context.goals:
            if goal.id == goal_id:
                return goal
        return None

    def get_completed_goals(self) -> List[Goal]:
        """
        Get all completed goals.

        Returns:
            List of goals with status 'completed'
        """
        return [g for g in self.context.goals if g.status == 'completed']

    # ==========================================================================
    # Decision Queries
    # ==========================================================================

    def get_recent_decisions(self, limit: int = 10) -> List[Decision]:
        """
        Get the most recent decisions.

        Args:
            limit: Maximum number of decisions to return

        Returns:
            List of decisions sorted by date, newest first
        """
        return sorted(
            self.context.decisions,
            key=lambda d: d.made_at,
            reverse=True
        )[:limit]

    def get_decisions_for_goal(self, goal_id: str) -> List[Decision]:
        """
        Get all decisions related to a specific goal.

        Args:
            goal_id: The goal ID to filter by

        Returns:
            List of decisions related to the goal
        """
        return [
            d for d in self.context.decisions
            if goal_id in d.related_goals
        ]

    def find_decisions(self, keyword: str) -> List[Decision]:
        """
        Search decisions by keyword.

        Args:
            keyword: Search term to match in description or rationale

        Returns:
            List of decisions containing the keyword
        """
        keyword_lower = keyword.lower()
        return [
            d for d in self.context.decisions
            if keyword_lower in d.description.lower()
            or keyword_lower in d.rationale.lower()
        ]

    def get_decision_by_id(self, decision_id: str) -> Optional[Decision]:
        """
        Get a specific decision by ID.

        Args:
            decision_id: The decision ID to find

        Returns:
            Decision if found, None otherwise
        """
        for decision in self.context.decisions:
            if decision.id == decision_id:
                return decision
        return None

    # ==========================================================================
    # Pattern Queries
    # ==========================================================================

    def get_frequent_patterns(self, min_frequency: int = 2) -> List[Pattern]:
        """
        Get patterns that occur frequently.

        Args:
            min_frequency: Minimum frequency threshold

        Returns:
            List of patterns with frequency >= min_frequency, sorted by frequency
        """
        return sorted(
            [p for p in self.context.patterns if p.frequency >= min_frequency],
            key=lambda p: p.frequency,
            reverse=True
        )

    def get_recent_patterns(self, limit: int = 5) -> List[Pattern]:
        """
        Get the most recently observed patterns.

        Args:
            limit: Maximum number of patterns to return

        Returns:
            List of patterns sorted by last_seen date, newest first
        """
        return sorted(
            self.context.patterns,
            key=lambda p: p.last_seen,
            reverse=True
        )[:limit]

    def find_patterns(self, keyword: str) -> List[Pattern]:
        """
        Search patterns by keyword.

        Args:
            keyword: Search term to match in name or description

        Returns:
            List of patterns containing the keyword
        """
        keyword_lower = keyword.lower()
        return [
            p for p in self.context.patterns
            if keyword_lower in p.name.lower()
            or keyword_lower in p.description.lower()
        ]

    def get_pattern_by_name(self, name: str) -> Optional[Pattern]:
        """
        Get a pattern by its name.

        Args:
            name: Pattern name to find (case-insensitive)

        Returns:
            Pattern if found, None otherwise
        """
        name_lower = name.lower()
        for pattern in self.context.patterns:
            if pattern.name.lower() == name_lower:
                return pattern
        return None

    # ==========================================================================
    # Mistake Queries
    # ==========================================================================

    def get_unresolved_mistakes(self) -> List[Mistake]:
        """
        Get all unresolved mistakes.

        Returns:
            List of mistakes without a resolution
        """
        return [m for m in self.context.mistakes if m.resolved_at is None]

    def get_high_impact_mistakes(self) -> List[Mistake]:
        """
        Get mistakes with high impact.

        Returns:
            List of mistakes with impact='high'
        """
        return [m for m in self.context.mistakes if m.impact == 'high']

    def get_resolved_mistakes(self) -> List[Mistake]:
        """
        Get all resolved mistakes.

        Returns:
            List of mistakes that have been resolved
        """
        return [m for m in self.context.mistakes if m.resolved_at is not None]

    def find_mistakes(self, keyword: str) -> List[Mistake]:
        """
        Search mistakes by keyword.

        Args:
            keyword: Search term to match in description or resolution

        Returns:
            List of mistakes containing the keyword
        """
        keyword_lower = keyword.lower()
        return [
            m for m in self.context.mistakes
            if keyword_lower in m.description.lower()
            or (m.resolution and keyword_lower in m.resolution.lower())
        ]

    # ==========================================================================
    # FileMapping Queries
    # ==========================================================================

    def get_file_context(self, file_path: str) -> Optional[FileMapping]:
        """
        Get context for a specific file.

        Args:
            file_path: File path to find

        Returns:
            FileMapping if found, None otherwise
        """
        for fm in self.context.file_map:
            if fm.path == file_path:
                return fm
        return None

    def get_files_for_goal(self, goal_id: str) -> List[FileMapping]:
        """
        Get all files related to a specific goal.

        Args:
            goal_id: The goal ID to filter by

        Returns:
            List of file mappings related to the goal
        """
        return [
            fm for fm in self.context.file_map
            if goal_id in fm.related_goals
        ]

    def find_files(self, keyword: str) -> List[FileMapping]:
        """
        Search files by keyword.

        Args:
            keyword: Search term to match in path or purpose

        Returns:
            List of file mappings containing the keyword
        """
        keyword_lower = keyword.lower()
        return [
            fm for fm in self.context.file_map
            if keyword_lower in fm.path.lower()
            or keyword_lower in fm.purpose.lower()
        ]

    def get_recently_modified_files(self, limit: int = 10) -> List[FileMapping]:
        """
        Get the most recently modified files.

        Args:
            limit: Maximum number of files to return

        Returns:
            List of file mappings sorted by last_modified, newest first
        """
        return sorted(
            self.context.file_map,
            key=lambda f: f.last_modified,
            reverse=True
        )[:limit]

    # ==========================================================================
    # Risk Queries
    # ==========================================================================

    def get_open_risks(self) -> List[Risk]:
        """
        Get all open risks.

        Returns:
            List of risks with status='open'
        """
        return [r for r in self.context.risks if r.status == 'open']

    def get_critical_risks(self) -> List[Risk]:
        """
        Get critical open risks.

        Returns:
            List of critical risks that are still open
        """
        return [
            r for r in self.context.risks
            if r.severity == 'critical' and r.status == 'open'
        ]

    def get_risks_by_severity(self, severity: str) -> List[Risk]:
        """
        Get risks by severity level.

        Args:
            severity: Severity level ('low', 'medium', 'high', 'critical')

        Returns:
            List of risks with the specified severity
        """
        return [r for r in self.context.risks if r.severity == severity]

    def get_mitigated_risks(self) -> List[Risk]:
        """
        Get all mitigated risks.

        Returns:
            List of risks with status='mitigated'
        """
        return [r for r in self.context.risks if r.status == 'mitigated']

    def find_risks(self, keyword: str) -> List[Risk]:
        """
        Search risks by keyword.

        Args:
            keyword: Search term to match in description or mitigation

        Returns:
            List of risks containing the keyword
        """
        keyword_lower = keyword.lower()
        return [
            r for r in self.context.risks
            if keyword_lower in r.description.lower()
            or (r.mitigation and keyword_lower in r.mitigation.lower())
        ]

    # ==========================================================================
    # Dependency Queries
    # ==========================================================================

    def get_required_dependencies(self) -> List[Dependency]:
        """
        Get all required dependencies.

        Returns:
            List of dependencies marked as required
        """
        return [d for d in self.context.dependencies if d.required]

    def find_dependency(self, name: str) -> Optional[Dependency]:
        """
        Find a dependency by name.

        Args:
            name: Dependency name (case-insensitive)

        Returns:
            Dependency if found, None otherwise
        """
        name_lower = name.lower()
        for d in self.context.dependencies:
            if d.name.lower() == name_lower:
                return d
        return None

    def get_optional_dependencies(self) -> List[Dependency]:
        """
        Get all optional dependencies.

        Returns:
            List of dependencies not marked as required
        """
        return [d for d in self.context.dependencies if not d.required]

    def get_dependencies_for_purpose(self, purpose_keyword: str) -> List[Dependency]:
        """
        Get dependencies matching a purpose keyword.

        Args:
            purpose_keyword: Keyword to match in purpose

        Returns:
            List of dependencies with matching purpose
        """
        keyword_lower = purpose_keyword.lower()
        return [
            d for d in self.context.dependencies
            if keyword_lower in d.purpose.lower()
        ]

    # ==========================================================================
    # Combined Queries
    # ==========================================================================

    def search_all(self, keyword: str) -> Dict[str, List]:
        """
        Search across all context items.

        Args:
            keyword: Search term to match

        Returns:
            Dictionary with search results for each category
        """
        return {
            'goals': self.find_goals(keyword),
            'decisions': self.find_decisions(keyword),
            'files': self.find_files(keyword),
            'patterns': self.find_patterns(keyword),
            'risks': self.find_risks(keyword),
            'mistakes': self.find_mistakes(keyword),
            'dependencies': self.get_dependencies_for_purpose(keyword),
        }

    def get_summary(self) -> Dict:
        """
        Get a summary of the context.

        Returns:
            Dictionary with context statistics
        """
        return {
            'project_id': self.context.project_id,
            'phase': self.context.phase,
            'active_goals': len(self.get_active_goals()),
            'completed_goals': len(self.get_completed_goals()),
            'total_goals': len(self.context.goals),
            'decisions_count': len(self.context.decisions),
            'patterns_count': len(self.context.patterns),
            'unresolved_mistakes': len(self.get_unresolved_mistakes()),
            'resolved_mistakes': len(self.get_resolved_mistakes()),
            'files_tracked': len(self.context.file_map),
            'dependencies_count': len(self.context.dependencies),
            'required_dependencies': len(self.get_required_dependencies()),
            'open_risks': len(self.get_open_risks()),
            'critical_risks': len(self.get_critical_risks()),
            'mitigated_risks': len(self.get_mitigated_risks()),
            'constraints_count': len(self.context.constraints),
            'created_at': self.context.created_at.isoformat(),
            'updated_at': self.context.updated_at.isoformat(),
        }

    def get_context_for_session(self, topic: str) -> Dict:
        """
        Get relevant context for a specific work session.

        Retrieves context items most relevant to the given topic,
        useful for initializing agent sessions.

        Args:
            topic: The topic or task for the session

        Returns:
            Dictionary with relevant context items
        """
        relevant = self.search_all(topic)

        return {
            'project_id': self.context.project_id,
            'phase': self.context.phase,
            'active_goals': [
                {'id': g.id, 'description': g.description, 'priority': g.priority}
                for g in self.get_active_goals()
            ],
            'relevant_goals': [
                {'id': g.id, 'description': g.description, 'priority': g.priority}
                for g in relevant['goals']
            ],
            'relevant_decisions': [
                {'id': d.id, 'description': d.description, 'rationale': d.rationale}
                for d in relevant['decisions']
            ],
            'relevant_files': [
                {'path': f.path, 'purpose': f.purpose}
                for f in relevant['files']
            ],
            'relevant_patterns': [
                {'name': p.name, 'description': p.description}
                for p in relevant['patterns']
            ],
            'open_risks': [
                {'id': r.id, 'description': r.description, 'severity': r.severity}
                for r in self.get_open_risks()
            ],
            'unresolved_mistakes': [
                {'id': m.id, 'description': m.description, 'impact': m.impact}
                for m in self.get_unresolved_mistakes()
            ],
            'constraints': self.context.constraints,
        }

    def apply_filter(
        self,
        items: List,
        query_filter: QueryFilter,
        date_field: str = None,
    ) -> List:
        """
        Apply a QueryFilter to a list of items.

        Args:
            items: List of items to filter
            query_filter: Filter criteria to apply
            date_field: Name of the date attribute for date filtering

        Returns:
            Filtered list of items
        """
        result = items

        # Filter by status
        if query_filter.status is not None:
            result = [
                item for item in result
                if hasattr(item, 'status') and item.status == query_filter.status
            ]

        # Filter by priority range
        if query_filter.priority_min is not None:
            result = [
                item for item in result
                if hasattr(item, 'priority') and item.priority >= query_filter.priority_min
            ]

        if query_filter.priority_max is not None:
            result = [
                item for item in result
                if hasattr(item, 'priority') and item.priority <= query_filter.priority_max
            ]

        # Filter by severity
        if query_filter.severity is not None:
            result = [
                item for item in result
                if hasattr(item, 'severity') and item.severity == query_filter.severity
            ]

        # Filter by date range
        if date_field and (query_filter.date_from or query_filter.date_to):
            filtered = []
            for item in result:
                if hasattr(item, date_field):
                    item_date = getattr(item, date_field)
                    if item_date:
                        if query_filter.date_from and item_date < query_filter.date_from:
                            continue
                        if query_filter.date_to and item_date > query_filter.date_to:
                            continue
                        filtered.append(item)
            result = filtered

        # Filter by keywords
        if query_filter.keywords:
            filtered = []
            for item in result:
                item_text = ""
                for attr in ['description', 'name', 'purpose', 'rationale', 'path']:
                    if hasattr(item, attr):
                        value = getattr(item, attr)
                        if value:
                            item_text += " " + str(value).lower()

                if any(kw.lower() in item_text for kw in query_filter.keywords):
                    filtered.append(item)
            result = filtered

        return result
