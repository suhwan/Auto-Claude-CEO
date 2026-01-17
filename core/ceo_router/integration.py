"""CEO 통합 오케스트레이터 - 코딩/비코딩 작업 통합 처리"""

import time
from typing import Optional

from .models import AgentResult
from .router import CEORouter
from .teams import Team, TeamRegistry


class CEOIntegration:
    """CEO Teams와 Auto-Claude 통합 오케스트레이터"""

    def __init__(
        self,
        router: Optional[CEORouter] = None,
        team_registry: Optional[TeamRegistry] = None
    ):
        """
        통합 오케스트레이터 초기화

        Args:
            router: CEORouter 인스턴스 (None이면 기본 생성)
            team_registry: TeamRegistry 인스턴스 (None이면 기본 생성)
        """
        self.router = router or CEORouter()
        self.team_registry = team_registry or TeamRegistry()

    def process_request(self, request: str) -> AgentResult:
        """
        사용자 요청을 분류하고 적절한 시스템/팀으로 라우팅하여 실행

        Args:
            request: 사용자 요청 텍스트

        Returns:
            AgentResult: 실행 결과
        """
        start_time = time.time()

        try:
            # 1. 작업 분류 및 라우팅
            routing_result = self.router.route(request)

            # 2. target에 따라 실행
            if routing_result.target == "auto-claude":
                # Auto-Claude로 위임 (현재는 stub)
                result = self._dispatch_to_auto_claude(request)
            else:
                # CEO Team으로 위임
                result = self.dispatch_to_team(routing_result.target, request)

            # 3. 실행 시간 기록
            result.duration = time.time() - start_time
            return result

        except Exception as e:
            # 오류 발생 시
            duration = time.time() - start_time
            return AgentResult(
                success=False,
                agent_type="ceo-integration",
                output=None,
                errors=[str(e)],
                duration=duration
            )

    def dispatch_to_team(self, team_name: str, request: str) -> AgentResult:
        """
        CEO Team으로 작업 분배

        Args:
            team_name: 팀 이름 (예: "marketing/leader")
            request: 사용자 요청

        Returns:
            AgentResult: 실행 결과
        """
        # TeamRegistry에서 Team 조회
        team = self.team_registry.get_team(team_name)

        if not team:
            return AgentResult(
                success=False,
                agent_type=team_name,
                output=None,
                errors=[f"팀을 찾을 수 없습니다: {team_name}"],
                duration=0.0
            )

        # 팀 태스크 실행
        return self.execute_team_task(team, request)

    def execute_team_task(self, team: Team, request: str) -> AgentResult:
        """
        개별 CEO Team 태스크 실행

        Args:
            team: Team 인스턴스
            request: 사용자 요청

        Returns:
            AgentResult: 실행 결과

        Note:
            실제 Claude Code Task tool 호출은 Claude Code 환경에서 실행됩니다.
            여기서는 시뮬레이션 결과를 반환합니다.
        """
        # TODO: 실제 Claude Code 환경에서는 Task tool 호출
        # Task(
        #     subagent_type=team.name,
        #     prompt=request
        # )

        # 현재는 시뮬레이션 결과 반환
        return AgentResult(
            success=True,
            agent_type=team.name,
            output={
                "team": team.name,
                "description": team.description,
                "request": request,
                "status": "simulated",
                "message": f"{team.name} 팀이 요청을 처리할 준비가 되었습니다."
            },
            errors=[],
            duration=0.0
        )

    def _dispatch_to_auto_claude(self, request: str) -> AgentResult:
        """
        Auto-Claude로 작업 분배 (stub)

        Args:
            request: 사용자 요청

        Returns:
            AgentResult: 실행 결과

        Note:
            실제 Auto-Claude Bridge 연동은 04-02에서 구현됩니다.
        """
        # TODO: AutoClaudeBridge 연동
        return AgentResult(
            success=True,
            agent_type="auto-claude",
            output={
                "request": request,
                "status": "stub",
                "message": "Auto-Claude 연동은 04-02에서 구현됩니다."
            },
            errors=[],
            duration=0.0
        )
