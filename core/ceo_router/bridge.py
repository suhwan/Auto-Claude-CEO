"""Auto-Claude Bridge: GSD PLAN.md를 Auto-Claude 파이프라인에 연결"""

import json
import logging
from pathlib import Path
from typing import Optional

from core.gsd_converter import GSDConverter
from core.gsd_converter.schemas import ImplementationPlan
from .models import ExecutionResult

logger = logging.getLogger(__name__)


class AutoClaudeBridge:
    """GSD PLAN.md를 Auto-Claude 파이프라인으로 전달하는 브릿지 클래스"""

    def __init__(
        self,
        gsd_converter: Optional[GSDConverter] = None,
        output_dir: str = ".auto-claude"
    ):
        """
        AutoClaudeBridge 초기화

        Args:
            gsd_converter: GSDConverter 인스턴스 (None이면 새로 생성)
            output_dir: implementation_plan.json 저장 디렉토리
        """
        self.converter = gsd_converter or GSDConverter(validate=True)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def prepare_plan(self, plan_path: str) -> ImplementationPlan:
        """
        PLAN.md 파일을 읽고 implementation_plan.json 생성

        Args:
            plan_path: PLAN.md 파일 경로

        Returns:
            변환된 ImplementationPlan 객체

        Raises:
            FileNotFoundError: PLAN.md 파일이 존재하지 않는 경우
            GSDConverterError: 파싱/검증 실패
        """
        try:
            logger.info(f"Converting PLAN.md: {plan_path}")

            # GSDConverter를 사용하여 변환
            output_path = self.get_plan_path_from_file(plan_path)
            impl_plan = self.converter.convert(plan_path, output_path)

            logger.info(f"Implementation plan created: {output_path}")
            logger.info(f"Spec ID: {impl_plan.spec_id}, Subtasks: {len(impl_plan.subtasks)}")

            return impl_plan

        except Exception as e:
            logger.error(f"Failed to prepare plan: {e}")
            raise

    def get_plan_path(self, plan: ImplementationPlan) -> str:
        """
        ImplementationPlan의 JSON 파일 경로 반환

        Args:
            plan: ImplementationPlan 객체

        Returns:
            JSON 파일 경로 (절대 경로)
        """
        filename = f"{plan.spec_id}_implementation_plan.json"
        return str((self.output_dir / filename).resolve())

    def get_plan_path_from_file(self, plan_path: str) -> str:
        """
        PLAN.md 파일 경로로부터 출력 JSON 경로 생성

        Args:
            plan_path: PLAN.md 파일 경로

        Returns:
            출력 JSON 파일 경로
        """
        # PLAN.md에서 spec_id 추출을 위해 임시로 파싱 (출력 없이)
        plan_model = self.converter.parse_plan(plan_path)
        spec_id = f"{plan_model.phase}-{plan_model.plan:02d}"
        filename = f"{spec_id}_implementation_plan.json"
        return str((self.output_dir / filename).resolve())

    def sync_status(self, result: ExecutionResult) -> None:
        """
        실행 결과를 STATE.md에 동기화

        현재는 로그 출력으로 대체. 실제 STATE.md 업데이트는 Phase 5에서 구현 예정.

        Args:
            result: Auto-Claude 실행 결과
        """
        logger.info(f"Syncing execution result for plan: {result.plan_id}")
        logger.info(f"Status: {result.status}")
        logger.info(f"Completed: {len(result.completed_subtasks)}/{len(result.completed_subtasks) + len(result.failed_subtasks)}")

        if result.failed_subtasks:
            logger.warning(f"Failed subtasks: {result.failed_subtasks}")

        if result.artifacts:
            logger.info(f"Generated artifacts: {result.artifacts}")

        # TODO: Phase 5에서 STATE.md 파일 업데이트 구현
        logger.debug("STATE.md sync is placeholder - will be implemented in Phase 5")

    def get_progress(self, spec_id: str) -> dict:
        """
        implementation_plan.json 파일에서 진행 상황 조회

        Args:
            spec_id: Plan의 spec_id (예: "04-02")

        Returns:
            진행 상황 딕셔너리:
            {
                "spec_id": str,
                "total": int,
                "pending": int,
                "in_progress": int,
                "completed": int,
                "blocked": int,
                "subtasks": List[dict]
            }

        Raises:
            FileNotFoundError: JSON 파일이 존재하지 않는 경우
        """
        filename = f"{spec_id}_implementation_plan.json"
        json_path = self.output_dir / filename

        if not json_path.exists():
            raise FileNotFoundError(f"Implementation plan not found: {json_path}")

        # JSON 파일 읽기
        data = json.loads(json_path.read_text(encoding='utf-8'))

        # Status별 카운트
        status_counts = {
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "blocked": 0,
        }

        subtasks = data.get("subtasks", [])
        for subtask in subtasks:
            status = subtask.get("status", "pending")
            if status in status_counts:
                status_counts[status] += 1

        return {
            "spec_id": spec_id,
            "total": len(subtasks),
            **status_counts,
            "subtasks": subtasks,
        }
