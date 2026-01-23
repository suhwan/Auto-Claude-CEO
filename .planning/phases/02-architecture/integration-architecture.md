# Integration Architecture

## Overview

GSD + CEO + Auto-Claude 세 시스템의 하이브리드 통합 아키텍처입니다.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Hybrid Integration Architecture                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐│
│  │     GSD      │     │     CEO      │     │     Auto-Claude      ││
│  │   (계획)     │────▶│   (분배)     │────▶│       (코딩)         ││
│  │              │     │              │     │                      ││
│  │ PLAN.md     │     │ Router       │     │ implementation_      ││
│  │ ROADMAP.md  │     │ Teams        │     │ plan.json            ││
│  │ STATE.md    │     │              │     │ CoderAgent           ││
│  └──────────────┘     └──────────────┘     └──────────────────────┘│
│         │                    │                       │             │
│         └────────────────────┴───────────────────────┘             │
│                              │                                      │
│                    ┌─────────┴─────────┐                           │
│                    │   Integration     │                           │
│                    │      Bridge       │                           │
│                    └───────────────────┘                           │
└─────────────────────────────────────────────────────────────────────┘
```

## System Roles

### GSD (Get Shit Done)
- **역할**: 프로젝트 계획 및 진행 추적
- **입력**: 사용자 요구사항
- **출력**: PLAN.md, ROADMAP.md, STATE.md
- **특징**: 구조화된 Markdown 기반 워크플로우

### CEO (AI Organization)
- **역할**: 작업 분류 및 팀 분배
- **입력**: 사용자 요청 또는 PLAN.md
- **출력**: 팀 실행 결과
- **특징**: 10개 전문 팀, 키워드 기반 라우팅

### Auto-Claude (Autonomous Coding)
- **역할**: 자율 코딩 실행
- **입력**: implementation_plan.json
- **출력**: 코드, 테스트, 커밋
- **특징**: 12 에이전트 파이프라인

## Integration Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Integration Flow                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  사용자 요청                                                         │
│      │                                                               │
│      ▼                                                               │
│  ┌─────────────────────────────────────────────┐                    │
│  │              /ceo (Entry Point)              │                    │
│  │                                              │                    │
│  │  1. 요청 분석                                │                    │
│  │  2. 작업 유형 분류 (코딩/비코딩)             │                    │
│  └──────────────────┬──────────────────────────┘                    │
│                     │                                                │
│         ┌───────────┴───────────┐                                   │
│         ▼                       ▼                                   │
│  ┌─────────────┐        ┌─────────────────────┐                     │
│  │ 코딩 작업   │        │    비코딩 작업      │                     │
│  │             │        │                     │                     │
│  │ Auto-Claude │        │    CEO Teams        │                     │
│  │ Pipeline    │        │    (10개 팀)        │                     │
│  └──────┬──────┘        └──────────┬──────────┘                     │
│         │                          │                                │
│         ▼                          ▼                                │
│  ┌─────────────┐        ┌─────────────────────┐                     │
│  │ Code/Test   │        │   Documents/        │                     │
│  │ Commit      │        │   Reports/Plans     │                     │
│  └──────┬──────┘        └──────────┬──────────┘                     │
│         │                          │                                │
│         └────────────┬─────────────┘                                │
│                      ▼                                              │
│           ┌─────────────────────┐                                   │
│           │   결과 동기화       │                                   │
│           │   STATE.md 업데이트 │                                   │
│           │   SUMMARY.md 생성   │                                   │
│           └─────────────────────┘                                   │
└─────────────────────────────────────────────────────────────────────┘
```

## Interface Definitions

### 1. GSD Converter Interface (Phase 3)

```python
class GSDConverter:
    """PLAN.md를 implementation_plan.json으로 변환"""

    def parse_plan(self, path: str) -> PlanModel:
        """
        PLAN.md 파일을 파싱하여 PlanModel 반환

        Args:
            path: PLAN.md 파일 경로

        Returns:
            PlanModel: 파싱된 계획 모델

        Raises:
            ParseError: 파싱 실패 시
        """
        pass

    def to_implementation_plan(self, plan: PlanModel) -> ImplementationPlan:
        """
        PlanModel을 Auto-Claude용 ImplementationPlan으로 변환

        Args:
            plan: GSD PlanModel

        Returns:
            ImplementationPlan: Auto-Claude 실행 가능한 계획
        """
        pass

    def validate(self, plan: PlanModel) -> ValidationResult:
        """계획 유효성 검증"""
        pass
```

### 2. CEO Router Interface (Phase 4)

```python
class TaskType(Enum):
    CODING = "coding"
    NON_CODING = "non_coding"
    MIXED = "mixed"

class CEORouter:
    """작업 유형 분류 및 라우팅"""

    def classify(self, request: str) -> TaskType:
        """
        요청을 코딩/비코딩으로 분류

        Args:
            request: 사용자 요청 텍스트

        Returns:
            TaskType: 작업 유형
        """
        pass

    def route(self, request: str, task_type: TaskType) -> AgentResult:
        """
        분류된 작업을 적절한 시스템으로 라우팅

        Args:
            request: 사용자 요청
            task_type: 분류된 작업 유형

        Returns:
            AgentResult: 실행 결과
        """
        pass

    def get_team(self, request: str) -> str:
        """비코딩 작업의 담당 팀 결정"""
        pass
```

### 3. Auto-Claude Bridge Interface (Phase 4)

```python
class AutoClaudeBridge:
    """Auto-Claude와의 연동 브릿지"""

    def execute_plan(self, plan: ImplementationPlan) -> ExecutionResult:
        """
        implementation_plan.json 실행

        Args:
            plan: 실행할 계획

        Returns:
            ExecutionResult: 실행 결과 (성공/실패, 산출물)
        """
        pass

    def sync_status(self, result: ExecutionResult) -> None:
        """
        실행 결과를 GSD 상태에 동기화

        Args:
            result: 실행 결과

        Side Effects:
            - STATE.md 업데이트
            - SUMMARY.md 생성
        """
        pass

    def get_progress(self) -> Progress:
        """현재 실행 진행 상황 조회"""
        pass
```

## Data Models

### PlanModel (GSD)

```python
@dataclass
class PlanModel:
    """GSD PLAN.md의 데이터 모델"""
    phase: str           # "01-foundation"
    plan: int            # 1, 2, 3
    type: str            # "execute" | "research"
    depends_on: List[str]
    files_modified: List[str]

    objective: str
    context: List[str]   # @ 참조 파일들
    tasks: List[TaskModel]
    verification: List[str]
    success_criteria: List[str]

@dataclass
class TaskModel:
    """PLAN.md 내 개별 태스크"""
    name: str
    type: str            # "auto" | "checkpoint:*"
    files: List[str]
    action: str
    verify: Optional[str]
    done: str
```

### ImplementationPlan (Auto-Claude)

```python
@dataclass
class ImplementationPlan:
    """Auto-Claude용 실행 계획"""
    spec_id: str         # "01-foundation-01"
    subtasks: List[Subtask]

@dataclass
class Subtask:
    """Auto-Claude 서브태스크"""
    id: str
    title: str
    description: str
    files: List[str]
    status: str          # "pending" | "in_progress" | "completed" | "blocked"
    dependencies: List[str]
```

### AgentResult

```python
@dataclass
class AgentResult:
    """에이전트 실행 결과"""
    success: bool
    agent_type: str      # "development/leader" | "auto-claude"
    output: Any
    errors: List[str]
    duration: float
```

### ExecutionResult

```python
@dataclass
class ExecutionResult:
    """Auto-Claude 실행 결과"""
    plan_id: str
    status: str          # "success" | "partial" | "failed"
    completed_subtasks: List[str]
    failed_subtasks: List[str]
    artifacts: List[str] # 생성된 파일들
    logs: List[str]
```

## Integration Points

### 1. Entry Point: /ceo 명령어 확장

현재 CEO는 키워드 기반으로 팀을 라우팅합니다. 통합 후:

```
/ceo 웹사이트 만들어줘
    │
    ├── 분석: "웹사이트", "만들어" → 코딩 작업
    │
    └── Auto-Claude 파이프라인 실행
        ├── spec.md 생성
        ├── PlannerAgent → implementation_plan.json
        ├── CoderAgent → 코드 생성
        └── QA → 검증 및 커밋
```

### 2. Router: 코딩/비코딩 분류기

```python
CODING_KEYWORDS = [
    "코드", "개발", "구현", "만들어", "작성", "수정",
    "API", "함수", "클래스", "버그", "디버그", "테스트",
    "빌드", "배포", "웹사이트", "앱", "서버"
]

NON_CODING_KEYWORDS = [
    "기획", "분석", "리포트", "문서", "계약", "법률",
    "마케팅", "블로그", "SEO", "영업", "제안서"
]

def is_coding_task(request: str) -> bool:
    coding_score = sum(1 for kw in CODING_KEYWORDS if kw in request)
    non_coding_score = sum(1 for kw in NON_CODING_KEYWORDS if kw in request)
    return coding_score > non_coding_score
```

### 3. Executor: Auto-Claude 에이전트 파이프라인

```
GSD PLAN.md
    │
    ▼ (GSDConverter)
implementation_plan.json
    │
    ▼ (AutoClaudeBridge)
Auto-Claude Pipeline
    │
    ├── PlannerAgent: 상세 계획 수립
    ├── CoderAgent: 코드 작성
    ├── QAAgent: 품질 검증
    └── CommitAgent: 커밋 생성
    │
    ▼
실행 결과
    │
    ▼ (sync_status)
STATE.md 업데이트, SUMMARY.md 생성
```

## Extensibility

### 새 팀 추가

1. `.claude/agents/{team}/leader.md` 생성
2. 라우팅 키워드 추가 (commands/ceo.md)
3. 팀 스킬 정의 (skills/{team}/SKILL.md)

### 새 워크플로우 추가

1. 워크플로우 정의 파일 생성
2. 라우터에 워크플로우 타입 추가
3. 실행기 구현

### 새 에이전트 타입 추가

1. BaseAgent 상속
2. 에이전트 설정 추가
3. 파이프라인에 연결

## Error Handling Strategy

### 레벨별 에러 처리

| 레벨 | 에러 유형 | 처리 방식 |
|------|----------|----------|
| GSD | 파싱 실패 | ValidationError + 상세 메시지 |
| Router | 분류 실패 | 기본값 (non_coding) + 경고 |
| Auto-Claude | 실행 실패 | 롤백 없음 + ISSUES.md 기록 |
| Bridge | 동기화 실패 | 재시도 + 수동 개입 요청 |

### 복구 전략

1. **부분 실패**: 성공한 부분 유지, 실패한 부분만 재시도
2. **전체 실패**: 에러 로그 기록, 수동 개입 대기
3. **타임아웃**: 진행 상황 저장, 재개 가능하도록 설계
