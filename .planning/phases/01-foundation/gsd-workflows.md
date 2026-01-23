# GSD (Get Shit Done) Workflows

## Overview

GSD는 Claude Code를 위한 구조화된 프로젝트 관리 시스템입니다.

## Directory Structure

```
.claude/get-shit-done/
├── workflows/           # 워크플로우 정의
│   ├── create-roadmap.md
│   ├── plan-phase.md
│   ├── execute-plan.md
│   ├── execute-phase.md
│   ├── verify-work.md
│   └── complete-milestone.md
├── templates/           # 문서 템플릿
│   ├── project.md
│   ├── roadmap.md
│   ├── state.md
│   ├── summary.md
│   └── phase-prompt.md
└── references/          # 참조 문서
    ├── plan-format.md
    ├── checkpoints.md
    └── principles.md
```

## Workflow Lifecycle

```
new-project → create-roadmap → plan-phase → execute-plan → verify-work → complete-milestone
```

### 1. new-project
- PROJECT.md 생성
- 프로젝트 비전, 목표, 제약조건 정의

### 2. create-roadmap
- ROADMAP.md 생성
- Phase 정의 및 의존성 설정
- STATE.md 초기화

### 3. plan-phase
- Phase별 PLAN.md 생성
- 태스크 분해 및 검증 기준 정의

### 4. execute-plan
- PLAN.md 실행
- 서브에이전트로 병렬 실행 가능
- SUMMARY.md 생성

### 5. execute-phase
- Phase 내 모든 PLAN 실행
- 의존성 분석 후 Wave별 병렬 실행

### 6. verify-work
- 결과물 검증
- UAT 이슈 트래킹

### 7. complete-milestone
- Milestone 완료 처리
- 아카이브 및 다음 Milestone 준비

## Slash Commands

| 명령어 | 설명 |
|--------|------|
| /gsd:new-project | 새 프로젝트 초기화 |
| /gsd:create-roadmap | 로드맵 생성 |
| /gsd:plan-phase N | Phase N 계획 수립 |
| /gsd:execute-plan | 현재 플랜 실행 |
| /gsd:execute-phase N | Phase N 전체 실행 |
| /gsd:progress | 진행 상황 확인 |
| /gsd:verify-work | 작업 검증 |

## State Transitions

```
PROJECT.md ─── 비전, 목표, 결정 사항
    ↓
ROADMAP.md ─── Phase 목록, 의존성
    ↓
STATE.md ───── 현재 위치, 진행률, 컨텍스트
    ↓
PLAN.md ────── 태스크 정의, 검증 기준
    ↓
SUMMARY.md ─── 결과물, 결정 사항, 이슈
```

## Parallelization

### Wave-based Execution
```python
# depends_on이 비어있는 Plan들은 Wave 1
# Wave 1 완료 후 depends_on이 충족된 Plan들은 Wave 2
# ...

Wave 1: [01-01, 01-02, 01-03]  # 의존성 없음, 병렬 실행
Wave 2: [01-04]                 # depends_on: [01-01, 01-02]
```

### Config Options
```json
{
  "parallelization": {
    "enabled": true,
    "max_concurrent_agents": 3
  }
}
```

## Context Management

- 메인 컨텍스트: 오케스트레이션 (~5%)
- 서브에이전트: Plan별 Fresh 200k context
- 컨텍스트 목표: 50% 미만 유지
