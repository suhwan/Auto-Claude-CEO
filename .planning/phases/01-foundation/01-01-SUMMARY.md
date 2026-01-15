---
phase: 01-foundation
plan: 01
subsystem: auto-claude-architecture
provides: [auto-claude-architecture, integration-points]
affects: [02-architecture, 03-gsd-converter, 09-ui-gsd-tab, 10-ui-dashboard]
---

# Auto-Claude 아키텍처 분석 요약

## 전체 아키텍처

Auto-Claude는 **subtask 기반 자율 코딩 프레임워크**로, 다음 구조를 가집니다:

```
spec.md → PlannerAgent → implementation_plan.json → CoderAgent → QA → Commit
```

### Backend (Python)
- **에이전트 시스템**: planner, coder, session 에이전트
- **도구 패키지**: subtask, progress, qa 도구
- **분석 모듈**: 프로젝트/프레임워크 분석기
- **QA 시스템**: 자동화된 품질 검증

### Frontend (Electron + React)
- **칸반 보드**: 태스크 시각화 및 관리
- **로드맵 뷰**: 프로젝트 진행 상황
- **터미널**: 에이전트 실행 로그
- **i18n**: 다국어 지원 (ko, en)

## GSD 통합 포인트

### 1. PLAN.md → implementation_plan.json 변환 (Phase 3)

| PLAN.md | implementation_plan.json |
|---------|-------------------------|
| `plan:` | `spec_id:` |
| `<task>` | `subtasks[]` |
| `<name>` | `subtasks[].title` |
| `type="auto"` | `status: "pending"` |

### 2. phase_config.py 확장
- GSD Phase 설정 추가
- 커스텀 에이전트 설정

### 3. UI 탭 추가 (Phase 9)
- App.tsx에 GSD 탭 컴포넌트 추가
- ROADMAP.md 파싱 및 시각화

## CEO 통합 포인트

### 1. 라우터 통합 (Phase 4)
```python
if is_coding_task(request):
    route_to_auto_claude(request)  # 12 에이전트 파이프라인
else:
    route_to_ceo_teams(request)    # 10개 팀
```

### 2. agents/ 구조 활용
- Auto-Claude의 에이전트 패턴을 CEO Teams에 적용
- BaseAgent 클래스 재사용 가능

### 3. 상태 동기화
- implementation_plan.json ↔ STATE.md
- 칸반 보드 ↔ 팀별 태스크

## 제약사항 (Upstream 동기화)

최소 수정 영역:
- `apps/backend/agents/`: 핵심 에이전트 로직
- `apps/backend/cli/`: CLI 인터페이스

확장 권장 영역:
- `apps/backend/core/`: 유틸리티 확장
- `apps/frontend/src/renderer/components/`: UI 컴포넌트 추가

## 다음 단계

1. **Phase 2**: 하이브리드 통합 아키텍처 설계
2. **Phase 3**: PLAN.md → JSON 변환기 구현
3. **Phase 9**: UI GSD 탭 추가
