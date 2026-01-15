# Deployment Strategy

## Overview

통합 시스템의 배포 방식과 실행 환경을 정의합니다.

## Execution Environment

```
┌─────────────────────────────────────────────────────────────────────┐
│                     User Environment (Local)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ Claude Code CLI                                              │    │
│  │                                                              │    │
│  │  ┌─────────────────────────────────────────────────────┐    │    │
│  │  │ .claude/                                             │    │    │
│  │  │ ├── agents/          ← CEO Teams (10개 팀)          │    │    │
│  │  │ │   ├── planning/                                    │    │    │
│  │  │ │   ├── development/                                 │    │    │
│  │  │ │   ├── marketing/                                   │    │    │
│  │  │ │   └── ...                                          │    │    │
│  │  │ │                                                    │    │    │
│  │  │ ├── commands/        ← CLI Commands                  │    │    │
│  │  │ │   ├── ceo.md                                       │    │    │
│  │  │ │   ├── dev.md                                       │    │    │
│  │  │ │   └── ...                                          │    │    │
│  │  │ │                                                    │    │    │
│  │  │ ├── skills/          ← Team Skills                   │    │    │
│  │  │ │   ├── development/SKILL.md                         │    │    │
│  │  │ │   └── ...                                          │    │    │
│  │  │ │                                                    │    │    │
│  │  │ └── get-shit-done/   ← GSD Workflows                 │    │    │
│  │  │     ├── workflows/                                   │    │    │
│  │  │     └── templates/                                   │    │    │
│  │  └─────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ Auto-Claude Electron App                                     │    │
│  │                                                              │    │
│  │  ┌────────────────────┐  ┌────────────────────────────┐     │    │
│  │  │ Frontend           │  │ Backend                     │     │    │
│  │  │ (Electron + React) │  │ (Python subprocess)         │     │    │
│  │  │                    │  │                             │     │    │
│  │  │ - Kanban Board     │  │ - PlannerAgent              │     │    │
│  │  │ - Roadmap View     │  │ - CoderAgent                │     │    │
│  │  │ - Terminal         │  │ - QAAgent                   │     │    │
│  │  │ - GSD Tab (Phase 9)│  │ - Tools                     │     │    │
│  │  └────────────────────┘  └────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ Integration Bridge (Python)                                  │    │
│  │                                                              │    │
│  │  - GSDConverter: PLAN.md → implementation_plan.json          │    │
│  │  - CEORouter: 코딩/비코딩 분류 및 라우팅                      │    │
│  │  - AutoClaudeBridge: 실행 및 상태 동기화                      │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Placement

### GSD + CEO (Claude Code Native)

| 컴포넌트 | 위치 | 형식 |
|----------|------|------|
| GSD Workflows | `.claude/get-shit-done/` | Markdown |
| CEO Teams | `.claude/agents/` | Markdown |
| Commands | `.claude/commands/` | Markdown |
| Skills | `.claude/skills/` | Markdown |

### Auto-Claude (Separate App)

| 컴포넌트 | 위치 | 형식 |
|----------|------|------|
| Frontend | `apps/frontend/` | TypeScript/React |
| Backend | `apps/backend/` | Python |
| Agents | `apps/backend/agents/` | Python |
| Tools | `apps/backend/tools/` | Python |

### Integration Bridge (Python Module)

| 모듈 | 위치 | 역할 |
|------|------|------|
| gsd_converter | `core/gsd_converter.py` | PLAN → JSON |
| ceo_router | `core/ceo_router.py` | 분류 및 라우팅 |
| auto_claude_bridge | `core/auto_claude_bridge.py` | 실행 연동 |

## Dependency Management

### Python Dependencies

```
# requirements.txt
pyyaml>=6.0          # YAML/Frontmatter 파싱
markdown>=3.4        # Markdown 파싱
pydantic>=2.0        # 데이터 검증
click>=8.0           # CLI 인터페이스
rich>=13.0           # 터미널 출력
```

### Node.js Dependencies

```json
// package.json (apps/frontend)
{
  "dependencies": {
    "react": "^18.2.0",
    "zustand": "^4.4.0",
    "electron": "^27.0.0",
    "@tanstack/react-query": "^5.0.0"
  }
}
```

### Claude Code Configuration

```json
// .claude/settings.json
{
  "agents": {
    "enabled": true,
    "path": ".claude/agents"
  },
  "commands": {
    "enabled": true,
    "path": ".claude/commands"
  },
  "skills": {
    "enabled": true,
    "path": ".claude/skills"
  }
}
```

## Development Workflow

### 1. Development Mode

#### Hot Reload

| 컴포넌트 | Hot Reload | 방법 |
|----------|-----------|------|
| Claude Code MD | No | 파일 저장 시 자동 반영 |
| Auto-Claude Frontend | Yes | Vite HMR |
| Auto-Claude Backend | No | 수동 재시작 |
| Integration Bridge | No | 수동 재시작 |

#### Debugging

```bash
# Claude Code 디버깅
claude --debug  # 상세 로그 출력

# Auto-Claude Backend 디버깅
python -m debugpy --listen 5678 main.py

# Auto-Claude Frontend 디버깅
# Chrome DevTools (Electron)
```

#### Log Locations

| 컴포넌트 | 로그 위치 |
|----------|----------|
| Claude Code | Terminal stdout |
| Auto-Claude Backend | `logs/backend.log` |
| Auto-Claude Frontend | Console (DevTools) |
| Integration | `logs/integration.log` |

### 2. Test Strategy

#### Unit Tests

```bash
# Python (Backend + Integration)
pytest tests/unit/

# TypeScript (Frontend)
npm test
```

#### Integration Tests

```bash
# 전체 흐름 테스트
pytest tests/integration/

# E2E 테스트
npm run test:e2e
```

#### Test Structure

```
tests/
├── unit/
│   ├── test_gsd_converter.py
│   ├── test_ceo_router.py
│   └── test_auto_claude_bridge.py
├── integration/
│   ├── test_gsd_to_autoclaude.py
│   └── test_full_workflow.py
└── e2e/
    └── test_user_scenarios.py
```

### 3. Version Control

#### Git Branching

```
main ─────────────────────────────────────────────▶
  │
  └─── develop ───────────────────────────────────▶
         │
         ├─── feature/phase-3-gsd-converter ──▶
         │
         └─── feature/phase-4-ceo-router ─────▶
```

#### Commit Convention

```
<type>(<scope>): <description>

Types:
- feat: 새 기능
- fix: 버그 수정
- docs: 문서
- refactor: 리팩토링
- test: 테스트
- chore: 기타

Examples:
- feat(gsd-converter): add PLAN.md parser
- fix(ceo-router): handle empty keywords
- docs(architecture): update integration diagram
```

#### Release Tagging

```
v1.0.0-alpha   # Phase 1-3 완료
v1.0.0-beta    # Phase 1-6 완료
v1.0.0-rc1     # Phase 1-9 완료
v1.0.0         # Phase 10 완료
```

### 4. CI/CD (Future)

```yaml
# .github/workflows/ci.yml (향후)
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install & Build
        run: |
          cd apps/frontend
          npm ci
          npm run build
```

## Installation Guide

### Prerequisites

```bash
# Required
- Python 3.11+
- Node.js 20+
- Claude Code CLI

# Optional
- Git
- VS Code (권장 IDE)
```

### Quick Start

```bash
# 1. Clone
git clone https://github.com/xxx/auto-claude-ceo.git
cd auto-claude-ceo

# 2. Python 환경
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Node.js 환경
cd apps/frontend
npm install

# 4. 실행
npm run dev        # Electron 앱 실행
# 또는
claude /ceo        # CLI로 CEO 호출
```

## Directory Structure (Final)

```
auto-claude-ceo/
├── .claude/
│   ├── agents/              # CEO Teams
│   ├── commands/            # CLI Commands
│   ├── skills/              # Team Skills
│   └── get-shit-done/       # GSD Workflows
│
├── .planning/
│   ├── PROJECT.md           # 프로젝트 정의
│   ├── ROADMAP.md           # 로드맵
│   ├── STATE.md             # 현재 상태
│   └── phases/              # Phase별 산출물
│
├── apps/
│   ├── frontend/            # Electron + React
│   └── backend/             # Python Backend
│
├── core/
│   ├── gsd_converter.py     # GSD → JSON
│   ├── ceo_router.py        # 분류 및 라우팅
│   └── auto_claude_bridge.py # 실행 연동
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── requirements.txt
├── package.json
└── README.md
```
