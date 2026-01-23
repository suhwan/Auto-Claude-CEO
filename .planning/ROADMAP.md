# Roadmap: Auto-Claude-CEO

## Overview

AI 에이전트 기반 1인 기업 통합 플랫폼 구축. Foundation부터 시작해 GSD-CEO-Auto-Claude 통합, 리더 에이전트 시스템, 팀 협업 시스템을 거쳐 UI 확장까지 10단계로 진행한다.

## Domain Expertise

None (커스텀 통합 프로젝트)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Foundation** - 기존 코드베이스 분석, 인프라 파악 ✓
- [x] **Phase 2: Architecture** - 시스템 아키텍처 설계, 기술 스택 확정 ✓
- [x] **Phase 3: GSD Converter** - PLAN.md → implementation_plan.json 변환기 ✓
- [x] **Phase 4: CEO Router** - CEO 라우터 통합 (코딩/비코딩 분배) ✓
- [x] **Phase 5: Leader Context** - Leader Context Model 구현 ✓
- [x] **Phase 6: Leader Checkpoints** - Subtask 체크포인트, 에러 로그, 리뷰 ✓
- [x] **Phase 7: Team Contracts** - Shared Contracts (API/UI/데이터 스펙) ✓
- [x] **Phase 8: Team Sync** - Sync Points, Shared Board, Leader Meeting ✓
- [x] **Phase 9: UI GSD Tab** - Auto-Claude UI에 GSD 탭 추가 ✓
- [x] **Phase 10: UI Dashboard** - 팀별 칸반 레인, 리더 대시보드, 수동 검증 UI ✓
- [x] **Phase 11: GSD Creation UI** - 프로젝트/로드맵/Plan 생성 UI, Claude Code 연동 ✓
- [ ] **Phase 12: GSD-Kanban Integration** - Ideas→GSD→Kanban 통합, 병렬 실행 지원

## Phase Details

### Phase 1: Foundation
**Goal**: Auto-Claude, GSD, CEO 코드베이스 분석 및 통합 포인트 파악
**Depends on**: Nothing (first phase)
**Research**: Unlikely (기존 코드 분석)
**Plans**: TBD

Plans:
- [x] 01-01: Auto-Claude 코드베이스 분석 ✓
- [x] 01-02: GSD 워크플로우 분석 ✓
- [x] 01-03: CEO Teams 구조 분석 ✓

### Phase 2: Architecture
**Goal**: 하이브리드 통합 아키텍처 설계, 기술 스택 확정
**Depends on**: Phase 1
**Research**: Likely (통합 아키텍처)
**Research topics**: 이벤트 기반 통합 패턴, 프로세스 간 통신, 상태 동기화
**Plans**: TBD

Plans:
- [x] 02-01: 통합 아키텍처 문서화 ✓
- [x] 02-02: 데이터 흐름 설계 ✓
- [x] 02-03: 배포 전략 수립 ✓

### Phase 3: GSD Converter
**Goal**: PLAN.md 마크다운을 implementation_plan.json으로 변환하는 모듈
**Depends on**: Phase 2
**Research**: Likely (파싱 및 스키마)
**Research topics**: Markdown AST 파싱, JSON 스키마 설계, 검증 로직
**Plans**: TBD

Plans:
- [x] 03-01: PLAN.md 파서 구현 ✓
- [x] 03-02: JSON 스키마 정의 및 변환 로직 ✓
- [x] 03-03: 검증 및 에러 핸들링 ✓

### Phase 4: CEO Router
**Goal**: 작업 유형별 라우팅 (코딩→Auto-Claude, 비코딩→CEO Teams)
**Depends on**: Phase 3
**Research**: Unlikely (기존 CEO 코드 활용)
**Plans**: TBD

Plans:
- [x] 04-01: 라우터 코어 구현 ✓
- [x] 04-02: Auto-Claude 연동 ✓
- [x] 04-03: CEO Teams 연동 ✓

### Phase 5: Leader Context
**Goal**: Leader Context Model 구현 (goals, constraints, decisions, patterns, mistakes)
**Depends on**: Phase 4
**Research**: Likely (Context Model 설계)
**Research topics**: 상태 모델 설계, 영속화 전략, 조회 인터페이스
**Plans**: TBD

Plans:
- [x] 05-01: Context Model 스키마 정의 ✓
- [x] 05-02: Context 저장/로드 구현 ✓
- [x] 05-03: Context 조회 API ✓

### Phase 6: Leader Checkpoints
**Goal**: Subtask 단위 체크포인트, 에러 로그, 비판적 리뷰
**Depends on**: Phase 5
**Research**: Likely (체크포인트 메커니즘)
**Research topics**: 트리거 조건, 상태 전환, 리뷰 자동화
**Plans**: TBD

Plans:
- [x] 06-01: 체크포인트 트리거 구현 ✓
- [x] 06-02: 에러 로그 시스템 ✓
- [x] 06-03: 리뷰 및 개선점 기록 ✓

### Phase 7: Team Contracts
**Goal**: Shared Contracts (API 스펙, UI 스펙, 데이터 모델)
**Depends on**: Phase 6
**Research**: Likely (Contract 설계)
**Research topics**: 스키마 버전 관리, 변경 감지, 충돌 해결
**Plans**: TBD

Plans:
- [x] 07-01: Contract 스키마 정의 ✓
- [x] 07-02: Contract 저장소 구현 ✓
- [x] 07-03: 변경 알림 시스템 ✓

### Phase 8: Team Sync
**Goal**: Sync Points, Shared Board, Leader Meeting 시스템
**Depends on**: Phase 7
**Research**: Likely (동기화 메커니즘)
**Research topics**: 이벤트 버스, 상태 동기화, 회의 자동화
**Plans**: TBD

Plans:
- [x] 08-01: Sync Points 구현 ✓
- [x] 08-02: Shared Board 구현 ✓
- [x] 08-03: Leader Meeting 자동화 ✓

### Phase 9: UI GSD Tab
**Goal**: Auto-Claude Electron UI에 GSD 탭 추가 (ROADMAP.md 표시)
**Depends on**: Phase 8
**Research**: Likely (Electron IPC)
**Research topics**: IPC 패턴, React 컴포넌트 통합, 상태 관리
**Plans**: 3

Plans:
- [x] 09-01: STATE.md 실시간 표시 ✓
- [x] 09-02: Plan 상세 보기 및 편집 ✓
- [x] 09-03: 진행 시각화 개선 ✓

### Phase 10: UI Dashboard
**Goal**: 팀별 칸반 레인, 리더 Context 대시보드, 수동 검증 UI
**Depends on**: Phase 9
**Research**: Unlikely (기존 UI 패턴 활용)
**Plans**: 3

Plans:
- [x] 10-01: 팀별 칸반 레인 추가 ✓
- [x] 10-02: 리더 Context 대시보드 ✓
- [x] 10-03: 수동 검증 UI (UAT Approve/Reject) ✓

### Phase 11: GSD Creation UI
**Goal**: UI에서 프로젝트/로드맵/Plan 생성, Claude Code CLI 연동으로 실행
**Depends on**: Phase 10
**Research**: Likely (Claude Code CLI 연동)
**Research topics**: CLI 프로세스 실행, IPC 스트리밍, 터미널 출력 캡처
**Plans**: TBD

Plans:
- [x] 11-01: New Project 마법사 UI ✓
- [x] 11-02: Create Roadmap UI (AI 생성) ✓
- [x] 11-03: Plan/Execute UI (Claude Code 연동) ✓

### Phase 12: GSD-Kanban Integration
**Goal**: Ideas→GSD→Kanban 워크플로우 통합, Phase별 Task 그룹화, 병렬 실행 지원
**Depends on**: Phase 11
**Research**: Likely (Kanban-GSD 연동)
**Research topics**: Ideas 데이터 구조, Kanban Task 메타데이터, 병렬 실행 상태 관리
**Plans**: 4

Plans:
- [ ] 12-01: Ideas → GSD 변환 (Convert to GSD Project)
- [ ] 12-02: GSD → Kanban 연동 (Phase별 Task 그룹화)
- [ ] 12-03: Kanban Task 실행 UI (Plan/Research/Execute 버튼)
- [ ] 12-04: 병렬 실행 및 의존성 관리

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → ... → 11 → 12

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 3/3 | Complete ✓ | 2025-01-15 |
| 2. Architecture | 3/3 | Complete ✓ | 2025-01-15 |
| 3. GSD Converter | 3/3 | Complete ✓ | 2025-01-15 |
| 4. CEO Router | 3/3 | Complete ✓ | 2025-01-18 |
| 5. Leader Context | 3/3 | Complete ✓ | 2025-01-18 |
| 6. Leader Checkpoints | 3/3 | Complete ✓ | 2025-01-18 |
| 7. Team Contracts | 3/3 | Complete ✓ | 2025-01-18 |
| 8. Team Sync | 3/3 | Complete ✓ | 2026-01-18 |
| 9. UI GSD Tab | 3/3 | Complete ✓ | 2026-01-18 |
| 10. UI Dashboard | 3/3 | Complete ✓ | 2026-01-19 |
| 11. GSD Creation UI | 3/3 | Complete ✓ | 2026-01-20 |
| 12. GSD-Kanban Integration | 0/4 | Not started | - |

## Milestone 2 Progress

**Total**: 11/12 Phases, 33/37 Plans
**Status**: Phase 12 ready
