# PLAN.md Schema Reference

## Overview

PLAN.md는 Claude가 해석 없이 바로 실행할 수 있는 실행 가능한 프롬프트입니다.

## File Structure

```markdown
---
phase: XX-name
plan: NN
type: execute
depends_on: []
files_modified: []
---

<objective>...</objective>
<execution_context>...</execution_context>
<context>...</context>
<tasks>...</tasks>
<verification>...</verification>
<success_criteria>...</success_criteria>
<output>...</output>
```

## Frontmatter Fields

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| phase | string | Y | Phase 식별자 (예: "01-foundation") |
| plan | number | Y | Plan 번호 (예: 01, 02) |
| type | enum | Y | "execute", "research", "tdd" |
| depends_on | array | Y | 의존하는 Plan ID 목록 |
| files_modified | array | N | 수정할 파일 목록 |
| domain | string | N | 도메인 전문성 |

## XML Sections

### <objective>
```xml
<objective>
[1줄 목표]

Purpose: [이 Plan의 목적]
Output: [산출물 명시]
</objective>
```

### <execution_context>
```xml
<execution_context>
[실행 워크플로우 경로]
[참조할 템플릿 경로]
</execution_context>
```

### <context>
```xml
<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@src/path/to/file.ts
</context>
```
- @ 접두사로 파일 참조
- 실행에 필요한 컨텍스트 파일 나열

### <tasks>
```xml
<tasks>
<task type="auto">
  <name>Task N: [이름]</name>
  <files>[파일 경로]</files>
  <action>[구체적인 실행 지침]</action>
  <verify>[검증 명령]</verify>
  <done>[완료 기준]</done>
</task>
</tasks>
```

## Task Types

### type="auto"
자동 실행 태스크. Claude가 독립적으로 실행.

```xml
<task type="auto">
  <name>Task 1: Create login endpoint</name>
  <files>src/api/auth/login.ts</files>
  <action>POST endpoint accepting {email, password}...</action>
  <verify>curl -X POST /api/auth/login returns 200</verify>
  <done>Valid → 200 + cookie, Invalid → 401</done>
</task>
```

### type="checkpoint:human-verify"
사람이 결과물 확인 필요.

```xml
<task type="checkpoint:human-verify" gate="blocking">
  <what-built>[빌드한 것]</what-built>
  <how-to-verify>[검증 단계]</how-to-verify>
  <resume-signal>[재개 신호]</resume-signal>
</task>
```

### type="checkpoint:decision"
사람이 결정 필요.

```xml
<task type="checkpoint:decision" gate="blocking">
  <decision>[결정 사항]</decision>
  <context>[배경]</context>
  <options>
    <option id="a"><name>...</name><pros>...</pros><cons>...</cons></option>
  </options>
  <resume-signal>[선택 방법]</resume-signal>
</task>
```

## implementation_plan.json 매핑

| PLAN.md | implementation_plan.json |
|---------|-------------------------|
| `phase` + `plan` | `spec_id` |
| `<task>` | `subtasks[]` |
| `<name>` | `subtasks[].title` |
| `<files>` | (파싱 필요) |
| `type="auto"` | `status: "pending"` |
| `type="checkpoint:*"` | `status: "blocked"` |
| `<done>` | 완료 기준 (메타) |

## 변환 시 주의사항

1. **task id 생성**: 순차 번호 (1, 2, 3...)
2. **status 초기화**: 모두 "pending"으로 시작
3. **checkpoint 처리**: gate="blocking"이면 별도 처리 필요
4. **context 무시**: @ 참조는 실행 시에만 사용
5. **verify/done**: JSON에 포함하지 않음 (실행 시 사용)
