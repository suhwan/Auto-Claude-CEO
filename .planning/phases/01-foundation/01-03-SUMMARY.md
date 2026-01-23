---
phase: 01-foundation
plan: 03
subsystem: ceo-teams
provides: [ceo-teams-structure, routing-requirements]
affects: [04-ceo-router]
---

# CEO Teams 분석 요약

## CEO 시스템 개요

CEO는 **AI 에이전트 기반 1인 기업 플랫폼**입니다.

- **10개 팀**: planning, development, design, marketing, sales, support, finance, legal, data, security
- **19개 에이전트**: 팀장 10명 + 전문가 9명

### 조직 구조
```
CEO (라우터)
├── Core Teams: 기획, 개발, 디자인
├── Business Teams: 마케팅, 영업, 고객지원
├── Back-office: 재무, 법무
└── Optional: 데이터, 보안
```

## 라우팅 규칙

### 키워드 → 팀 매핑
| 키워드 | 팀 |
|--------|-----|
| 코드, API, 버그 | development |
| 기획, 분석 | planning |
| UI, UX | design |
| 블로그, SEO | marketing |
| 제안서, 견적 | sales |
| 문의, 지원 | support |
| 회계, 세금 | finance |
| 계약, 법률 | legal |
| 데이터, 리포트 | data |
| 보안, 취약점 | security |

### 라우팅 알고리즘
1. 요청 분석 → 키워드 추출
2. 라우팅 테이블 매칭
3. 복합 업무 → 순차 처리
4. Task tool로 팀 호출

## 통합 라우터 요구사항 (Phase 4)

### 코딩 vs 비코딩 분류

```
사용자 요청
    ↓
코딩 작업? ─── Yes ──→ Auto-Claude (12 에이전트)
    │                    spec → plan → code → qa
    No
    ↓
CEO Teams (10개 팀)
    │
    └→ 키워드 매칭 → 적절한 팀 호출
```

### 분류 기준

**코딩 작업 (Auto-Claude)**
- 코드 작성/수정/디버깅
- API 개발
- 테스트 작성
- 빌드/배포

**비코딩 작업 (CEO Teams)**
- 기획서, 블로그, 계약서
- 데이터 분석 리포트
- 마케팅 전략
- 고객 지원

### 통합 설계 방향

1. **키워드 분류기**
   - CODING_KEYWORDS 리스트
   - is_coding_task() 함수

2. **Auto-Claude 연결**
   - spec → implementation_plan 파이프라인
   - CoderAgent 활용

3. **CEO Teams 연결**
   - 기존 라우팅 테이블 유지
   - Task tool로 subagent 호출

4. **확장 포인트**
   - 새 팀 추가: agents/{team}/leader.md
   - 라우팅 규칙 수정: commands/ceo.md

## 다음 단계

**Phase 4: CEO Router**에서:
1. 통합 라우터 코어 구현
2. Auto-Claude 연동
3. CEO Teams 연동
4. 테스트 및 검증
