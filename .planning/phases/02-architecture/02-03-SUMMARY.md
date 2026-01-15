---
phase: 02-architecture
plan: 03
subsystem: deployment
provides: [deployment-strategy, dev-workflow]
affects: [03-gsd-converter, 09-ui-gsd-tab]
---

# Deployment Strategy Summary

## Execution Environment Overview

로컬 환경에서 세 시스템이 통합 실행됩니다.

```
┌─────────────────────────────────────┐
│ 사용자 환경 (로컬)                   │
├─────────────────────────────────────┤
│ Claude Code CLI                     │
│ ├── .claude/agents/ (CEO Teams)     │
│ ├── .claude/commands/ (GSD)         │
│ └── .claude/skills/ (통합 스킬)      │
├─────────────────────────────────────┤
│ Auto-Claude Electron App            │
│ ├── Frontend (React)                │
│ └── Backend (Python subprocess)     │
├─────────────────────────────────────┤
│ Integration Bridge (Python)         │
│ ├── GSDConverter                    │
│ ├── CEORouter                       │
│ └── AutoClaudeBridge                │
└─────────────────────────────────────┘
```

## Component Placement Summary

| 시스템 | 위치 | 형식 |
|--------|------|------|
| GSD | `.claude/get-shit-done/` | Markdown |
| CEO | `.claude/agents/` | Markdown |
| Auto-Claude | `apps/` | Python/TypeScript |
| Bridge | `core/` | Python |

## Development Workflow Summary

### Development Mode
- Claude Code: 파일 저장 시 자동 반영
- Auto-Claude Frontend: Vite HMR
- Backend: 수동 재시작

### Test Strategy
- Unit: `pytest tests/unit/`, `npm test`
- Integration: `pytest tests/integration/`
- E2E: `npm run test:e2e`

### Version Control
- Git Flow: main ← develop ← feature/*
- Commits: Conventional Commits
- Tags: v1.0.0-alpha/beta/rc/release

## Dependency Management

| 환경 | 파일 | 주요 패키지 |
|------|------|------------|
| Python | requirements.txt | pyyaml, pydantic, click |
| Node.js | package.json | react, zustand, electron |
| Claude | settings.json | agents, commands, skills |

## Phase 3+ Preparation

### Phase 3: GSD Converter
- `core/gsd_converter.py` 위치에 구현
- pyyaml, markdown 의존성 사용

### Phase 9: UI GSD Tab
- `apps/frontend/src/renderer/components/` 에 컴포넌트 추가
- Zustand store로 상태 관리

## Files Created

- `deployment-strategy.md`: 상세 배포 전략 문서
- `02-03-SUMMARY.md`: 본 요약 문서

## Phase 2 Architecture Complete

Phase 2에서 생성된 모든 산출물:

| Plan | 산출물 | 용도 |
|------|--------|------|
| 02-01 | integration-architecture.md | 통합 아키텍처 설계 |
| 02-02 | data-flow.md | 데이터 흐름 및 상태 관리 |
| 02-03 | deployment-strategy.md | 배포 및 실행 환경 |
