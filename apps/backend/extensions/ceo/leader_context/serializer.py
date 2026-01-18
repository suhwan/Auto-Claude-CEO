"""
Leader Context Serializer
=========================

Provides JSON serialization and deserialization for LeaderContext
and its component data models.
"""

import json
from datetime import datetime
from typing import Any, Dict

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


class LeaderContextSerializer:
    """
    Serializer for LeaderContext and related models.

    Provides static methods to convert LeaderContext objects to/from
    dictionaries and JSON strings. Handles datetime conversion using
    ISO 8601 format.
    """

    # ISO 8601 format for datetime serialization
    DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

    @staticmethod
    def _datetime_to_str(dt: datetime) -> str:
        """Convert datetime to ISO format string."""
        return dt.isoformat()

    @staticmethod
    def _str_to_datetime(dt_str: str) -> datetime:
        """Convert ISO format string to datetime."""
        return datetime.fromisoformat(dt_str)

    @staticmethod
    def _goal_to_dict(goal: Goal) -> Dict[str, Any]:
        """Convert Goal to dictionary."""
        return {
            'id': goal.id,
            'description': goal.description,
            'priority': goal.priority,
            'status': goal.status,
            'created_at': LeaderContextSerializer._datetime_to_str(goal.created_at),
            'completed_at': (
                LeaderContextSerializer._datetime_to_str(goal.completed_at)
                if goal.completed_at else None
            ),
        }

    @staticmethod
    def _dict_to_goal(data: Dict[str, Any]) -> Goal:
        """Convert dictionary to Goal."""
        return Goal(
            id=data['id'],
            description=data['description'],
            priority=data['priority'],
            status=data['status'],
            created_at=LeaderContextSerializer._str_to_datetime(data['created_at']),
            completed_at=(
                LeaderContextSerializer._str_to_datetime(data['completed_at'])
                if data.get('completed_at') else None
            ),
        )

    @staticmethod
    def _decision_to_dict(decision: Decision) -> Dict[str, Any]:
        """Convert Decision to dictionary."""
        return {
            'id': decision.id,
            'description': decision.description,
            'rationale': decision.rationale,
            'made_at': LeaderContextSerializer._datetime_to_str(decision.made_at),
            'related_goals': decision.related_goals,
        }

    @staticmethod
    def _dict_to_decision(data: Dict[str, Any]) -> Decision:
        """Convert dictionary to Decision."""
        return Decision(
            id=data['id'],
            description=data['description'],
            rationale=data['rationale'],
            made_at=LeaderContextSerializer._str_to_datetime(data['made_at']),
            related_goals=data.get('related_goals', []),
        )

    @staticmethod
    def _pattern_to_dict(pattern: Pattern) -> Dict[str, Any]:
        """Convert Pattern to dictionary."""
        return {
            'id': pattern.id,
            'name': pattern.name,
            'description': pattern.description,
            'frequency': pattern.frequency,
            'first_seen': LeaderContextSerializer._datetime_to_str(pattern.first_seen),
            'last_seen': LeaderContextSerializer._datetime_to_str(pattern.last_seen),
        }

    @staticmethod
    def _dict_to_pattern(data: Dict[str, Any]) -> Pattern:
        """Convert dictionary to Pattern."""
        return Pattern(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            frequency=data['frequency'],
            first_seen=LeaderContextSerializer._str_to_datetime(data['first_seen']),
            last_seen=LeaderContextSerializer._str_to_datetime(data['last_seen']),
        )

    @staticmethod
    def _mistake_to_dict(mistake: Mistake) -> Dict[str, Any]:
        """Convert Mistake to dictionary."""
        return {
            'id': mistake.id,
            'description': mistake.description,
            'impact': mistake.impact,
            'occurred_at': LeaderContextSerializer._datetime_to_str(mistake.occurred_at),
            'resolution': mistake.resolution,
            'resolved_at': (
                LeaderContextSerializer._datetime_to_str(mistake.resolved_at)
                if mistake.resolved_at else None
            ),
        }

    @staticmethod
    def _dict_to_mistake(data: Dict[str, Any]) -> Mistake:
        """Convert dictionary to Mistake."""
        return Mistake(
            id=data['id'],
            description=data['description'],
            impact=data['impact'],
            occurred_at=LeaderContextSerializer._str_to_datetime(data['occurred_at']),
            resolution=data.get('resolution'),
            resolved_at=(
                LeaderContextSerializer._str_to_datetime(data['resolved_at'])
                if data.get('resolved_at') else None
            ),
        )

    @staticmethod
    def _file_mapping_to_dict(file_mapping: FileMapping) -> Dict[str, Any]:
        """Convert FileMapping to dictionary."""
        return {
            'path': file_mapping.path,
            'purpose': file_mapping.purpose,
            'last_modified': LeaderContextSerializer._datetime_to_str(
                file_mapping.last_modified
            ),
            'related_goals': file_mapping.related_goals,
        }

    @staticmethod
    def _dict_to_file_mapping(data: Dict[str, Any]) -> FileMapping:
        """Convert dictionary to FileMapping."""
        return FileMapping(
            path=data['path'],
            purpose=data['purpose'],
            last_modified=LeaderContextSerializer._str_to_datetime(data['last_modified']),
            related_goals=data.get('related_goals', []),
        )

    @staticmethod
    def _dependency_to_dict(dependency: Dependency) -> Dict[str, Any]:
        """Convert Dependency to dictionary."""
        return {
            'name': dependency.name,
            'version': dependency.version,
            'purpose': dependency.purpose,
            'required': dependency.required,
        }

    @staticmethod
    def _dict_to_dependency(data: Dict[str, Any]) -> Dependency:
        """Convert dictionary to Dependency."""
        return Dependency(
            name=data['name'],
            version=data.get('version'),
            purpose=data['purpose'],
            required=data.get('required', True),
        )

    @staticmethod
    def _risk_to_dict(risk: Risk) -> Dict[str, Any]:
        """Convert Risk to dictionary."""
        return {
            'id': risk.id,
            'description': risk.description,
            'severity': risk.severity,
            'likelihood': risk.likelihood,
            'mitigation': risk.mitigation,
            'status': risk.status,
        }

    @staticmethod
    def _dict_to_risk(data: Dict[str, Any]) -> Risk:
        """Convert dictionary to Risk."""
        return Risk(
            id=data['id'],
            description=data['description'],
            severity=data['severity'],
            likelihood=data['likelihood'],
            mitigation=data.get('mitigation'),
            status=data.get('status', 'open'),
        )

    @staticmethod
    def to_dict(context: LeaderContext) -> Dict[str, Any]:
        """
        Convert LeaderContext to dictionary.

        Args:
            context: LeaderContext instance to convert

        Returns:
            Dictionary representation of the context
        """
        return {
            'project_id': context.project_id,
            'phase': context.phase,
            'goals': [
                LeaderContextSerializer._goal_to_dict(g) for g in context.goals
            ],
            'constraints': context.constraints,
            'decisions': [
                LeaderContextSerializer._decision_to_dict(d) for d in context.decisions
            ],
            'patterns': [
                LeaderContextSerializer._pattern_to_dict(p) for p in context.patterns
            ],
            'mistakes': [
                LeaderContextSerializer._mistake_to_dict(m) for m in context.mistakes
            ],
            'file_map': [
                LeaderContextSerializer._file_mapping_to_dict(f) for f in context.file_map
            ],
            'dependencies': [
                LeaderContextSerializer._dependency_to_dict(d) for d in context.dependencies
            ],
            'risks': [
                LeaderContextSerializer._risk_to_dict(r) for r in context.risks
            ],
            'progress': context.progress,
            'domain': context.domain,
            'created_at': LeaderContextSerializer._datetime_to_str(context.created_at),
            'updated_at': LeaderContextSerializer._datetime_to_str(context.updated_at),
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> LeaderContext:
        """
        Create LeaderContext from dictionary.

        Args:
            data: Dictionary containing context data

        Returns:
            LeaderContext instance
        """
        return LeaderContext(
            project_id=data['project_id'],
            phase=data['phase'],
            goals=[
                LeaderContextSerializer._dict_to_goal(g) for g in data.get('goals', [])
            ],
            constraints=data.get('constraints', []),
            decisions=[
                LeaderContextSerializer._dict_to_decision(d)
                for d in data.get('decisions', [])
            ],
            patterns=[
                LeaderContextSerializer._dict_to_pattern(p)
                for p in data.get('patterns', [])
            ],
            mistakes=[
                LeaderContextSerializer._dict_to_mistake(m)
                for m in data.get('mistakes', [])
            ],
            file_map=[
                LeaderContextSerializer._dict_to_file_mapping(f)
                for f in data.get('file_map', [])
            ],
            dependencies=[
                LeaderContextSerializer._dict_to_dependency(d)
                for d in data.get('dependencies', [])
            ],
            risks=[
                LeaderContextSerializer._dict_to_risk(r) for r in data.get('risks', [])
            ],
            progress=data.get('progress', {}),
            domain=data.get('domain', {}),
            created_at=LeaderContextSerializer._str_to_datetime(data['created_at']),
            updated_at=LeaderContextSerializer._str_to_datetime(data['updated_at']),
        )

    @staticmethod
    def to_json(context: LeaderContext, indent: int = 2) -> str:
        """
        Serialize LeaderContext to JSON string.

        Args:
            context: LeaderContext instance to serialize
            indent: JSON indentation level (default: 2)

        Returns:
            JSON string representation
        """
        return json.dumps(
            LeaderContextSerializer.to_dict(context),
            indent=indent,
            ensure_ascii=False,
        )

    @staticmethod
    def from_json(json_str: str) -> LeaderContext:
        """
        Deserialize LeaderContext from JSON string.

        Args:
            json_str: JSON string to parse

        Returns:
            LeaderContext instance
        """
        data = json.loads(json_str)
        return LeaderContextSerializer.from_dict(data)
