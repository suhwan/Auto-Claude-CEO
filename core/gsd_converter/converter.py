"""GSD PLAN.md to Implementation Plan Converter"""

import json
from pathlib import Path
from typing import Union

from .models import PlanModel, TaskModel
from .parser import parse_frontmatter, parse_xml_section, parse_tasks
from .schemas import ImplementationPlan, Subtask


class GSDConverter:
    """PLAN.md 파일을 implementation_plan.json으로 변환하는 클래스"""

    def parse_plan(self, path: str) -> PlanModel:
        """
        PLAN.md 파일을 읽고 PlanModel로 파싱

        Args:
            path: PLAN.md 파일 경로

        Returns:
            파싱된 PlanModel 객체

        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
            ParseError: 파싱 중 오류 발생
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"PLAN file not found: {path}")

        content = file_path.read_text(encoding='utf-8')

        # Frontmatter 파싱
        frontmatter = parse_frontmatter(content)

        # XML 섹션 파싱
        objective = parse_xml_section(content, 'objective')
        context_str = parse_xml_section(content, 'context')
        verification_str = parse_xml_section(content, 'verification')
        success_criteria_str = parse_xml_section(content, 'success_criteria')

        # 리스트 필드 파싱 (줄바꿈 기준)
        context = [line.strip() for line in context_str.split('\n') if line.strip()]
        verification = [line.strip() for line in verification_str.split('\n') if line.strip()]
        success_criteria = [line.strip() for line in success_criteria_str.split('\n') if line.strip()]

        # Tasks 파싱
        tasks = parse_tasks(content)

        # PlanModel 생성
        plan = PlanModel(
            phase=frontmatter['phase'],
            plan=frontmatter['plan'],
            type=frontmatter['type'],
            depends_on=frontmatter.get('depends_on', []),
            files_modified=frontmatter.get('files_modified', []),
            objective=objective,
            context=context,
            tasks=tasks,
            verification=verification,
            success_criteria=success_criteria
        )

        return plan

    def to_implementation_plan(self, plan: PlanModel) -> ImplementationPlan:
        """
        PlanModel을 ImplementationPlan으로 변환

        Args:
            plan: 변환할 PlanModel 객체

        Returns:
            변환된 ImplementationPlan 객체
        """
        # spec_id 생성: {phase}-{plan:02d}
        spec_id = f"{plan.phase}-{plan.plan:02d}"

        # 각 task를 subtask로 변환
        subtasks = []
        for index, task in enumerate(plan.tasks):
            # status 결정: type="auto" → "pending", 나머지 → "blocked"
            status = "pending" if task.type == "auto" else "blocked"

            subtask = Subtask(
                id=str(index + 1),
                title=task.name,
                description=task.action,
                files=task.files,
                status=status,
                dependencies=[]  # 기본값
            )
            subtasks.append(subtask)

        return ImplementationPlan(spec_id=spec_id, subtasks=subtasks)

    def convert(self, plan_path: str, output_path: str) -> ImplementationPlan:
        """
        PLAN.md → implementation_plan.json 전체 변환

        Args:
            plan_path: 입력 PLAN.md 파일 경로
            output_path: 출력 JSON 파일 경로

        Returns:
            변환된 ImplementationPlan 객체 (파일에도 저장됨)

        Raises:
            FileNotFoundError: 입력 파일이 존재하지 않는 경우
            ParseError: 파싱 중 오류 발생
        """
        # PLAN.md 파싱
        plan = self.parse_plan(plan_path)

        # ImplementationPlan으로 변환
        impl_plan = self.to_implementation_plan(plan)

        # JSON 파일로 저장
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(impl_plan.to_json(), encoding='utf-8')

        return impl_plan
