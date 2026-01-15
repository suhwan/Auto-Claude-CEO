# CEO Routing Rules

## Overview

CEO는 사용자 요청을 분석하여 적절한 팀에 자동으로 분배합니다.

## Routing Table

| 키워드 | 담당 팀 (subagent_type) |
|--------|------------------------|
| 코드, 개발, 버그, API, 구현, 프로그래밍 | development/leader |
| 기획, 요구사항, 분석, 프로젝트, 계획 | planning/leader |
| 디자인, UI, UX, 와이어프레임, 목업 | design/leader |
| 블로그, 콘텐츠, SEO, 마케팅, 홍보 | marketing/leader |
| 제안서, 견적, 영업, 고객, 계약 수주 | sales/leader |
| 문의, 지원, 도움, 트러블슈팅 | support/leader |
| 회계, 세금, 예산, 재무, 비용 | finance/leader |
| 계약서, 법률, 컴플라이언스, 라이선스 | legal/leader |
| 데이터, 리포트, 분석, 대시보드, 지표 | data/leader |
| 보안, 취약점, 해킹, 인증 | security/leader |

## Routing Algorithm

```
1. 요청 분석
   ↓
2. 핵심 키워드 추출
   ↓
3. 라우팅 테이블 매칭
   ↓
4. 복합 업무? → 순차적 팀 호출
   ↓
5. Task tool로 팀 에이전트 호출
```

### Priority Rules

1. **명시적 키워드 우선**: "코드 작성해줘" → development
2. **복합 키워드**: 여러 팀 관련 → 순차 처리
3. **기본 라우터**: 매칭 없을 시 → planning (기획팀)

## Routing Examples

### 단일 팀 라우팅
```
"웹사이트 만들어줘"
→ 분석: "웹사이트" = 개발 관련
→ Task: development/leader
```

### 복합 업무 라우팅
```
"블로그 사이트 만들고 첫 글 써줘"
→ 분석: "사이트" = 개발, "글 써줘" = 마케팅
→ Task 1: development/leader (사이트 구축)
→ Task 2: marketing/leader (콘텐츠 작성)
```

## Coding vs Non-Coding 구분

### Coding Tasks (→ Auto-Claude)
- 코드 작성, 수정, 디버깅
- API 개발
- 테스트 작성
- 빌드, 배포

### Non-Coding Tasks (→ CEO Teams)
- 기획서 작성
- 블로그/콘텐츠 작성
- 계약서 검토
- 데이터 분석 리포트
- 마케팅 전략
- 고객 지원

## Response Format

```
[CEO] 업무 분석 완료
- 담당 팀: {팀 이름}
- 작업 내용: {요약}

---
{팀 결과}
---

[CEO] 작업 완료
```

## Integration with Auto-Claude

### Hybrid Routing Logic
```python
def route_request(request):
    if is_coding_task(request):
        # Auto-Claude의 12 에이전트 파이프라인
        return route_to_auto_claude(request)
    else:
        # CEO의 10개 팀
        team = match_keywords(request)
        return route_to_ceo_teams(team, request)
```

### Keyword Classification
```python
CODING_KEYWORDS = [
    "코드", "개발", "구현", "프로그래밍", "버그", "API",
    "함수", "클래스", "테스트", "빌드", "배포", "디버그"
]

def is_coding_task(request):
    return any(kw in request for kw in CODING_KEYWORDS)
```
