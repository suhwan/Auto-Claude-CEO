"""작업 분류기 - 코딩/비코딩 분류"""

import re
from typing import List, Tuple

from .models import TaskType, RoutingResult


# 코딩 관련 키워드
CODING_KEYWORDS = [
    "코드", "개발", "구현", "만들어", "작성", "수정",
    "API", "함수", "클래스", "버그", "디버그", "테스트",
    "빌드", "배포", "웹사이트", "앱", "서버",
    "fix", "implement", "create", "build", "code",
    "function", "class", "debug", "deploy", "website", "app", "server"
]

# 비코딩 관련 키워드
NON_CODING_KEYWORDS = [
    "기획", "분석", "리포트", "문서", "계약", "법률",
    "마케팅", "블로그", "SEO", "영업", "제안서", "견적",
    "회의", "조사", "연구",
    "plan", "report", "document", "contract", "legal",
    "marketing", "blog", "sales", "proposal", "quote",
    "meeting", "research"
]


class TaskClassifier:
    """작업 유형 분류기"""

    def __init__(self):
        """분류기 초기화"""
        # 정규식 패턴 컴파일 (성능 최적화)
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
        텍스트에서 패턴 매칭 횟수와 매칭된 키워드 반환

        Args:
            text: 검색할 텍스트
            patterns: 정규식 패턴 리스트
            keywords: 키워드 리스트

        Returns:
            (매칭 횟수, 매칭된 키워드 리스트)
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
        요청을 코딩/비코딩으로 분류

        Args:
            request: 사용자 요청 텍스트

        Returns:
            RoutingResult: 분류 결과
        """
        # 각 카테고리별 매칭 횟수 계산
        coding_score, coding_matched = self._count_matches(
            request, self._coding_patterns, CODING_KEYWORDS
        )
        non_coding_score, non_coding_matched = self._count_matches(
            request, self._non_coding_patterns, NON_CODING_KEYWORDS
        )

        # 작업 유형 결정
        total = coding_score + non_coding_score

        if coding_score > non_coding_score:
            task_type = TaskType.CODING
            keywords_matched = coding_matched
        elif non_coding_score > coding_score:
            task_type = TaskType.NON_CODING
            keywords_matched = non_coding_matched
        else:
            # 둘 다 0이거나 같으면 MIXED
            task_type = TaskType.MIXED if total > 0 else TaskType.NON_CODING
            keywords_matched = coding_matched + non_coding_matched

        # 신뢰도 계산 (차이가 클수록 신뢰도 높음)
        confidence = abs(coding_score - non_coding_score) / max(total, 1)

        return RoutingResult(
            task_type=task_type,
            target="",  # router에서 설정
            confidence=confidence,
            keywords_matched=keywords_matched
        )

    def is_coding_task(self, request: str) -> bool:
        """
        코딩 작업 여부 확인 (헬퍼 메서드)

        Args:
            request: 사용자 요청 텍스트

        Returns:
            bool: 코딩 작업이면 True
        """
        result = self.classify(request)
        return result.task_type == TaskType.CODING
