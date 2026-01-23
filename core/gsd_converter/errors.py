"""GSD Converter 커스텀 예외 정의"""

from typing import Optional


class GSDConverterError(Exception):
    """Base exception for GSD Converter"""
    pass


class ParseError(GSDConverterError):
    """PLAN.md 파싱 실패"""

    def __init__(self, message: str, line: Optional[int] = None, context: Optional[str] = None):
        self.line = line
        self.context = context
        super().__init__(self._format_message(message))

    def _format_message(self, message: str) -> str:
        parts = [message]
        if self.line:
            parts.append(f"Line: {self.line}")
        if self.context:
            parts.append(f"Context: {self.context}")
        return " | ".join(parts)


class ValidationError(GSDConverterError):
    """필수 필드 누락 또는 형식 오류"""

    def __init__(self, field: str, expected: str, actual: Optional[str] = None):
        self.field = field
        self.expected = expected
        self.actual = actual
        message = f"Validation failed for '{field}': expected {expected}"
        if actual:
            message += f", got {actual}"
        super().__init__(message)


class ConversionError(GSDConverterError):
    """변환 과정 오류"""
    pass
