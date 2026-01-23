"""GSD PLAN.md 검증 로직"""

from typing import List

from .models import PlanModel, TaskModel
from .errors import ValidationError


class PlanValidator:
    """PlanModel 검증 클래스"""

    def validate(self, plan: PlanModel) -> List[str]:
        """
        PlanModel 검증. 오류 목록 반환 (빈 리스트 = 유효).

        Args:
            plan: 검증할 PlanModel 객체

        Returns:
            오류 메시지 리스트 (빈 리스트면 검증 통과)
        """
        errors = []
        errors.extend(self._validate_frontmatter(plan))
        errors.extend(self._validate_tasks(plan.tasks))
        return errors

    def _validate_frontmatter(self, plan: PlanModel) -> List[str]:
        """
        Frontmatter 필수 필드 검증

        Args:
            plan: 검증할 PlanModel 객체

        Returns:
            오류 메시지 리스트
        """
        errors = []

        # phase: 비어있지 않은 문자열
        if not plan.phase or not isinstance(plan.phase, str) or not plan.phase.strip():
            errors.append("phase: expected non-empty string")

        # plan: 양의 정수
        if not isinstance(plan.plan, int) or plan.plan <= 0:
            errors.append(f"plan: expected positive integer, got {plan.plan}")

        # type: "execute" | "tdd"
        valid_types = ["execute", "tdd"]
        if plan.type not in valid_types:
            errors.append(f"type: expected one of {valid_types}, got '{plan.type}'")

        return errors

    def _validate_tasks(self, tasks: List[TaskModel]) -> List[str]:
        """
        각 task의 필수 필드 검증

        Args:
            tasks: TaskModel 리스트

        Returns:
            오류 메시지 리스트
        """
        errors = []
        valid_task_types = ["auto", "checkpoint:human-verify", "checkpoint:decision"]

        for index, task in enumerate(tasks):
            task_prefix = f"Task {index + 1}"

            # task.name: 비어있지 않은 문자열
            if not task.name or not isinstance(task.name, str) or not task.name.strip():
                errors.append(f"{task_prefix}: name expected non-empty string")

            # task.type: 유효한 타입
            if task.type not in valid_task_types:
                errors.append(f"{task_prefix}: type expected one of {valid_task_types}, got '{task.type}'")

            # task.action: auto 타입일 경우 비어있지 않은 문자열
            if task.type == "auto":
                if not task.action or not isinstance(task.action, str) or not task.action.strip():
                    errors.append(f"{task_prefix}: action expected non-empty string for type 'auto'")

        return errors

    def validate_or_raise(self, plan: PlanModel) -> None:
        """
        검증 실패 시 ValidationError 발생

        Args:
            plan: 검증할 PlanModel 객체

        Raises:
            ValidationError: 검증 실패 시
        """
        errors = self.validate(plan)
        if errors:
            error_message = "Plan validation failed:\n- " + "\n- ".join(errors)
            raise ValidationError(
                field="plan",
                expected="valid plan structure",
                actual=f"{len(errors)} validation error(s)"
            )
