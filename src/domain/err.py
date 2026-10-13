from dataclasses import dataclass
from enum import StrEnum


class ErrorCode(StrEnum):
    INVALID_DATA = "invalid_data"
    INTERNAL_ERROR = "internal_error"


@dataclass(slots=True)
class DomainError(Exception):
    code: ErrorCode
    message: str

    def __str__(self) -> str:
        return self.message


class InvalidDataError(DomainError):
    def __init__(self, message: str = "Invalid data") -> None:
        super().__init__(ErrorCode.INVALID_DATA, message)


class InternalError(DomainError):
    def __init__(self, message: str = "Internal error") -> None:
        super().__init__(ErrorCode.INTERNAL_ERROR, message)
