"""Plan Executor: Auto-Claude 실행 시뮬레이션"""

import logging
from typing import List, Optional

from core.gsd_converter.schemas import ImplementationPlan, Subtask
from .bridge import AutoClaudeBridge
from .models import ExecutionResult

logger = logging.getLogger(__name__)


class PlanExecutor:
    """ImplementationPlan을 실행하는 클래스 (Auto-Claude 시뮬레이션)"""

    def __init__(self, bridge: Optional[AutoClaudeBridge] = None):
        """
        PlanExecutor 초기화

        Args:
            bridge: AutoClaudeBridge 인스턴스 (None이면 새로 생성)
        """
        self.bridge = bridge or AutoClaudeBridge()

    def execute(self, plan: ImplementationPlan) -> ExecutionResult:
        """
        Implementation plan 실행 (현재는 시뮬레이션)

        실제 Auto-Claude API 호출은 Phase 5 (Leader Context)에서 UI 통합 시 구현 예정.
        현재는 각 subtask를 순회하며 status를 "completed"로 변경하는 시뮬레이션.

        Args:
            plan: 실행할 ImplementationPlan 객체

        Returns:
            ExecutionResult: 실행 결과 (성공/실패한 subtask 목록 포함)
        """
        logger.info(f"Executing plan: {plan.spec_id}")
        logger.info(f"Total subtasks: {len(plan.subtasks)}")

        completed: List[str] = []
        failed: List[str] = []
        artifacts: List[str] = []

        for subtask in plan.subtasks:
            logger.debug(f"Processing subtask {subtask.id}: {subtask.title}")

            # 실행 시뮬레이션
            success = self.execute_subtask(subtask)

            if success:
                completed.append(subtask.id)
                # 시뮬레이션: 파일이 생성되었다고 가정
                artifacts.extend(subtask.files)
                logger.info(f"✓ Subtask {subtask.id} completed")
            else:
                failed.append(subtask.id)
                logger.warning(f"✗ Subtask {subtask.id} failed")

        # ExecutionResult 생성
        result = self._create_execution_result(plan, completed, failed, artifacts)

        # 결과를 브릿지에 동기화 (STATE.md 업데이트는 Phase 5에서)
        self.bridge.sync_status(result)

        logger.info(f"Execution complete: {result.status}")
        logger.info(f"Completed: {len(completed)}/{len(plan.subtasks)}")

        return result

    def execute_subtask(self, subtask: Subtask) -> bool:
        """
        개별 서브태스크 실행 (시뮬레이션)

        실제 구현에서는 Auto-Claude API를 호출하여:
        1. subtask.description을 프롬프트로 전달
        2. subtask.files에 대해 파일 작업 수행
        3. 결과를 반환

        현재는 항상 성공하는 것으로 시뮬레이션.

        Args:
            subtask: 실행할 Subtask 객체

        Returns:
            성공 여부 (현재는 항상 True)
        """
        # TODO: Phase 5에서 실제 Auto-Claude API 호출 구현
        # 예시:
        # response = auto_claude_client.execute(
        #     prompt=subtask.description,
        #     files=subtask.files
        # )
        # return response.success

        logger.debug(f"Simulating execution of subtask {subtask.id}")
        logger.debug(f"Files to modify: {subtask.files}")

        # 시뮬레이션: 항상 성공
        return True

    def _create_execution_result(
        self,
        plan: ImplementationPlan,
        completed: List[str],
        failed: List[str],
        artifacts: List[str]
    ) -> ExecutionResult:
        """
        ExecutionResult 생성 헬퍼 메서드

        Args:
            plan: 원본 ImplementationPlan
            completed: 완료된 subtask ID 리스트
            failed: 실패한 subtask ID 리스트
            artifacts: 생성된 파일 경로 리스트

        Returns:
            ExecutionResult 객체
        """
        total = len(plan.subtasks)
        completed_count = len(completed)
        failed_count = len(failed)

        # 상태 결정
        if failed_count == 0:
            status = "success"
        elif completed_count > 0:
            status = "partial"
        else:
            status = "failed"

        # 로그 생성 (시뮬레이션)
        logs = [
            f"Plan execution started: {plan.spec_id}",
            f"Total subtasks: {total}",
            f"Completed: {completed_count}",
            f"Failed: {failed_count}",
            f"Status: {status}"
        ]

        return ExecutionResult(
            plan_id=plan.spec_id,
            status=status,
            completed_subtasks=completed,
            failed_subtasks=failed,
            artifacts=artifacts,
            logs=logs
        )
