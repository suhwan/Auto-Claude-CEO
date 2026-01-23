"""
CEO Models - Data models for CEO integration
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class TaskType(Enum):
    """Task type classification"""
    CODING = "coding"
    NON_CODING = "non_coding"
    MIXED = "mixed"


@dataclass
class RoutingResult:
    """Result of task routing"""
    task_type: TaskType
    target: str
    confidence: float
    keywords_matched: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'task_type': self.task_type.value,
            'target': self.target,
            'confidence': self.confidence,
            'keywords_matched': self.keywords_matched
        }


@dataclass
class AgentDefinition:
    """Agent definition loaded from .claude/agents/"""
    name: str
    description: str
    tools: List[str]
    model: str
    skills: str
    permission_mode: str
    content: str
    team: str
    role: str  # 'leader' or specific role

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'description': self.description,
            'tools': self.tools,
            'model': self.model,
            'skills': self.skills,
            'permission_mode': self.permission_mode,
            'team': self.team,
            'role': self.role,
            'content': self.content
        }


@dataclass
class TeamInfo:
    """Team information"""
    name: str
    description: str
    leader: Optional[AgentDefinition] = None
    members: List[AgentDefinition] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'description': self.description,
            'leader': self.leader.to_dict() if self.leader else None,
            'members': [m.to_dict() for m in self.members]
        }
