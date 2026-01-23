"""GSD PLAN.md 데이터 모델 정의"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TaskModel:
    """PLAN.md의 개별 Task 모델"""
    name: str
    type: str  # "auto" | "checkpoint:human-verify" | "checkpoint:decision"
    files: List[str] = field(default_factory=list)
    action: str = ""
    verify: Optional[str] = None
    done: str = ""


@dataclass
class PlanModel:
    """PLAN.md 전체 구조 모델"""
    phase: str
    plan: int
    type: str  # "execute" | "tdd"
    depends_on: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    objective: str = ""
    context: List[str] = field(default_factory=list)
    tasks: List[TaskModel] = field(default_factory=list)
    verification: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
