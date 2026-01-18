"""
Leader Context Initializer
==========================

Provides utilities for creating and initializing LeaderContext instances
from various sources (empty, PROJECT.md, STATE.md, previous phase).
"""

import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from .models import (
    Dependency,
    FileMapping,
    Goal,
    LeaderContext,
    Risk,
)

if TYPE_CHECKING:
    from .storage import ContextStorage


class ContextInitializer:
    """
    Utility class for initializing LeaderContext instances.

    Provides static methods to create contexts from various sources:
    - Empty context for new phases
    - From PROJECT.md for initial project context
    - From STATE.md for current state information
    - Inherited from previous phase
    """

    @staticmethod
    def create_empty(project_id: str, phase: int) -> LeaderContext:
        """
        Create an empty LeaderContext.

        Args:
            project_id: Unique identifier for the project
            phase: Phase number

        Returns:
            Empty LeaderContext instance
        """
        return LeaderContext(
            project_id=project_id,
            phase=phase,
            goals=[],
            constraints=[],
            decisions=[],
            patterns=[],
            mistakes=[],
            file_map=[],
            dependencies=[],
            risks=[],
            progress={},
            domain={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @staticmethod
    def from_project_md(project_md_path: str) -> LeaderContext:
        """
        Extract initial context from PROJECT.md.

        Parses PROJECT.md to extract:
        - Project ID (from title or filename)
        - Constraints
        - Domain information
        - Dependencies (if listed)

        Args:
            project_md_path: Path to PROJECT.md file

        Returns:
            LeaderContext with extracted information
        """
        path = Path(project_md_path)

        if not path.exists():
            raise FileNotFoundError(f"PROJECT.md not found: {project_md_path}")

        content = path.read_text(encoding='utf-8')

        # Extract project ID from title or path
        project_id = ContextInitializer._extract_project_id(content, path)

        # Create context
        context = ContextInitializer.create_empty(project_id, phase=1)

        # Extract constraints
        context.constraints = ContextInitializer._extract_constraints(content)

        # Extract domain information
        context.domain = ContextInitializer._extract_domain(content)

        # Extract dependencies
        context.dependencies = ContextInitializer._extract_dependencies(content)

        # Extract goals from objectives section
        context.goals = ContextInitializer._extract_goals(content)

        # Extract risks
        context.risks = ContextInitializer._extract_risks(content)

        return context

    @staticmethod
    def from_state_md(state_md_path: str) -> LeaderContext:
        """
        Extract context updates from STATE.md.

        Parses STATE.md to extract:
        - Current phase
        - Progress information
        - Decisions made

        Args:
            state_md_path: Path to STATE.md file

        Returns:
            LeaderContext with state information
        """
        path = Path(state_md_path)

        if not path.exists():
            raise FileNotFoundError(f"STATE.md not found: {state_md_path}")

        content = path.read_text(encoding='utf-8')

        # Extract project ID (may be in title or metadata)
        project_id = ContextInitializer._extract_project_id_from_state(content, path)

        # Extract current phase
        phase = ContextInitializer._extract_current_phase(content)

        # Create context
        context = ContextInitializer.create_empty(project_id, phase)

        # Extract progress
        context.progress = ContextInitializer._extract_progress(content)

        # Extract file map from recent changes
        context.file_map = ContextInitializer._extract_file_map(content)

        return context

    @staticmethod
    def inherit_from_phase(
        storage: 'ContextStorage',
        previous_phase: int
    ) -> LeaderContext:
        """
        Create new context by inheriting from previous phase.

        Inheritance rules:
        - Incomplete goals are carried over
        - All decisions are inherited
        - All patterns are inherited
        - Dependencies are inherited
        - Risks are inherited (unless mitigated)
        - Phase number is incremented

        Args:
            storage: ContextStorage instance
            previous_phase: Phase number to inherit from

        Returns:
            New LeaderContext with inherited data

        Raises:
            ValueError: If previous phase context not found
        """
        previous = storage.load(previous_phase)

        if previous is None:
            raise ValueError(f"No context found for phase {previous_phase}")

        new_phase = previous_phase + 1

        # Create new context
        context = LeaderContext(
            project_id=previous.project_id,
            phase=new_phase,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Inherit incomplete goals (not completed or deferred)
        context.goals = [
            Goal(
                id=g.id,
                description=g.description,
                priority=g.priority,
                status=g.status if g.status != 'completed' else 'completed',
                created_at=g.created_at,
                completed_at=g.completed_at,
            )
            for g in previous.goals
            if g.status == 'active'  # Only carry over active goals
        ]

        # Inherit all constraints
        context.constraints = list(previous.constraints)

        # Inherit all decisions
        context.decisions = list(previous.decisions)

        # Inherit all patterns
        context.patterns = list(previous.patterns)

        # Inherit mistakes (for learning, don't repeat them)
        context.mistakes = list(previous.mistakes)

        # Inherit file map
        context.file_map = list(previous.file_map)

        # Inherit dependencies
        context.dependencies = list(previous.dependencies)

        # Inherit open/accepted risks only
        context.risks = [
            r for r in previous.risks
            if r.status in ('open', 'accepted')
        ]

        # Inherit domain knowledge
        context.domain = dict(previous.domain)

        # Inherit and update progress
        context.progress = dict(previous.progress)
        context.progress['inherited_from_phase'] = previous_phase

        return context

    @staticmethod
    def _extract_project_id(content: str, path: Path) -> str:
        """Extract project ID from PROJECT.md content or path."""
        # Try to find project name in title (# Project Name)
        title_match = re.search(r'^#\s+(.+?)(?:\s*[-:].*)?$', content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
            # Convert to ID format (lowercase, replace spaces with dashes)
            return re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

        # Try to find project_id in metadata
        id_match = re.search(r'project[_-]?id:\s*(.+)', content, re.IGNORECASE)
        if id_match:
            return id_match.group(1).strip()

        # Fall back to parent directory name
        return path.parent.name

    @staticmethod
    def _extract_project_id_from_state(content: str, path: Path) -> str:
        """Extract project ID from STATE.md content or path."""
        # Try to find project reference
        project_match = re.search(r'project:\s*(.+)', content, re.IGNORECASE)
        if project_match:
            return project_match.group(1).strip()

        # Fall back to parent directory name
        return path.parent.name

    @staticmethod
    def _extract_constraints(content: str) -> List[str]:
        """Extract constraints from markdown content."""
        constraints = []

        # Look for Constraints section
        constraint_section = re.search(
            r'##\s*Constraints?\s*\n(.*?)(?=\n##|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )

        if constraint_section:
            section_content = constraint_section.group(1)
            # Extract bullet points
            for match in re.finditer(r'^[-*]\s+(.+)$', section_content, re.MULTILINE):
                constraints.append(match.group(1).strip())

        # Also look for "must", "cannot", "should not" patterns
        requirement_patterns = [
            r'must\s+(.+?)(?:\.|$)',
            r'cannot\s+(.+?)(?:\.|$)',
            r'should\s+not\s+(.+?)(?:\.|$)',
        ]

        for pattern in requirement_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                constraint = match.group(0).strip().rstrip('.')
                if constraint and constraint not in constraints:
                    constraints.append(constraint)

        return constraints

    @staticmethod
    def _extract_domain(content: str) -> dict:
        """Extract domain information from markdown content."""
        domain = {}

        # Look for tech stack
        tech_match = re.search(
            r'##\s*Tech(?:nology)?\s*(?:Stack)?\s*\n(.*?)(?=\n##|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )
        if tech_match:
            technologies = []
            for match in re.finditer(r'^[-*]\s+(.+)$', tech_match.group(1), re.MULTILINE):
                technologies.append(match.group(1).strip())
            if technologies:
                domain['technologies'] = technologies

        # Look for architecture
        arch_match = re.search(
            r'##\s*Architecture\s*\n(.*?)(?=\n##|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )
        if arch_match:
            domain['architecture'] = arch_match.group(1).strip()

        # Look for key terms/glossary
        glossary_match = re.search(
            r'##\s*(?:Glossary|Terms|Terminology)\s*\n(.*?)(?=\n##|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )
        if glossary_match:
            terms = {}
            for match in re.finditer(
                r'^[-*]\s*\*\*(.+?)\*\*:\s*(.+)$',
                glossary_match.group(1),
                re.MULTILINE
            ):
                terms[match.group(1).strip()] = match.group(2).strip()
            if terms:
                domain['glossary'] = terms

        return domain

    @staticmethod
    def _extract_dependencies(content: str) -> List[Dependency]:
        """Extract dependencies from markdown content."""
        dependencies = []

        # Look for Dependencies section
        dep_section = re.search(
            r'##\s*Dependencies?\s*\n(.*?)(?=\n##|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )

        if dep_section:
            section_content = dep_section.group(1)

            # Match patterns like: - package@version - purpose
            # or: - package (version) - purpose
            for match in re.finditer(
                r'^[-*]\s+([^\s@(]+)(?:[@(]([^)]+)[)]?)?\s*[-:]?\s*(.+)?$',
                section_content,
                re.MULTILINE
            ):
                name = match.group(1).strip()
                version = match.group(2).strip() if match.group(2) else None
                purpose = match.group(3).strip() if match.group(3) else "Required dependency"

                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    purpose=purpose,
                    required=True,
                ))

        return dependencies

    @staticmethod
    def _extract_goals(content: str) -> List[Goal]:
        """Extract goals/objectives from markdown content."""
        goals = []

        # Look for Objectives, Goals, or Requirements section
        goal_section = re.search(
            r'##\s*(?:Objectives?|Goals?|Requirements?)\s*\n(.*?)(?=\n##|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )

        if goal_section:
            section_content = goal_section.group(1)
            now = datetime.now()

            # Extract bullet points
            for i, match in enumerate(
                re.finditer(r'^[-*]\s+(.+)$', section_content, re.MULTILINE)
            ):
                description = match.group(1).strip()
                goals.append(Goal(
                    id=f"goal-{uuid.uuid4().hex[:8]}",
                    description=description,
                    priority=min(i + 1, 5),  # Priority 1-5
                    status='active',
                    created_at=now,
                ))

        return goals

    @staticmethod
    def _extract_risks(content: str) -> List[Risk]:
        """Extract risks from markdown content."""
        risks = []

        # Look for Risks section
        risk_section = re.search(
            r'##\s*Risks?\s*\n(.*?)(?=\n##|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )

        if risk_section:
            section_content = risk_section.group(1)

            # Extract bullet points
            for match in re.finditer(r'^[-*]\s+(.+)$', section_content, re.MULTILINE):
                description = match.group(1).strip()

                # Try to determine severity from keywords
                severity = 'medium'
                if any(word in description.lower() for word in ['critical', 'severe', 'blocker']):
                    severity = 'critical'
                elif any(word in description.lower() for word in ['high', 'major', 'significant']):
                    severity = 'high'
                elif any(word in description.lower() for word in ['low', 'minor', 'trivial']):
                    severity = 'low'

                risks.append(Risk(
                    id=f"risk-{uuid.uuid4().hex[:8]}",
                    description=description,
                    severity=severity,
                    likelihood='medium',
                    mitigation=None,
                    status='open',
                ))

        return risks

    @staticmethod
    def _extract_current_phase(content: str) -> int:
        """Extract current phase number from STATE.md."""
        # Look for phase indicator
        phase_match = re.search(
            r'(?:current\s+)?phase[:\s]+(\d+)',
            content,
            re.IGNORECASE
        )

        if phase_match:
            return int(phase_match.group(1))

        # Default to phase 1
        return 1

    @staticmethod
    def _extract_progress(content: str) -> dict:
        """Extract progress information from STATE.md."""
        progress = {}

        # Look for Progress section
        progress_section = re.search(
            r'##\s*Progress\s*\n(.*?)(?=\n##|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )

        if progress_section:
            section_content = progress_section.group(1)

            # Look for percentage
            percent_match = re.search(r'(\d+)\s*%', section_content)
            if percent_match:
                progress['completion_percent'] = int(percent_match.group(1))

            # Look for completed/total tasks
            tasks_match = re.search(r'(\d+)\s*/\s*(\d+)', section_content)
            if tasks_match:
                progress['completed_tasks'] = int(tasks_match.group(1))
                progress['total_tasks'] = int(tasks_match.group(2))

        return progress

    @staticmethod
    def _extract_file_map(content: str) -> List[FileMapping]:
        """Extract file mappings from STATE.md."""
        file_map = []
        now = datetime.now()

        # Look for Recent Changes or Modified Files section
        files_section = re.search(
            r'##\s*(?:Recent\s+Changes?|Modified\s+Files?|Files?)\s*\n(.*?)(?=\n##|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )

        if files_section:
            section_content = files_section.group(1)

            # Match file paths (common patterns)
            for match in re.finditer(
                r'^[-*]\s+`?([^\s`]+\.[a-zA-Z]+)`?\s*[-:]?\s*(.+)?$',
                section_content,
                re.MULTILINE
            ):
                path = match.group(1).strip()
                purpose = match.group(2).strip() if match.group(2) else "Modified file"

                file_map.append(FileMapping(
                    path=path,
                    purpose=purpose,
                    last_modified=now,
                    related_goals=[],
                ))

        return file_map

    @staticmethod
    def combine(
        base: LeaderContext,
        *updates: Optional[LeaderContext]
    ) -> LeaderContext:
        """
        Combine a base context with updates.

        Later updates take precedence for scalar values.
        Lists are merged with deduplication.

        Args:
            base: Base context
            *updates: Optional context updates to apply

        Returns:
            Combined LeaderContext
        """
        from .merger import ContextMerger

        contexts = [base]
        for update in updates:
            if update is not None:
                contexts.append(update)

        if len(contexts) == 1:
            return base

        return ContextMerger.merge(contexts)
