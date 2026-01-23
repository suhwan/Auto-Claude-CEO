"""
CEO Router - Route tasks to appropriate teams/systems
"""

from typing import Optional

from .classifier import TaskClassifier
from .models import TaskType, RoutingResult


class CEORouter:
    """Routes tasks to coding (Auto-Claude) or non-coding (CEO Teams)"""

    # Team keywords for routing non-coding tasks
    TEAM_KEYWORDS = {
        "planning/leader": [
            "기획", "요구사항", "분석", "plan", "requirement", "analysis", "strategy"
        ],
        "marketing/leader": [
            "마케팅", "블로그", "SEO", "콘텐츠", "marketing", "blog", "content", "social"
        ],
        "legal/leader": [
            "계약", "법률", "법무", "contract", "legal", "compliance"
        ],
        "finance/leader": [
            "회계", "세금", "재무", "예산", "finance", "accounting", "tax", "budget"
        ],
        "design/leader": [
            "디자인", "UI", "UX", "design", "wireframe", "mockup", "visual"
        ],
        "sales/leader": [
            "영업", "제안서", "견적", "sales", "proposal", "quote", "client"
        ],
        "data/leader": [
            "데이터", "리포트", "분석", "data", "report", "analytics", "metrics"
        ],
        "security/leader": [
            "보안", "취약점", "security", "vulnerability", "audit"
        ],
        "support/leader": [
            "문의", "지원", "도움", "support", "help", "customer"
        ],
    }

    def __init__(self, classifier: Optional[TaskClassifier] = None):
        """
        Initialize router

        Args:
            classifier: Task classifier (creates default if None)
        """
        self.classifier = classifier or TaskClassifier()

    def classify(self, request: str) -> TaskType:
        """
        Classify request as coding/non-coding (convenience method)

        Args:
            request: User request text

        Returns:
            TaskType
        """
        result = self.classifier.classify(request)
        return result.task_type

    def get_team(self, request: str) -> str:
        """
        Determine which team should handle a non-coding task

        Args:
            request: User request text

        Returns:
            Team name (e.g., "planning/leader")
        """
        request_lower = request.lower()

        # Calculate score for each team
        team_scores = {}
        for team, keywords in self.TEAM_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in request_lower)
            if score > 0:
                team_scores[team] = score

        # Return team with highest score
        if team_scores:
            best_team = max(team_scores.items(), key=lambda x: x[1])[0]
            return best_team

        # Default to planning if no keywords match
        return "planning/leader"

    def route(
        self,
        request: str,
        task_type: Optional[TaskType] = None
    ) -> RoutingResult:
        """
        Route a task to the appropriate system/team

        Args:
            request: User request
            task_type: Task type (auto-classifies if None)

        Returns:
            RoutingResult with routing decision
        """
        # Classify if task_type not provided
        if task_type is None:
            result = self.classifier.classify(request)
        else:
            result = RoutingResult(
                task_type=task_type,
                target="",
                confidence=1.0,
                keywords_matched=[]
            )

        # Determine target
        if result.task_type == TaskType.CODING:
            result.target = "auto-claude"
        elif result.task_type == TaskType.NON_CODING:
            result.target = self.get_team(request)
        else:  # MIXED
            # Default to coding for mixed tasks
            result.target = "auto-claude"

        return result

    def to_dict(self) -> dict:
        """Export router configuration as dictionary"""
        return {
            'team_keywords': self.TEAM_KEYWORDS,
            'teams': list(self.TEAM_KEYWORDS.keys())
        }
