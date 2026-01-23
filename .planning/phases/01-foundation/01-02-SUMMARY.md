---
phase: 01-foundation
plan: 02
subsystem: gsd-schema
provides: [gsd-schema-analysis, conversion-requirements]
affects: [03-gsd-converter]
---

# GSD 워크플로우 분석 요약

## GSD 시스템 개요

GSD (Get Shit Done)는 Claude Code를 위한 **구조화된 프로젝트 관리 시스템**입니다.

### 문서 계층
```
PROJECT.md → ROADMAP.md → PLAN.md → SUMMARY.md
     ↑            ↑           ↑          ↑
   비전        Phase      태스크      결과물
```

### 핵심 워크플로우
1. **new-project**: 프로젝트 초기화
2. **create-roadmap**: Phase 정의
3. **plan-phase**: 태스크 분해
4. **execute-plan**: 실행 및 SUMMARY 생성
5. **execute-phase**: 병렬 실행

## PLAN.md 스키마

### Frontmatter
```yaml
---
phase: 01-foundation
plan: 01
type: execute
depends_on: []
files_modified: [output.md]
---
```

### XML 구조
| 섹션 | 설명 |
|------|------|
| `<objective>` | 목표와 목적 |
| `<context>` | @ 파일 참조 |
| `<tasks>` | 태스크 목록 |
| `<verification>` | 전체 검증 |
| `<success_criteria>` | 성공 기준 |

### Task Types
| Type | 실행 방식 |
|------|----------|
| `auto` | 자동 실행 |
| `checkpoint:human-verify` | 사람 검증 필요 |
| `checkpoint:decision` | 사람 결정 필요 |

## 변환 요구사항 (Phase 3)

### PLAN.md → implementation_plan.json

```
입력:                          출력:
---                           {
phase: 01-foundation    →       "spec_id": "01-foundation-01",
plan: 01                        "subtasks": [
---                               {
<task type="auto">      →           "id": "1",
  <name>Task 1...</name>→           "title": "Task 1...",
                                    "status": "pending"
                                  }
                                ]
                              }
```

### 필드 매핑 테이블

| PLAN.md | JSON | 변환 규칙 |
|---------|------|----------|
| `phase` | `spec_id` (prefix) | `{phase}-{plan}` |
| `plan` | `spec_id` (suffix) | |
| `<task>` | `subtasks[]` | 배열로 변환 |
| `<name>` | `title` | 텍스트 추출 |
| `type="auto"` | `status: "pending"` | 기본값 |
| `type="checkpoint:*"` | `status: "blocked"` | 특별 처리 |

### 변환 불가능한 정보

다음은 JSON에 포함하지 않고 실행 시 별도 처리:
- `<context>`: 파일 참조 (@...)
- `<action>`: 실행 지침
- `<verify>`: 검증 명령
- `<done>`: 완료 기준

### 검증 로직 요구사항

1. **Frontmatter 검증**
   - phase, plan, type 필수
   - depends_on은 배열

2. **Task 검증**
   - name, files, action 필수 (auto)
   - verify, done 권장

3. **에러 핸들링**
   - 파싱 실패 시 상세 오류 메시지
   - 부분 성공 지원 (경고 + 계속)

## 다음 단계

**Phase 3: GSD Converter**에서:
1. Markdown 파서 구현
2. JSON 스키마 정의
3. 변환 로직 구현
4. 검증 시스템 구축
