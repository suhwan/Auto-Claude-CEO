---
phase: 02-architecture
plan: 01
subsystem: integration
provides: [integration-architecture, component-interfaces]
affects: [03-gsd-converter, 04-ceo-router]
---

# Integration Architecture Summary

## Architecture Overview

GSD + CEO + Auto-Claude 세 시스템의 **하이브리드 통합 아키텍처**를 설계했습니다.

```
GSD (계획) → CEO (분배) → Auto-Claude (코딩)
     ↓            ↓              ↓
  PLAN.md    Router/Teams   implementation_plan.json
```

## Key Design Decisions

### 1. Layer Structure

| Layer | 역할 | 컴포넌트 |
|-------|------|----------|
| Entry | 진입점 | /ceo 명령어 |
| Router | 분류 | CEORouter (코딩/비코딩) |
| Converter | 변환 | GSDConverter (PLAN → JSON) |
| Executor | 실행 | Auto-Claude / CEO Teams |
| Sync | 동기화 | AutoClaudeBridge |

### 2. Interface Pattern

- **GSDConverter**: PLAN.md 파싱, JSON 변환
- **CEORouter**: 작업 분류, 팀 라우팅
- **AutoClaudeBridge**: 실행, 상태 동기화

### 3. Extension Strategy

- **새 팀**: `.claude/agents/{team}/leader.md`
- **새 워크플로우**: 라우터 타입 + 실행기
- **새 에이전트**: BaseAgent 상속

## Data Models

### Core Types

```python
PlanModel          # GSD PLAN.md
ImplementationPlan # Auto-Claude JSON
TaskType           # coding | non_coding
AgentResult        # 실행 결과
ExecutionResult    # Auto-Claude 결과
```

### Field Mapping

| GSD (PLAN.md) | Auto-Claude (JSON) |
|---------------|-------------------|
| phase + plan | spec_id |
| `<task>` | subtasks[] |
| `<name>` | title |
| `<action>` | description |

## Integration Points

1. **진입점**: /ceo 명령어 확장
2. **라우터**: is_coding_task() 분류기
3. **변환**: GSDConverter.to_implementation_plan()
4. **실행**: Auto-Claude 12 에이전트 파이프라인
5. **동기화**: STATE.md, SUMMARY.md 자동 업데이트

## Next Steps

### Phase 3: GSD Converter
- parse_plan() 구현
- to_implementation_plan() 구현
- 검증 로직 추가

### Phase 4: CEO Router
- classify() 구현
- route() 구현
- Auto-Claude/Teams 연동

## Files Created

- `integration-architecture.md`: 상세 아키텍처 문서
- `02-01-SUMMARY.md`: 본 요약 문서
