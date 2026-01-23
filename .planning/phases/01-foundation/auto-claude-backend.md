# Auto-Claude Backend Architecture

## Overview

Auto-Claude는 subtask 기반 구현 계획을 실행하는 자율 코딩 프레임워크입니다.

## Directory Structure

```
apps/backend/
├── run.py              # CLI 진입점
├── cli/                # 명령행 인터페이스
│   ├── main.py         # CLI 메인
│   ├── spec_commands.py
│   ├── qa_commands.py
│   └── workspace_commands.py
├── agents/             # 에이전트 구현
│   ├── base.py         # BaseAgent
│   ├── planner.py      # PlannerAgent
│   ├── coder.py        # CoderAgent
│   ├── session.py      # SessionAgent
│   └── tools_pkg/      # 에이전트 도구
│       └── tools/
│           ├── subtask.py
│           ├── progress.py
│           └── qa.py
├── analysis/           # 코드베이스 분석
│   ├── project_analyzer.py
│   ├── framework_analyzer.py
│   └── analyzers/
├── context/            # 컨텍스트 빌더
│   ├── builder.py
│   ├── search.py
│   └── models.py
├── core/               # 핵심 유틸리티
│   ├── workspace.py    # Git worktree 관리
│   ├── client.py       # Claude API 클라이언트
│   └── progress.py
├── qa/                 # QA 시스템
│   ├── qa_agent.py
│   └── qa_orchestrator.py
└── spec/               # Spec 관리
    ├── spec_manager.py
    └── spec_contract.json
```

## Core Modules

### 1. Agents (agents/)
- **BaseAgent**: 모든 에이전트의 기본 클래스
- **PlannerAgent**: implementation_plan.json 생성
- **CoderAgent**: 실제 코드 구현
- **SessionAgent**: 세션 상태 관리

### 2. CLI (cli/)
- spec: Spec 생성/관리
- qa: QA 실행
- workspace: 워크스페이스 관리 (--merge, --review, --discard)

### 3. Analysis (analysis/)
- 프로젝트 구조 분석
- 프레임워크 감지
- 보안 스캐닝

### 4. QA System (qa/)
- 자동화된 품질 검증
- QA 에이전트 오케스트레이션

## Data Flow

```
spec.md → PlannerAgent → implementation_plan.json → CoderAgent → QA → Commit
```

1. **Spec 입력**: spec/*.md 파일 로드
2. **계획 생성**: PlannerAgent가 implementation_plan.json 생성
3. **구현**: CoderAgent가 subtask별로 코드 작성
4. **검증**: QA 에이전트가 결과 검증
5. **완료**: Git commit 및 병합

## implementation_plan.json Schema

```json
{
  "spec_id": "string",
  "subtasks": [
    {
      "id": "string",
      "title": "string",
      "status": "pending|in_progress|completed"
    }
  ],
  "qa_signoff": {
    "status": "string",
    "timestamp": "ISO8601"
  }
}
```

## Extension Points

### 1. phase_config.py
Phase별 설정 커스터마이징

### 2. spec_contract.json
Spec 스키마 정의

### 3. agents/tools_pkg/
새 도구 추가 가능

## Dependencies

- Claude API (claude-sdk)
- Git (worktree 기능)
- Python 3.10+

## Integration Points for GSD/CEO

1. **PLAN.md → implementation_plan.json 변환**
   - GSD의 PLAN.md를 파싱하여 subtasks 배열 생성
   - task type에 따라 status 초기화

2. **CEO Router 연동**
   - 코딩 작업: Auto-Claude 에이전트 파이프라인 사용
   - 비코딩 작업: CEO Teams로 라우팅

3. **상태 동기화**
   - implementation_plan.json의 status를 GSD STATE.md와 동기화
