# Auto-Claude Frontend Architecture

## Overview

Electron 기반 데스크톱 앱으로 React + TypeScript로 구현되어 있습니다.

## Directory Structure

```
apps/frontend/src/
├── main/               # Electron 메인 프로세스
│   ├── main.ts
│   └── ipc/            # IPC 핸들러
├── renderer/           # React 렌더러
│   ├── App.tsx         # 메인 앱
│   ├── components/
│   │   ├── KanbanBoard.tsx      # 칸반 보드 (핵심)
│   │   ├── TaskCard.tsx         # 태스크 카드
│   │   ├── Roadmap.tsx          # 로드맵 뷰
│   │   ├── Terminal.tsx         # 터미널 뷰
│   │   ├── Sidebar.tsx          # 사이드바
│   │   └── ...
│   ├── features/
│   ├── hooks/
│   └── stores/
└── shared/
    ├── i18n/            # 다국어 지원
    │   └── locales/     # ko, en 등
    └── constants/
```

## Key Components

### 1. KanbanBoard.tsx
- 태스크 칸반 보드
- 드래그 앤 드롭 지원
- 상태별 레인: Backlog, To Do, In Progress, Done

### 2. TaskCard.tsx
- 개별 태스크 카드
- 상태, 진행률, 메타데이터 표시

### 3. Roadmap.tsx
- 로드맵 시각화
- Phase/Milestone 표시

### 4. Terminal.tsx
- 에이전트 실행 로그 표시
- 실시간 출력 스트리밍

## State Management

- React Context API
- Custom hooks (useProject, useTasks, etc.)
- Local storage for persistence

## Electron IPC Channels

```typescript
// Main → Renderer
'task:update'     // 태스크 상태 업데이트
'agent:output'    // 에이전트 출력
'project:loaded'  // 프로젝트 로드 완료

// Renderer → Main
'task:create'     // 태스크 생성
'agent:start'     // 에이전트 시작
'file:open'       // 파일 열기
```

## i18n Structure

```
shared/i18n/
├── index.ts          # i18n 설정
└── locales/
    ├── en.json       # 영어
    └── ko.json       # 한국어
```

## UI Extension Points

### 1. 탭 추가 위치
```tsx
// App.tsx 또는 Sidebar.tsx에서
<Tab label="GSD" component={<GSDTab />} />
```

### 2. 칸반 레인 확장
```tsx
// KanbanBoard.tsx에서 새 레인 추가 가능
const lanes = ['Backlog', 'To Do', 'In Progress', 'Review', 'Done'];
```

### 3. 대시보드 위젯
```tsx
// components/ 내 새 위젯 컴포넌트 추가
```

## Integration Points for GSD/CEO

### 1. GSD Tab (Phase 9)
- ROADMAP.md 파싱 및 표시
- Phase 진행률 시각화
- PLAN.md 실행 트리거

### 2. CEO Dashboard (Phase 10)
- 팀별 칸반 레인
- 리더 Context 대시보드
- 라우팅 상태 모니터링

### 3. 상태 동기화
- implementation_plan.json ↔ UI 상태
- GSD STATE.md ↔ 진행률 표시
