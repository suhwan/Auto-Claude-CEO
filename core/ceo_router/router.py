"""CEO 라우터 - 작업 분류 및 팀 분배"""

from typing import Optional

from .classifier import TaskClassifier
from .models import TaskType, RoutingResult


class CEORouter:
    """작업 유형별 라우팅 (코딩→Auto-Claude, 비코딩→CEO Teams)"""

    # 팀별 키워드 매핑
    TEAM_KEYWORDS = {
        "planning/leader": ["기획", "요구사항", "분석", "plan", "requirement", "analysis"],
        "marketing/leader": ["마케팅", "블로그", "SEO", "콘텐츠", "marketing", "blog", "content"],
        "legal/leader": ["계약", "법률", "법무", "contract", "legal"],
        "finance/leader": ["회계", "세금", "재무", "예산", "finance", "accounting", "tax", "budget"],
        "design/leader": ["디자인", "UI", "UX", "design"],
        "sales/leader": ["영업", "제안서", "견적", "sales", "proposal", "quote"],
        "data/leader": ["데이터", "리포트", "분석", "data", "report", "analytics"],
        "security/leader": ["보안", "취약점", "security", "vulnerability"],
        "support/leader": ["문의", "지원", "도움", "support", "help"],
    }

    def __init__(self, classifier: Optional[TaskClassifier] = None):
        """
        라우터 초기화

        Args:
            classifier: 작업 분류기 (None이면 기본 생성)
        """
        self.classifier = classifier or TaskClassifier()

    def classify(self, request: str) -> TaskType:
        """
        요청을 코딩/비코딩으로 분류 (간편 인터페이스)

        Args:
            request: 사용자 요청 텍스트

        Returns:
            TaskType: 작업 유형
        """
        result = self.classifier.classify(request)
        return result.task_type

    def get_team(self, request: str) -> str:
        """
        비코딩 작업의 담당 팀 결정

        Args:
            request: 사용자 요청 텍스트

        Returns:
            str: 팀 이름 (예: "planning/leader")
        """
        request_lower = request.lower()

        # 각 팀별 키워드 매칭 점수 계산
        team_scores = {}
        for team, keywords in self.TEAM_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in request_lower)
            if score > 0:
                team_scores[team] = score

        # 가장 높은 점수의 팀 반환
        if team_scores:
            best_team = max(team_scores.items(), key=lambda x: x[1])[0]
            return best_team

        # 키워드가 없으면 기본값 (기획팀)
        return "planning/leader"

    def route(
        self,
        request: str,
        task_type: Optional[TaskType] = None
    ) -> RoutingResult:
        """
        분류된 작업을 적절한 시스템으로 라우팅

        Args:
            request: 사용자 요청
            task_type: 작업 유형 (None이면 자동 분류)

        Returns:
            RoutingResult: 라우팅 결과
        """
        # task_type이 없으면 분류 수행
        if task_type is None:
            result = self.classifier.classify(request)
        else:
            result = RoutingResult(
                task_type=task_type,
                target="",
                confidence=1.0,
                keywords_matched=[]
            )

        # target 결정
        if result.task_type == TaskType.CODING:
            result.target = "auto-claude"
        elif result.task_type == TaskType.NON_CODING:
            result.target = self.get_team(request)
        else:  # MIXED
            # 코딩 우선 (코딩 + 비코딩이 섞였을 때)
            result.target = "auto-claude"

        return result
