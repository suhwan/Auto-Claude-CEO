"""
Leader Context Merger
=====================

Provides utilities for merging multiple LeaderContext instances
and computing differences between contexts.
"""

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Set

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


class ContextMerger:
    """
    Utility class for merging and comparing LeaderContext instances.

    Provides methods to:
    - Merge multiple contexts into one
    - Calculate differences between two contexts
    """

    @staticmethod
    def merge(contexts: List[LeaderContext]) -> LeaderContext:
        """
        Merge multiple contexts into a single context.

        Merge strategy:
        - goals: Deduplicate by ID, keep latest status
        - decisions: Combine all, sort by time
        - patterns: Deduplicate by ID, sum frequencies
        - mistakes: Keep all unique mistakes
        - file_map: Deduplicate by path, keep latest info
        - dependencies: Deduplicate by name, keep latest version
        - risks: Deduplicate by ID, keep latest status
        - progress: Merge dictionaries, later values override
        - domain: Merge dictionaries, later values override
        - constraints: Unique constraints

        Args:
            contexts: List of LeaderContext instances to merge

        Returns:
            Merged LeaderContext instance

        Raises:
            ValueError: If contexts list is empty
        """
        if not contexts:
            raise ValueError("Cannot merge empty list of contexts")

        if len(contexts) == 1:
            return deepcopy(contexts[0])

        # Sort contexts by phase and updated_at for consistent ordering
        sorted_contexts = sorted(
            contexts,
            key=lambda c: (c.phase, c.updated_at)
        )

        # Use the latest context as base for project_id and phase
        base = sorted_contexts[-1]

        merged = LeaderContext(
            project_id=base.project_id,
            phase=max(c.phase for c in contexts),
            created_at=min(c.created_at for c in contexts),
            updated_at=datetime.now(),
        )

        # Merge goals
        merged.goals = ContextMerger._merge_goals(
            [g for c in sorted_contexts for g in c.goals]
        )

        # Merge decisions (all decisions, sorted by time)
        merged.decisions = ContextMerger._merge_decisions(
            [d for c in sorted_contexts for d in c.decisions]
        )

        # Merge patterns (sum frequencies for same ID)
        merged.patterns = ContextMerger._merge_patterns(
            [p for c in sorted_contexts for p in c.patterns]
        )

        # Merge mistakes (keep all unique)
        merged.mistakes = ContextMerger._merge_mistakes(
            [m for c in sorted_contexts for m in c.mistakes]
        )

        # Merge file_map (latest info per path)
        merged.file_map = ContextMerger._merge_file_mappings(
            [f for c in sorted_contexts for f in c.file_map]
        )

        # Merge dependencies (latest version per name)
        merged.dependencies = ContextMerger._merge_dependencies(
            [d for c in sorted_contexts for d in c.dependencies]
        )

        # Merge risks (latest status per ID)
        merged.risks = ContextMerger._merge_risks(
            [r for c in sorted_contexts for r in c.risks]
        )

        # Merge constraints (unique)
        all_constraints: Set[str] = set()
        for ctx in sorted_contexts:
            all_constraints.update(ctx.constraints)
        merged.constraints = sorted(all_constraints)

        # Merge progress (later values override)
        merged.progress = {}
        for ctx in sorted_contexts:
            merged.progress.update(ctx.progress)

        # Merge domain (later values override)
        merged.domain = {}
        for ctx in sorted_contexts:
            merged.domain.update(ctx.domain)

        return merged

    @staticmethod
    def _merge_goals(goals: List[Goal]) -> List[Goal]:
        """Merge goals, keeping latest status per ID."""
        goal_map: Dict[str, Goal] = {}

        for goal in goals:
            if goal.id not in goal_map:
                goal_map[goal.id] = deepcopy(goal)
            else:
                existing = goal_map[goal.id]
                # Keep the one with later created_at, or if same, prefer completed
                if goal.created_at > existing.created_at:
                    goal_map[goal.id] = deepcopy(goal)
                elif goal.status == 'completed' and existing.status != 'completed':
                    goal_map[goal.id] = deepcopy(goal)

        return sorted(goal_map.values(), key=lambda g: (g.priority, g.created_at))

    @staticmethod
    def _merge_decisions(decisions: List[Decision]) -> List[Decision]:
        """Merge decisions, deduplicate by ID, sort by time."""
        decision_map: Dict[str, Decision] = {}

        for decision in decisions:
            if decision.id not in decision_map:
                decision_map[decision.id] = deepcopy(decision)
            # Keep first occurrence for same ID

        return sorted(decision_map.values(), key=lambda d: d.made_at)

    @staticmethod
    def _merge_patterns(patterns: List[Pattern]) -> List[Pattern]:
        """Merge patterns, sum frequencies for same ID."""
        pattern_map: Dict[str, Pattern] = {}

        for pattern in patterns:
            if pattern.id not in pattern_map:
                pattern_map[pattern.id] = deepcopy(pattern)
            else:
                existing = pattern_map[pattern.id]
                # Sum frequencies
                existing.frequency += pattern.frequency
                # Update last_seen to latest
                if pattern.last_seen > existing.last_seen:
                    existing.last_seen = pattern.last_seen
                # Keep earliest first_seen
                if pattern.first_seen < existing.first_seen:
                    existing.first_seen = pattern.first_seen

        return sorted(
            pattern_map.values(),
            key=lambda p: p.frequency,
            reverse=True
        )

    @staticmethod
    def _merge_mistakes(mistakes: List[Mistake]) -> List[Mistake]:
        """Merge mistakes, keep all unique by ID."""
        mistake_map: Dict[str, Mistake] = {}

        for mistake in mistakes:
            if mistake.id not in mistake_map:
                mistake_map[mistake.id] = deepcopy(mistake)
            else:
                existing = mistake_map[mistake.id]
                # If new one has resolution and old doesn't, update
                if mistake.resolution and not existing.resolution:
                    existing.resolution = mistake.resolution
                    existing.resolved_at = mistake.resolved_at

        return sorted(mistake_map.values(), key=lambda m: m.occurred_at)

    @staticmethod
    def _merge_file_mappings(file_mappings: List[FileMapping]) -> List[FileMapping]:
        """Merge file mappings, keep latest info per path."""
        mapping_map: Dict[str, FileMapping] = {}

        for mapping in file_mappings:
            if mapping.path not in mapping_map:
                mapping_map[mapping.path] = deepcopy(mapping)
            else:
                existing = mapping_map[mapping.path]
                # Keep the one with later last_modified
                if mapping.last_modified > existing.last_modified:
                    mapping_map[mapping.path] = deepcopy(mapping)
                # Merge related_goals
                all_goals = set(existing.related_goals) | set(mapping.related_goals)
                mapping_map[mapping.path].related_goals = sorted(all_goals)

        return sorted(mapping_map.values(), key=lambda f: f.path)

    @staticmethod
    def _merge_dependencies(dependencies: List[Dependency]) -> List[Dependency]:
        """Merge dependencies, keep latest version per name."""
        dep_map: Dict[str, Dependency] = {}

        for dep in dependencies:
            if dep.name not in dep_map:
                dep_map[dep.name] = deepcopy(dep)
            else:
                existing = dep_map[dep.name]
                # Keep newer version if specified
                if dep.version and (not existing.version or dep.version > existing.version):
                    dep_map[dep.name] = deepcopy(dep)

        return sorted(dep_map.values(), key=lambda d: d.name)

    @staticmethod
    def _merge_risks(risks: List[Risk]) -> List[Risk]:
        """Merge risks, keep latest status per ID."""
        risk_map: Dict[str, Risk] = {}

        # Status priority: mitigated > accepted > open
        status_priority = {'open': 0, 'accepted': 1, 'mitigated': 2}

        for risk in risks:
            if risk.id not in risk_map:
                risk_map[risk.id] = deepcopy(risk)
            else:
                existing = risk_map[risk.id]
                # Prefer higher priority status
                if status_priority.get(risk.status, 0) > status_priority.get(existing.status, 0):
                    risk_map[risk.id] = deepcopy(risk)
                elif risk.mitigation and not existing.mitigation:
                    existing.mitigation = risk.mitigation

        # Sort by severity (critical first) then likelihood
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        likelihood_order = {'high': 0, 'medium': 1, 'low': 2}

        return sorted(
            risk_map.values(),
            key=lambda r: (
                severity_order.get(r.severity, 4),
                likelihood_order.get(r.likelihood, 3)
            )
        )

    @staticmethod
    def diff(old: LeaderContext, new: LeaderContext) -> Dict[str, Any]:
        """
        Calculate differences between two contexts.

        Returns a dictionary with added, modified, and removed items
        for each category.

        Args:
            old: Previous context state
            new: Current context state

        Returns:
            Dictionary with structure:
            {
                'goals': {'added': [...], 'modified': [...], 'removed': [...]},
                'decisions': {...},
                'patterns': {...},
                ...
            }
        """
        diff_result = {
            'phase_changed': old.phase != new.phase,
            'old_phase': old.phase,
            'new_phase': new.phase,
            'goals': ContextMerger._diff_goals(old.goals, new.goals),
            'decisions': ContextMerger._diff_decisions(old.decisions, new.decisions),
            'patterns': ContextMerger._diff_patterns(old.patterns, new.patterns),
            'mistakes': ContextMerger._diff_mistakes(old.mistakes, new.mistakes),
            'file_map': ContextMerger._diff_file_mappings(old.file_map, new.file_map),
            'dependencies': ContextMerger._diff_dependencies(
                old.dependencies, new.dependencies
            ),
            'risks': ContextMerger._diff_risks(old.risks, new.risks),
            'constraints': ContextMerger._diff_lists(old.constraints, new.constraints),
            'progress': ContextMerger._diff_dicts(old.progress, new.progress),
            'domain': ContextMerger._diff_dicts(old.domain, new.domain),
        }

        return diff_result

    @staticmethod
    def _diff_goals(old_goals: List[Goal], new_goals: List[Goal]) -> Dict[str, Any]:
        """Diff goals by ID."""
        old_map = {g.id: g for g in old_goals}
        new_map = {g.id: g for g in new_goals}

        added = [g.id for g in new_goals if g.id not in old_map]
        removed = [g.id for g in old_goals if g.id not in new_map]
        modified = []

        for gid in set(old_map.keys()) & set(new_map.keys()):
            old_g, new_g = old_map[gid], new_map[gid]
            if (old_g.status != new_g.status or
                old_g.priority != new_g.priority or
                old_g.description != new_g.description):
                modified.append({
                    'id': gid,
                    'changes': {
                        'status': (old_g.status, new_g.status) if old_g.status != new_g.status else None,
                        'priority': (old_g.priority, new_g.priority) if old_g.priority != new_g.priority else None,
                        'description': (old_g.description, new_g.description) if old_g.description != new_g.description else None,
                    }
                })

        return {'added': added, 'removed': removed, 'modified': modified}

    @staticmethod
    def _diff_decisions(
        old_decisions: List[Decision],
        new_decisions: List[Decision]
    ) -> Dict[str, Any]:
        """Diff decisions by ID."""
        old_ids = {d.id for d in old_decisions}
        new_ids = {d.id for d in new_decisions}

        return {
            'added': sorted(new_ids - old_ids),
            'removed': sorted(old_ids - new_ids),
            'count_change': len(new_decisions) - len(old_decisions),
        }

    @staticmethod
    def _diff_patterns(
        old_patterns: List[Pattern],
        new_patterns: List[Pattern]
    ) -> Dict[str, Any]:
        """Diff patterns by ID."""
        old_map = {p.id: p for p in old_patterns}
        new_map = {p.id: p for p in new_patterns}

        added = [p.id for p in new_patterns if p.id not in old_map]
        removed = [p.id for p in old_patterns if p.id not in new_map]
        frequency_changes = []

        for pid in set(old_map.keys()) & set(new_map.keys()):
            old_freq = old_map[pid].frequency
            new_freq = new_map[pid].frequency
            if old_freq != new_freq:
                frequency_changes.append({
                    'id': pid,
                    'old_frequency': old_freq,
                    'new_frequency': new_freq,
                })

        return {
            'added': added,
            'removed': removed,
            'frequency_changes': frequency_changes,
        }

    @staticmethod
    def _diff_mistakes(
        old_mistakes: List[Mistake],
        new_mistakes: List[Mistake]
    ) -> Dict[str, Any]:
        """Diff mistakes by ID."""
        old_map = {m.id: m for m in old_mistakes}
        new_map = {m.id: m for m in new_mistakes}

        added = [m.id for m in new_mistakes if m.id not in old_map]
        removed = [m.id for m in old_mistakes if m.id not in new_map]
        resolved = []

        for mid in set(old_map.keys()) & set(new_map.keys()):
            old_m, new_m = old_map[mid], new_map[mid]
            if not old_m.resolution and new_m.resolution:
                resolved.append(mid)

        return {'added': added, 'removed': removed, 'resolved': resolved}

    @staticmethod
    def _diff_file_mappings(
        old_mappings: List[FileMapping],
        new_mappings: List[FileMapping]
    ) -> Dict[str, Any]:
        """Diff file mappings by path."""
        old_paths = {f.path for f in old_mappings}
        new_paths = {f.path for f in new_mappings}

        return {
            'added': sorted(new_paths - old_paths),
            'removed': sorted(old_paths - new_paths),
            'unchanged': sorted(old_paths & new_paths),
        }

    @staticmethod
    def _diff_dependencies(
        old_deps: List[Dependency],
        new_deps: List[Dependency]
    ) -> Dict[str, Any]:
        """Diff dependencies by name."""
        old_map = {d.name: d for d in old_deps}
        new_map = {d.name: d for d in new_deps}

        added = [d.name for d in new_deps if d.name not in old_map]
        removed = [d.name for d in old_deps if d.name not in new_map]
        version_changes = []

        for name in set(old_map.keys()) & set(new_map.keys()):
            old_ver = old_map[name].version
            new_ver = new_map[name].version
            if old_ver != new_ver:
                version_changes.append({
                    'name': name,
                    'old_version': old_ver,
                    'new_version': new_ver,
                })

        return {
            'added': added,
            'removed': removed,
            'version_changes': version_changes,
        }

    @staticmethod
    def _diff_risks(old_risks: List[Risk], new_risks: List[Risk]) -> Dict[str, Any]:
        """Diff risks by ID."""
        old_map = {r.id: r for r in old_risks}
        new_map = {r.id: r for r in new_risks}

        added = [r.id for r in new_risks if r.id not in old_map]
        removed = [r.id for r in old_risks if r.id not in new_map]
        status_changes = []

        for rid in set(old_map.keys()) & set(new_map.keys()):
            old_status = old_map[rid].status
            new_status = new_map[rid].status
            if old_status != new_status:
                status_changes.append({
                    'id': rid,
                    'old_status': old_status,
                    'new_status': new_status,
                })

        return {
            'added': added,
            'removed': removed,
            'status_changes': status_changes,
        }

    @staticmethod
    def _diff_lists(old_list: List[str], new_list: List[str]) -> Dict[str, Any]:
        """Diff simple string lists."""
        old_set = set(old_list)
        new_set = set(new_list)

        return {
            'added': sorted(new_set - old_set),
            'removed': sorted(old_set - new_set),
        }

    @staticmethod
    def _diff_dicts(old_dict: Dict, new_dict: Dict) -> Dict[str, Any]:
        """Diff dictionaries."""
        old_keys = set(old_dict.keys())
        new_keys = set(new_dict.keys())

        added = {k: new_dict[k] for k in new_keys - old_keys}
        removed = list(old_keys - new_keys)
        modified = {}

        for key in old_keys & new_keys:
            if old_dict[key] != new_dict[key]:
                modified[key] = {
                    'old': old_dict[key],
                    'new': new_dict[key],
                }

        return {
            'added': added,
            'removed': removed,
            'modified': modified,
        }

    @staticmethod
    def has_changes(diff_result: Dict[str, Any]) -> bool:
        """
        Check if the diff result contains any changes.

        Args:
            diff_result: Result from diff() method

        Returns:
            True if there are any changes, False otherwise
        """
        if diff_result.get('phase_changed'):
            return True

        for key in ['goals', 'decisions', 'patterns', 'mistakes',
                    'file_map', 'dependencies', 'risks', 'constraints']:
            section = diff_result.get(key, {})
            if section.get('added') or section.get('removed'):
                return True
            if section.get('modified') or section.get('resolved'):
                return True
            if section.get('frequency_changes') or section.get('version_changes'):
                return True
            if section.get('status_changes'):
                return True

        for key in ['progress', 'domain']:
            section = diff_result.get(key, {})
            if section.get('added') or section.get('removed') or section.get('modified'):
                return True

        return False

    @staticmethod
    def summarize_diff(diff_result: Dict[str, Any]) -> str:
        """
        Create a human-readable summary of the diff.

        Args:
            diff_result: Result from diff() method

        Returns:
            Summary string
        """
        lines = []

        if diff_result.get('phase_changed'):
            lines.append(
                f"Phase changed: {diff_result['old_phase']} -> {diff_result['new_phase']}"
            )

        categories = [
            ('goals', 'Goals'),
            ('decisions', 'Decisions'),
            ('patterns', 'Patterns'),
            ('mistakes', 'Mistakes'),
            ('file_map', 'File mappings'),
            ('dependencies', 'Dependencies'),
            ('risks', 'Risks'),
            ('constraints', 'Constraints'),
        ]

        for key, label in categories:
            section = diff_result.get(key, {})
            added = len(section.get('added', []))
            removed = len(section.get('removed', []))
            modified = len(section.get('modified', []))

            if added or removed or modified:
                parts = []
                if added:
                    parts.append(f"+{added}")
                if removed:
                    parts.append(f"-{removed}")
                if modified:
                    parts.append(f"~{modified}")
                lines.append(f"{label}: {', '.join(parts)}")

        if not lines:
            return "No changes"

        return "\n".join(lines)
