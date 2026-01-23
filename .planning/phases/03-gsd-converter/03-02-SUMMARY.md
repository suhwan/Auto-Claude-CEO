---
phase: 03-gsd-converter
plan: 02
status: completed
date: 2026-01-15
---

# 03-02: JSON 스키마 및 변환 로직 구현 - 완료

## 목표

PlanModel을 Auto-Claude의 implementation_plan.json 형식으로 변환하는 스키마 및 변환 로직 구현

## 완료된 작업

### Task 1: JSON 스키마 정의
- `core/gsd_converter/schemas.py` 생성
- `Subtask` dataclass 정의
  - id, title, description, files, status, dependencies 필드
- `ImplementationPlan` dataclass 정의
  - spec_id, subtasks 필드
  - `to_dict()`: dataclasses.asdict()를 사용한 dict 변환
  - `to_json()`: JSON 문자열 직렬화 (ensure_ascii=False로 한글 지원)

### Task 2: 변환 로직 구현
- `core/gsd_converter/converter.py` 생성
- `GSDConverter` 클래스 구현
  - `parse_plan(path)`: PLAN.md 파일 읽기 및 PlanModel 파싱
    - frontmatter, XML 섹션, tasks 파싱
    - 파일 존재 여부 검증
  - `to_implementation_plan(plan)`: PlanModel → ImplementationPlan 변환
    - spec_id 생성: `{phase}-{plan:02d}`
    - task → subtask 변환
    - status 자동 설정: type="auto" → "pending", 나머지 → "blocked"
  - `convert(plan_path, output_path)`: 전체 변환 파이프라인
    - 파싱 → 변환 → JSON 파일 저장
    - 디렉토리 자동 생성

### Task 3: 패키지 통합
- `core/gsd_converter/__init__.py` 업데이트
- 새로운 클래스 export 추가
  - ImplementationPlan, Subtask, GSDConverter
- `__all__` 리스트 업데이트
- 패키지 독스트링 업데이트

## 검증 완료

### 단위 검증
- ✓ schemas.py: ImplementationPlan.to_json() 정상 동작
- ✓ converter.py: GSDConverter 임포트 성공
- ✓ __init__.py: 패키지 레벨 임포트 성공

### 통합 테스트
- ✓ 실제 PLAN 파일(03-02-PLAN.md) 파싱 성공
  - Phase: 03-gsd-converter
  - Plan: 2
  - Tasks: 3개
- ✓ ImplementationPlan 변환 성공
  - spec_id: "03-gsd-converter-02"
  - 3개 subtask 생성
  - 한글 정상 처리 (UTF-8)
- ✓ JSON 파일 생성 및 저장 성공

### 변환 규칙 검증
- ✓ spec_id = f"{phase}-{plan:02d}" 형식
- ✓ subtask.id = 순차적 문자열 ("1", "2", "3", ...)
- ✓ subtask.title = task.name
- ✓ subtask.description = task.action
- ✓ subtask.status = "pending" (type="auto") / "blocked" (기타)
- ✓ subtask.dependencies = [] (기본값)

## 파일 변경사항

### 신규 파일
- `core/gsd_converter/schemas.py` (31줄)
- `core/gsd_converter/converter.py` (125줄)

### 수정 파일
- `core/gsd_converter/__init__.py` (+7줄)

### Git 커밋
```
commit 0b6fff70d89c60c3dda04b9349de7c0c5aa3dd69
feat(03-02): JSON 스키마 및 변환 로직 구현

- ImplementationPlan, Subtask dataclass 정의 (schemas.py)
- GSDConverter 클래스 구현 (converter.py)
  - parse_plan(): PLAN.md -> PlanModel 파싱
  - to_implementation_plan(): PlanModel -> ImplementationPlan 변환
  - convert(): 전체 변환 파이프라인 (파일 저장 포함)
- 패키지 통합: __init__.py 업데이트
```

## 주요 구현 내용

### 데이터 스키마 (schemas.py)
```python
@dataclass
class Subtask:
    id: str
    title: str
    description: str
    files: List[str]
    status: str
    dependencies: List[str] = field(default_factory=list)

@dataclass
class ImplementationPlan:
    spec_id: str
    subtasks: List[Subtask]

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
```

### 변환 로직 (converter.py)
```python
class GSDConverter:
    def parse_plan(self, path: str) -> PlanModel:
        # PLAN.md 파일 읽기 및 파싱

    def to_implementation_plan(self, plan: PlanModel) -> ImplementationPlan:
        # PlanModel → ImplementationPlan 변환
        spec_id = f"{plan.phase}-{plan.plan:02d}"
        subtasks = [...]

    def convert(self, plan_path: str, output_path: str) -> ImplementationPlan:
        # 파싱 → 변환 → 파일 저장
```

## 성공 기준 달성

- ✓ JSON 스키마 dataclass 정의 완료
- ✓ GSDConverter 변환 로직 구현
- ✓ 패키지 통합 완료
- ✓ 실제 PLAN 파일로 검증 완료

## 다음 단계

03-03: CLI 도구 구현
- argparse를 사용한 명령줄 인터페이스
- `gsd-convert` 실행 파일
- 사용 예시: `gsd-convert PLAN.md -o output.json`
