"""Implementation Plan JSON 스키마 정의"""

import json
from dataclasses import dataclass, field, asdict
from typing import List


@dataclass
class Subtask:
    """Implementation plan의 개별 서브태스크"""
    id: str
    title: str
    description: str
    files: List[str]
    status: str  # "pending" | "in_progress" | "completed" | "blocked"
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ImplementationPlan:
    """Implementation plan 전체 구조"""
    spec_id: str
    subtasks: List[Subtask]

    def to_dict(self) -> dict:
        """JSON 직렬화를 위한 dict 변환"""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
