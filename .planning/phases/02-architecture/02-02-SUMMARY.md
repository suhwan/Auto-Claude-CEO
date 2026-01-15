---
phase: 02-architecture
plan: 02
subsystem: data-flow
provides: [data-flow-design, state-management]
affects: [03-gsd-converter, 05-leader-context]
---

# Data Flow Design Summary

## Data Flow Overview

시스템 간 단방향 데이터 흐름을 설계했습니다.

```
사용자 요청 → /ceo Router → 분류 → Auto-Claude/CEO Teams → 결과 동기화
```

## Key Data Structures

### Input → Output Mapping

| 입력 | 변환 | 출력 |
|------|------|------|
| PLAN.md | GSDConverter | implementation_plan.json |
| implementation_plan.json | Auto-Claude | ExecutionResult |
| ExecutionResult | sync_status | SUMMARY.md, STATE.md |

### State Stores

| 저장소 | 파일 | 용도 |
|--------|------|------|
| Project State | STATE.md | 전체 진행 상황 |
| Execution State | implementation_plan.json | 현재 실행 상태 |
| UI State | Zustand Store | 프론트엔드 |

## State Synchronization Strategy

### Sync Points

1. **Plan 시작**: STATE.md → executing
2. **Subtask 완료**: implementation_plan.json 갱신
3. **Plan 완료**: SUMMARY.md 생성, STATE.md 갱신
4. **Phase 완료**: ROADMAP.md 업데이트

### Conflict Resolution

- **Last Write Wins**: 마지막 쓰기 우선
- **순차 실행**: 동시 쓰기 방지
- **롤백 없음**: 실패 시 로그만 기록

## Error Handling

| 에러 유형 | 처리 방식 |
|----------|----------|
| ParseError | 상세 메시지 + 가이드 |
| ExecutionError | 재시도 3회 + ISSUES.md |
| SyncError | 재시도 + 수동 개입 |

## Next Steps

### Phase 3: GSD Converter
- 변환 로직에서 이 데이터 흐름 사용
- 상태 갱신 훅 구현

### Phase 5: Leader Context
- Context 저장소로 STATE.md 패턴 활용
- 실시간 업데이트 이벤트 시스템 적용

## Files Created

- `data-flow.md`: 상세 데이터 흐름 문서
- `02-02-SUMMARY.md`: 본 요약 문서
