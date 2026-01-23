"""CEO Router 데이터 모델 정의"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Any


class TaskType(Enum):
    """작업 유형 분류"""
    CODING = "coding"
    NON_CODING = "non_coding"
    MIXED = "mixed"


@dataclass
class RoutingResult:
    """라우팅 결과"""
    task_type: TaskType
    target: str  # "auto-claude" 또는 "planning/leader" 등 팀 이름
    confidence: float = 0.0  # 0.0 ~ 1.0
    keywords_matched: List[str] = field(default_factory=list)

    def __post_init__(self):
        """데이터 유효성 검증"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence는 0.0~1.0 사이여야 합니다: {self.confidence}")


@dataclass
class AgentResult:
    """에이전트 실행 결과"""
    success: bool
    agent_type: str  # "development/leader" | "auto-claude" 등
    output: Any = None
    errors: List[str] = field(default_factory=list)
    duration: float = 0.0  # 실행 시간 (초)

    def __post_init__(self):
        """데이터 유효성 검증"""
        if self.duration < 0:
            raise ValueError(f"duration은 0 이상이어야 합니다: {self.duration}")


@dataclass
class ExecutionResult:
    """Auto-Claude 실행 결과"""
    plan_id: str
    status: str  # "success" | "partial" | "failed"
    completed_subtasks: List[str] = field(default_factory=list)
    failed_subtasks: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)  # 생성된 파일 경로들
    logs: List[str] = field(default_factory=list)

    def __post_init__(self):
        """데이터 유효성 검증"""
        valid_statuses = ["success", "partial", "failed"]
        if self.status not in valid_statuses:
            raise ValueError(f"status는 {valid_statuses} 중 하나여야 합니다: {self.status}")
