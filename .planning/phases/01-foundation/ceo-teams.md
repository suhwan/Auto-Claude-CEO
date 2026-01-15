# CEO Teams Structure

## Overview

CEO는 AI 에이전트 기반 1인 기업 플랫폼입니다. 10개 팀, 19개 에이전트로 구성됩니다.

## Organization Chart

```
                      ┌─────────────────┐
                      │      CEO        │
                      │  (업무 라우터)   │
                      └────────┬────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────┴───────┐    ┌────────┴────────┐    ┌───────┴───────┐
│   Core Teams  │    │ Business Teams  │    │ Back-office   │
├───────────────┤    ├─────────────────┤    ├───────────────┤
│ - 기획팀      │    │ - 마케팅팀      │    │ - 재무팀      │
│ - 개발팀      │    │ - 영업팀        │    │ - 법무팀      │
│ - 디자인팀    │    │ - 고객지원팀    │    │               │
└───────────────┘    └─────────────────┘    └───────────────┘

        ┌──────────────────────┐
        │   Optional Teams     │
        ├──────────────────────┤
        │ - 데이터팀           │
        │ - 보안팀             │
        └──────────────────────┘
```

## Team Composition

### Core Teams

| 팀 | 폴더 | 팀장 | 팀원 |
|----|------|------|------|
| 기획팀 | planning/ | leader.md | analyst.md, researcher.md |
| 개발팀 | development/ | leader.md | architect.md, backend.md, frontend.md, qa.md |
| 디자인팀 | design/ | leader.md | - |

### Business Teams

| 팀 | 폴더 | 팀장 | 팀원 |
|----|------|------|------|
| 마케팅팀 | marketing/ | leader.md | content.md |
| 영업팀 | sales/ | leader.md | - |
| 고객지원팀 | support/ | leader.md | - |

### Back-office Teams

| 팀 | 폴더 | 팀장 | 팀원 |
|----|------|------|------|
| 재무팀 | finance/ | leader.md | - |
| 법무팀 | legal/ | leader.md | contract.md |

### Optional Teams

| 팀 | 폴더 | 팀장 | 팀원 |
|----|------|------|------|
| 데이터팀 | data/ | leader.md | analyst.md |
| 보안팀 | security/ | leader.md | - |

## Agent Definition Format

### YAML Frontmatter
```yaml
---
name: team/role
description: |
  역할 설명
allowed-tools: Task, Read, Glob, Grep, ...
---
```

### Agent Structure
```markdown
# [역할명]

당신은 [팀명]의 [역할]입니다.

## 역할
- 담당 업무 1
- 담당 업무 2

## 작업 지침
1. 지침 1
2. 지침 2

## 출력 형식
```
[출력 템플릿]
```
```

## Team → Member Invocation

팀장이 팀원을 호출하는 패턴:

```markdown
Task tool 사용:
- subagent_type: "development/backend"
- prompt: "API 엔드포인트 구현해줘"
```

## Agent File Summary

| 팀 | 파일 수 | 에이전트 목록 |
|----|---------|--------------|
| planning | 3 | leader, analyst, researcher |
| development | 5 | leader, architect, backend, frontend, qa |
| design | 1 | leader |
| marketing | 2 | leader, content |
| sales | 1 | leader |
| support | 1 | leader |
| finance | 1 | leader |
| legal | 2 | leader, contract |
| data | 2 | leader, analyst |
| security | 1 | leader |
| **합계** | **19** | |
