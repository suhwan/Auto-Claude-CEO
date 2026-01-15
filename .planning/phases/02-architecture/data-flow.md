# Data Flow Design

## Overview

시스템 간 데이터 흐름과 상태 동기화 전략을 정의합니다.

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Complete Data Flow                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  사용자 요청                                                         │
│      │                                                               │
│      ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                   /ceo (CEO Router)                          │    │
│  │                                                              │    │
│  │  입력: 사용자 요청 텍스트                                    │    │
│  │  처리: 키워드 분석 → TaskType 분류                           │    │
│  │  출력: TaskType (coding | non_coding)                        │    │
│  └──────────────────────────┬───────────────────────────────────┘    │
│                             │                                        │
│              ┌──────────────┴──────────────┐                        │
│              ▼                             ▼                        │
│  ┌───────────────────────┐    ┌───────────────────────────────┐    │
│  │     코딩 작업          │    │        비코딩 작업            │    │
│  │                       │    │                               │    │
│  │  GSD Integration      │    │     CEO Teams Direct         │    │
│  │  ┌─────────────────┐  │    │  ┌─────────────────────┐     │    │
│  │  │ PLAN.md 읽기    │  │    │  │ 요청 → 팀 매칭      │     │    │
│  │  │      ↓          │  │    │  │      ↓              │     │    │
│  │  │ GSDConverter    │  │    │  │ Task tool 호출      │     │    │
│  │  │      ↓          │  │    │  │ (subagent_type)     │     │    │
│  │  │ implementation_ │  │    │  │      ↓              │     │    │
│  │  │ plan.json       │  │    │  │ 팀 리더 실행        │     │    │
│  │  └─────────────────┘  │    │  └─────────────────────┘     │    │
│  │          ↓            │    │            ↓                 │    │
│  │  ┌─────────────────┐  │    │  ┌─────────────────────┐     │    │
│  │  │ Auto-Claude     │  │    │  │ 문서/리포트/분석    │     │    │
│  │  │ Pipeline        │  │    │  │ 결과물              │     │    │
│  │  │ (12 Agents)     │  │    │  └─────────────────────┘     │    │
│  │  └─────────────────┘  │    │                               │    │
│  │          ↓            │    │                               │    │
│  │  ┌─────────────────┐  │    │                               │    │
│  │  │ 코드/테스트/    │  │    │                               │    │
│  │  │ 커밋            │  │    │                               │    │
│  │  └─────────────────┘  │    │                               │    │
│  └───────────┬───────────┘    └─────────────┬─────────────────┘    │
│              │                              │                       │
│              └──────────────┬───────────────┘                       │
│                             ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    결과 동기화                                │    │
│  │                                                              │    │
│  │  ┌─────────────────┐  ┌─────────────────┐                   │    │
│  │  │ STATE.md        │  │ SUMMARY.md      │                   │    │
│  │  │ 업데이트        │  │ 생성            │                   │    │
│  │  │ (진행 상황)     │  │ (작업 결과)     │                   │    │
│  │  └─────────────────┘  └─────────────────┘                   │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Transformations

### 1. PLAN.md → ImplementationPlan

```
입력 (PLAN.md):
---
phase: 02-architecture
plan: 01
type: execute
depends_on: []
files_modified: [integration-architecture.md]
---

<objective>
아키텍처 설계
</objective>

<tasks>
<task type="auto">
  <name>Task 1: 시스템 통합 레이어 설계</name>
  <files>integration-architecture.md</files>
  <action>문서 작성...</action>
  <verify>cat integration-architecture.md</verify>
  <done>문서 완성</done>
</task>
</tasks>

              ↓ GSDConverter.to_implementation_plan()

출력 (implementation_plan.json):
{
  "spec_id": "02-architecture-01",
  "subtasks": [
    {
      "id": "1",
      "title": "Task 1: 시스템 통합 레이어 설계",
      "description": "문서 작성...",
      "files": ["integration-architecture.md"],
      "status": "pending",
      "dependencies": []
    }
  ]
}
```

### 2. ImplementationPlan → Auto-Claude Execution

```
implementation_plan.json
        ↓
┌───────────────────────────────────────┐
│ Auto-Claude Pipeline                  │
│                                       │
│  1. PlannerAgent                      │
│     - 상세 실행 계획 수립              │
│     - 파일 의존성 분석                 │
│                                       │
│  2. CoderAgent                        │
│     - 코드 작성                        │
│     - 파일 생성/수정                   │
│                                       │
│  3. QAAgent                           │
│     - 테스트 실행                      │
│     - 린트/타입 체크                   │
│                                       │
│  4. CommitAgent                       │
│     - 변경사항 커밋                    │
│     - 커밋 메시지 생성                 │
└───────────────────────────────────────┘
        ↓
ExecutionResult
```

### 3. Execution Result → SUMMARY.md

```
ExecutionResult
{
  "plan_id": "02-architecture-01",
  "status": "success",
  "completed_subtasks": ["1"],
  "artifacts": ["integration-architecture.md"],
  "logs": ["Created file...", "Validated..."]
}
        ↓ sync_status()

SUMMARY.md:
---
phase: 02-architecture
plan: 01
subsystem: integration
provides: [integration-architecture]
---

# Summary

## Completed Tasks
- Task 1: 시스템 통합 레이어 설계 ✓

## Artifacts
- integration-architecture.md

## Logs
- Created file...
- Validated...
```

## State Management Strategy

### 1. State Stores

| 저장소 | 파일 | 용도 | 갱신 주기 |
|--------|------|------|----------|
| Project State | `.planning/STATE.md` | 전체 프로젝트 상태 | Phase/Plan 완료 시 |
| Execution State | `implementation_plan.json` | 현재 실행 중인 Plan | Subtask 완료 시 |
| UI State | Zustand Store | 프론트엔드 상태 | 실시간 |

### 2. State Schema

```typescript
// Project State (STATE.md parsed)
interface ProjectState {
  currentPhase: number;      // 현재 Phase (1-10)
  currentPlan: number;       // 현재 Plan (1-N)
  status: 'ready' | 'executing' | 'complete' | 'error';
  progress: number;          // 0-100%
  lastActivity: string;      // ISO 날짜
}

// Execution State (implementation_plan.json)
interface ExecutionState {
  specId: string;
  subtasks: Subtask[];
  currentSubtask: number;
  startTime: string;
  errors: string[];
}

// UI State (Zustand)
interface UIState {
  view: 'kanban' | 'roadmap' | 'terminal' | 'gsd';
  selectedTask: string | null;
  logs: LogEntry[];
  isExecuting: boolean;
}
```

### 3. Synchronization Strategy

```
단방향 흐름:
GSD ──────▶ CEO ──────▶ Auto-Claude ──────▶ GSD
    PLAN.md      Route        Execute       Update

상태 갱신 시점:
┌──────────────────┬────────────────────────────────┐
│ 이벤트           │ 갱신 대상                       │
├──────────────────┼────────────────────────────────┤
│ Plan 시작        │ STATE.md (status: executing)   │
│ Subtask 시작     │ implementation_plan.json       │
│ Subtask 완료     │ implementation_plan.json       │
│ Plan 완료        │ STATE.md, SUMMARY.md 생성      │
│ Phase 완료       │ ROADMAP.md, STATE.md           │
└──────────────────┴────────────────────────────────┘

충돌 해결:
- Last Write Wins (마지막 쓰기 우선)
- 동시 쓰기 방지 (락 없음, 순차 실행)
```

### 4. State Transitions

```
Plan Lifecycle:
                ┌─────────┐
                │ pending │
                └────┬────┘
                     │ start
                     ▼
                ┌─────────┐
          ┌─────│executing│─────┐
          │     └────┬────┘     │
          │          │          │
    error │    complete         │ error
          │          │          │
          ▼          ▼          ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │  error  │ │complete │ │ partial │
    └─────────┘ └─────────┘ └─────────┘

Subtask Lifecycle:
    pending → in_progress → completed
                   │
                   └──▶ failed
```

## Error Handling

### Error Types

| 에러 유형 | 원인 | 처리 방식 |
|----------|------|----------|
| ParseError | PLAN.md 형식 오류 | 상세 메시지 + 수정 가이드 |
| ValidationError | 필수 필드 누락 | 필드별 오류 목록 |
| ExecutionError | 코드 실행 실패 | 로그 기록 + 재시도 옵션 |
| SyncError | 파일 쓰기 실패 | 재시도 + 수동 개입 |

### Error Flow

```
에러 발생
    │
    ▼
┌─────────────────────────────────┐
│ 에러 분류                        │
│ - Recoverable: 재시도 가능       │
│ - Non-recoverable: 수동 개입     │
└─────────┬───────────────────────┘
          │
    ┌─────┴─────┐
    ▼           ▼
Recoverable   Non-recoverable
    │              │
    ▼              ▼
재시도 (3회)    ISSUES.md 기록
    │              │
    ▼              ▼
성공/실패      사용자 알림
```

### ISSUES.md Format

```markdown
# Deferred Issues

## [2025-01-15] Plan 02-01 Execution Error

**Phase**: 02-architecture
**Plan**: 01
**Subtask**: Task 1
**Error**: FileWriteError - Permission denied

**Context**:
- 파일: integration-architecture.md
- 시도 횟수: 3

**Resolution**:
- [ ] 파일 권한 확인
- [ ] 수동 생성 후 재실행
```

## Real-time Updates

### Event Flow

```
┌─────────────────────────────────────────────────────────┐
│ Backend → Frontend Event Flow                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Backend                      Frontend                   │
│  ┌────────────────┐          ┌────────────────┐         │
│  │ Auto-Claude    │          │ React App      │         │
│  │ Pipeline       │          │                │         │
│  └───────┬────────┘          └───────┬────────┘         │
│          │                           │                   │
│          │ subtask.start             │                   │
│          ├──────────────────────────▶│ update kanban     │
│          │                           │                   │
│          │ subtask.progress          │                   │
│          ├──────────────────────────▶│ update progress   │
│          │                           │                   │
│          │ subtask.complete          │                   │
│          ├──────────────────────────▶│ move card         │
│          │                           │                   │
│          │ plan.complete             │                   │
│          ├──────────────────────────▶│ show summary      │
│          │                           │                   │
└─────────────────────────────────────────────────────────┘
```

### Event Types

```typescript
type BackendEvent =
  | { type: 'subtask.start'; subtaskId: string }
  | { type: 'subtask.progress'; subtaskId: string; progress: number }
  | { type: 'subtask.complete'; subtaskId: string; result: any }
  | { type: 'subtask.error'; subtaskId: string; error: string }
  | { type: 'plan.complete'; planId: string; summary: string }
  | { type: 'log'; level: 'info' | 'warn' | 'error'; message: string };
```
