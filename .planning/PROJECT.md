# Auto-Claude-CEO

## What This Is

AI 에이전트 기반 1인 기업 통합 플랫폼. GSD로 계획하고, CEO가 팀에 분배하고, Auto-Claude가 병렬 실행한다. 사용자는 "관리자"로서 승인만 하면 시스템이 모든 것을 실행한다.

## Core Value

**사용자는 관리자만 한다.** 계획, 분배, 실행, 검증 모두 시스템이 처리. 사용자는 전략적 의사결정과 최종 승인만 담당.

## Requirements

### Validated

(None yet — ship to validate)

### Active

**Phase 0: 인프라 & 아키텍처 (최우선):**
- [ ] 사용자 인프라 파악 (AWS/GCP, DB, 메시지큐, CI/CD 등)
- [ ] 시스템 아키텍처 설계
- [ ] 기술 스택 확정
- [ ] 배포 전략 수립

**핵심 통합:**
- [ ] GSD PLAN.md → Auto-Claude implementation_plan.json 변환기
- [ ] CEO 라우터: 코딩 작업 → Auto-Claude, 비코딩 → CEO Teams

**리더 에이전트 시스템:**
- [ ] Leader Context Model (goals, constraints, decisions, patterns, mistakes, file_map, dependencies, risks, progress, domain)
- [ ] Subtask 단위 리더 체크포인트 (사전 컨텍스트 주입 → 실행 → 사후 검토)
- [ ] 에러 로그 및 패턴 추적
- [ ] 비판적 리뷰 및 개선점 기록

**팀 협업 시스템:**
- [ ] Shared Contracts (API 스펙, UI 스펙, 데이터 모델)
- [ ] Sync Points (Phase 내 통합 체크포인트)
- [ ] Shared Board (공지, 블로커, 질문, 변경사항)
- [ ] Leader Meeting 시스템 (계획, 중간점검, 회고)

**UI 확장:**
- [ ] Auto-Claude UI에 GSD 탭 추가 (ROADMAP.md 표시)
- [ ] 팀별 칸반 레인 추가
- [ ] 리더 Context 대시보드

### Out of Scope

- 실시간 리더 모니터링 — Claude 세션 한계로 불가능, Subtask 단위 체크포인트로 대체
- CEO development 팀 직접 실행 — Auto-Claude가 코딩 담당, CEO dev team은 제거
- Auto-Claude 코어 수정 — 업스트림 동기화 유지를 위해 UI 확장만
- 멀티 유저 — 1인 기업 플랫폼, 싱글 유저만

## Context

**기존 시스템:**
- Auto-Claude: Electron UI + Python 백엔드, 12 병렬 에이전트, Git worktree, QA 자동화
- GSD: Claude Code 워크플로우, PROJECT.md → ROADMAP.md → PLAN.md 계층
- CEO: Python 멀티팀 라우터, 10개 팀 (마케팅, 법무, 재무 등)

**통합 아키텍처:**
```
GSD (계획) → CEO (분배) → Auto-Claude (코딩) / CEO Teams (비코딩)
                ↓
        Leader Agents (감독 & 컨텍스트 관리)
```

**데이터 흐름:**
```
PLAN.md (Markdown) → 변환기 → implementation_plan.json (JSON) → Auto-Claude 실행
```

## Constraints

- **Tech Stack**: Auto-Claude 기반 (Electron + Python), CEO 로직 통합
- **업스트림 호환**: Auto-Claude 코어 수정 최소화, git upstream 동기화 유지
- **실행 환경**: Claude Max 구독 필요 (OAuth 토큰)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Auto-Claude 기반으로 통합 | UI, 병렬 실행, Git worktree 이미 구현됨 | — Pending |
| GSD → implementation_plan.json 변환 | Auto-Claude 코어 수정 없이 GSD 계획 사용 | — Pending |
| 리더는 감독자 역할 (승인자 아님) | 병목 방지, 1인 기업 효율성 | — Pending |
| Subtask 단위 리더 체크포인트 | 세밀한 컨텍스트 관리, 방향 이탈 방지 | — Pending |
| CEO development 팀 제거 | Auto-Claude 12 병렬 에이전트가 대체 | — Pending |
| Shared Contracts로 팀 간 조율 | 병렬 작업 시 충돌 방지 | — Pending |

---
*Last updated: 2025-01-13 after initialization*
