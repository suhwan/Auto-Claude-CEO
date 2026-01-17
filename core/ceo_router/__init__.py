"""CEO Router 패키지

CEO Router: 사용자 요청을 코딩/비코딩으로 분류하고 적절한 시스템으로 라우팅

## 사용법

### 기본 사용
```python
from core.ceo_router import CEOIntegration

integration = CEOIntegration()

# 코딩 작업 → Auto-Claude
result = integration.process_request("웹사이트 만들어줘")

# 비코딩 작업 → CEO Team
result = integration.process_request("블로그 글 써줘")
```

### 개별 컴포넌트 사용
```python
from core.ceo_router import CEORouter, TaskClassifier, TeamRegistry

# 1. 작업 분류만
classifier = TaskClassifier()
result = classifier.classify("API 개발해줘")  # TaskType.CODING

# 2. 라우팅만
router = CEORouter()
routing = router.route("마케팅 계획")  # target="marketing/leader"

# 3. 팀 레지스트리만
registry = TeamRegistry()
team = registry.get_team("marketing/leader")
```

## 확장 방법

### 새 팀 추가
```python
from core.ceo_router import Team, TeamRegistry

custom_teams = {
    "hr/leader": Team(
        name="hr/leader",
        description="인사팀 팀장",
        keywords=["인사", "채용", "HR"],
        capabilities=["채용 공고", "면접 진행"]
    )
}

registry = TeamRegistry(teams=custom_teams)
```

### 커스텀 분류기
```python
from core.ceo_router import TaskClassifier, CEORouter

classifier = TaskClassifier()
classifier.CODING_KEYWORDS.append("새키워드")

router = CEORouter(classifier=classifier)
```
"""

from .models import (
    TaskType,
    RoutingResult,
    AgentResult,
    ExecutionResult,
)
from .classifier import TaskClassifier
from .router import CEORouter
from .bridge import AutoClaudeBridge
from .executor import PlanExecutor
from .teams import Team, TeamRegistry
from .integration import CEOIntegration

__all__ = [
    "TaskType",
    "RoutingResult",
    "AgentResult",
    "ExecutionResult",
    "TaskClassifier",
    "CEORouter",
    "AutoClaudeBridge",
    "PlanExecutor",
    "Team",
    "TeamRegistry",
    "CEOIntegration",
]
