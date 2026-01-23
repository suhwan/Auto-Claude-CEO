"""
Task Classifier - Classify tasks as coding/non-coding
"""

import re
from typing import List, Tuple

from .models import TaskType, RoutingResult


# Coding-related keywords
CODING_KEYWORDS = [
    # Korean
    "코드", "개발", "구현", "만들어", "작성", "수정",
    "API", "함수", "클래스", "버그", "디버그", "테스트",
    "빌드", "배포", "웹사이트", "앱", "서버", "프로그래밍",
    # English
    "code", "develop", "implement", "create", "build", "write",
    "fix", "function", "class", "bug", "debug", "test",
    "deploy", "website", "app", "server", "programming",
    "software", "script", "module", "package", "library"
]

# Non-coding related keywords
NON_CODING_KEYWORDS = [
    # Korean
    "기획", "분석", "리포트", "문서", "계약", "법률",
    "마케팅", "블로그", "SEO", "영업", "제안서", "견적",
    "회의", "조사", "연구", "보고서", "데이터", "디자인",
    "예산", "세금", "회계",
    # English
    "plan", "planning", "analysis", "report", "document", "contract",
    "legal", "marketing", "blog", "sales", "proposal", "quote",
    "meeting", "research", "survey", "design", "budget", "tax",
    "accounting", "strategy", "communication", "writing"
]


class TaskClassifier:
    """Classifies tasks as coding or non-coding"""

    def __init__(self):
        """Initialize classifier"""
        # Compile regex patterns for performance
        self._coding_patterns = [
            re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
            for kw in CODING_KEYWORDS
        ]
        self._non_coding_patterns = [
            re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
            for kw in NON_CODING_KEYWORDS
        ]

    def _count_matches(
        self,
        text: str,
        patterns: List[re.Pattern],
        keywords: List[str]
    ) -> Tuple[int, List[str]]:
        """
        Count pattern matches and return matched keywords

        Args:
            text: Text to search
            patterns: Regex patterns
            keywords: Keyword list

        Returns:
            Tuple of (match count, matched keywords)
        """
        count = 0
        matched = []

        for pattern, keyword in zip(patterns, keywords):
            if pattern.search(text):
                count += 1
                matched.append(keyword)

        return count, matched

    def classify(self, request: str) -> RoutingResult:
        """
        Classify request as coding/non-coding

        Args:
            request: User request text

        Returns:
            RoutingResult with classification
        """
        # Count matches for each category
        coding_score, coding_matched = self._count_matches(
            request, self._coding_patterns, CODING_KEYWORDS
        )
        non_coding_score, non_coding_matched = self._count_matches(
            request, self._non_coding_patterns, NON_CODING_KEYWORDS
        )

        # Determine task type
        total = coding_score + non_coding_score

        if coding_score > non_coding_score:
            task_type = TaskType.CODING
            keywords_matched = coding_matched
        elif non_coding_score > coding_score:
            task_type = TaskType.NON_CODING
            keywords_matched = non_coding_matched
        else:
            # Equal or both 0
            task_type = TaskType.MIXED if total > 0 else TaskType.NON_CODING
            keywords_matched = coding_matched + non_coding_matched

        # Calculate confidence (higher difference = higher confidence)
        confidence = abs(coding_score - non_coding_score) / max(total, 1)

        return RoutingResult(
            task_type=task_type,
            target="",  # Set by router
            confidence=confidence,
            keywords_matched=keywords_matched
        )

    def is_coding_task(self, request: str) -> bool:
        """
        Check if request is a coding task

        Args:
            request: User request text

        Returns:
            True if coding task
        """
        result = self.classify(request)
        return result.task_type == TaskType.CODING
