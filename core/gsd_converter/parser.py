"""GSD PLAN.md 파서 구현"""

import re
from typing import Dict, List, Any
import yaml

from .models import PlanModel, TaskModel


class ParseError(Exception):
    """파싱 중 발생하는 에러"""
    pass


def parse_frontmatter(content: str) -> dict:
    """
    PLAN.md의 YAML frontmatter를 파싱.
    --- 로 시작하고 --- 로 끝나는 부분 추출.

    Args:
        content: PLAN.md 파일 내용

    Returns:
        파싱된 frontmatter 딕셔너리

    Raises:
        ParseError: frontmatter가 없거나 필수 필드가 누락된 경우
    """
    # Frontmatter 추출 (---로 시작하고 ---로 끝남)
    pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.search(pattern, content, re.DOTALL | re.MULTILINE)

    if not match:
        raise ParseError("Frontmatter not found. PLAN.md must start with YAML frontmatter between --- markers.")

    yaml_content = match.group(1)

    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ParseError(f"Invalid YAML in frontmatter: {e}")

    if not isinstance(data, dict):
        raise ParseError("Frontmatter must be a YAML dictionary")

    # 필수 필드 검증
    required_fields = ['phase', 'plan', 'type']
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        raise ParseError(f"Missing required frontmatter fields: {', '.join(missing_fields)}")

    return data


def parse_xml_section(content: str, tag: str) -> str:
    """
    XML 스타일 태그 내용 추출

    Args:
        content: 검색할 텍스트
        tag: 태그 이름 (예: "objective", "context")

    Returns:
        태그 내용 (없으면 빈 문자열)
    """
    pattern = f'<{tag}[^>]*>(.*?)</{tag}>'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        return match.group(1).strip()
    return ""


def parse_tasks(content: str) -> List[TaskModel]:
    """
    <tasks> 섹션 내 모든 <task> 파싱

    Args:
        content: PLAN.md 파일 내용

    Returns:
        TaskModel 객체 리스트
    """
    tasks = []

    # <tasks> 섹션 전체 추출
    tasks_section = parse_xml_section(content, 'tasks')
    if not tasks_section:
        return tasks

    # 각 <task> 태그 찾기
    task_pattern = r'<task\s+type="([^"]+)">(.*?)</task>'
    task_matches = re.finditer(task_pattern, tasks_section, re.DOTALL)

    for match in task_matches:
        task_type = match.group(1)
        task_content = match.group(2)

        # 각 task 내부 요소 파싱
        name = parse_xml_section(task_content, 'name')
        files_str = parse_xml_section(task_content, 'files')
        action = parse_xml_section(task_content, 'action')
        verify = parse_xml_section(task_content, 'verify')
        done = parse_xml_section(task_content, 'done')

        # files는 쉼표로 구분된 문자열을 리스트로 변환
        files = [f.strip() for f in files_str.split(',')] if files_str else []

        task = TaskModel(
            name=name,
            type=task_type,
            files=files,
            action=action,
            verify=verify if verify else None,
            done=done
        )
        tasks.append(task)

    return tasks
