"""CEO Teams 레지스트리"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class Team:
    """CEO 팀 정의"""
    name: str  # 예: "marketing/leader"
    description: str
    keywords: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)

    def __post_init__(self):
        """데이터 유효성 검증"""
        if not self.name:
            raise ValueError("name은 필수입니다")
        if "/" not in self.name:
            raise ValueError(f"name은 'team/role' 형식이어야 합니다: {self.name}")


# CEO Teams 레지스트리 (development 제외, Auto-Claude가 담당)
TEAM_REGISTRY: Dict[str, Team] = {
    "planning/leader": Team(
        name="planning/leader",
        description="기획팀 팀장. 프로젝트 기획, 요구사항 분석, 시장 조사",
        keywords=["기획", "요구사항", "분석", "프로젝트", "계획", "로드맵", "스펙", "사양"],
        capabilities=["요구사항 수집", "기획서 작성", "시장 조사", "경쟁사 분석", "프로젝트 계획"]
    ),
    "marketing/leader": Team(
        name="marketing/leader",
        description="마케팅팀 팀장. 콘텐츠 제작, SNS 마케팅, SEO, 브랜딩",
        keywords=["마케팅", "블로그", "콘텐츠", "SNS", "홍보", "광고", "SEO", "브랜딩", "캠페인"],
        capabilities=["블로그 글 작성", "SNS 콘텐츠 제작", "SEO 최적화", "마케팅 전략 수립", "광고 기획"]
    ),
    "legal/leader": Team(
        name="legal/leader",
        description="법무팀 팀장. 계약서 검토, 법률 자문, 규정 준수",
        keywords=["계약", "법률", "약관", "규정", "준수", "컴플라이언스", "법무", "계약서"],
        capabilities=["계약서 검토", "법률 자문", "규정 준수 검토", "약관 작성", "리스크 분석"]
    ),
    "finance/leader": Team(
        name="finance/leader",
        description="재무팀 팀장. 회계, 세금, 예산 관리, 재무 분석",
        keywords=["회계", "재무", "세금", "예산", "비용", "투자", "수익", "손익"],
        capabilities=["재무 분석", "예산 수립", "세금 계산", "투자 분석", "수익성 평가"]
    ),
    "design/leader": Team(
        name="design/leader",
        description="디자인팀 팀장. UI/UX 디자인, 그래픽 디자인, 브랜드 아이덴티티",
        keywords=["디자인", "UI", "UX", "그래픽", "로고", "아이콘", "색상", "레이아웃"],
        capabilities=["UI/UX 디자인", "그래픽 디자인", "브랜드 아이덴티티", "디자인 시스템", "프로토타이핑"]
    ),
    "sales/leader": Team(
        name="sales/leader",
        description="영업팀 팀장. 제안서 작성, 견적, 고객 관리, 영업 전략",
        keywords=["영업", "제안", "견적", "고객", "판매", "세일즈", "제안서", "발주"],
        capabilities=["제안서 작성", "견적 산출", "고객 관리", "영업 전략 수립", "CRM"]
    ),
    "support/leader": Team(
        name="support/leader",
        description="고객지원팀 팀장. 고객 문의 응대, 기술 지원, FAQ 작성",
        keywords=["지원", "문의", "도움", "헬프", "FAQ", "고객센터", "상담", "응대"],
        capabilities=["고객 문의 응대", "기술 지원", "FAQ 작성", "문제 해결", "고객 만족도 관리"]
    ),
    "data/leader": Team(
        name="data/leader",
        description="데이터팀 팀장. 데이터 분석, 리포트 작성, 인사이트 도출",
        keywords=["데이터", "분석", "통계", "리포트", "인사이트", "지표", "대시보드", "시각화"],
        capabilities=["데이터 분석", "리포트 작성", "통계 분석", "인사이트 도출", "데이터 시각화"]
    ),
    "security/leader": Team(
        name="security/leader",
        description="보안팀 팀장. 보안 취약점 분석, 보안 권고, 보안 감사",
        keywords=["보안", "취약점", "해킹", "암호화", "인증", "권한", "방화벽", "침투"],
        capabilities=["보안 취약점 분석", "보안 권고", "보안 감사", "침투 테스트", "보안 정책 수립"]
    ),
}


class TeamRegistry:
    """CEO Teams 레지스트리 관리"""

    def __init__(self, teams: Optional[Dict[str, Team]] = None):
        """
        Args:
            teams: 커스텀 팀 레지스트리. None이면 기본 TEAM_REGISTRY 사용
        """
        self.teams = teams if teams is not None else TEAM_REGISTRY

    def get_team(self, name: str) -> Optional[Team]:
        """
        팀 이름으로 Team 조회

        Args:
            name: 팀 이름 (예: "marketing/leader")

        Returns:
            Team 또는 None
        """
        return self.teams.get(name)

    def list_teams(self) -> List[Team]:
        """
        모든 팀 목록 반환

        Returns:
            Team 리스트
        """
        return list(self.teams.values())

    def find_by_keyword(self, keyword: str) -> Optional[Team]:
        """
        키워드로 팀 검색 (첫 번째 매칭)

        Args:
            keyword: 검색 키워드

        Returns:
            첫 번째 매칭된 Team 또는 None
        """
        keyword_lower = keyword.lower()
        for team in self.teams.values():
            if any(kw.lower() == keyword_lower for kw in team.keywords):
                return team
        return None

    def get_best_match(self, request: str) -> Team:
        """
        요청 텍스트에서 키워드 매칭 스코어 기반으로 최적 팀 선택

        Args:
            request: 사용자 요청 텍스트

        Returns:
            최적 Team (매칭 없으면 planning/leader 반환)
        """
        request_lower = request.lower()
        scores: Dict[str, int] = {}

        # 각 팀별 키워드 매칭 스코어 계산
        for team_name, team in self.teams.items():
            score = 0
            for keyword in team.keywords:
                # 정규식 단어 경계 매칭
                pattern = re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE)
                matches = pattern.findall(request_lower)
                score += len(matches)

            if score > 0:
                scores[team_name] = score

        # 최고 스코어 팀 반환
        if scores:
            best_team_name = max(scores, key=scores.get)
            return self.teams[best_team_name]

        # 매칭 없으면 기본값: planning/leader
        return self.teams["planning/leader"]
