from typing import NoReturn

from fastapi import HTTPException, status

from src.domain.err import (
    InternalError,
    InvalidDataError,
    NotFoundError,
    UnauthorizedError,
)


def map_error_to_http_status_code(error: Exception) -> NoReturn:
    if isinstance(error, InvalidDataError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    elif isinstance(error, InternalError):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    elif isinstance(error, (NotFoundError, UnauthorizedError)):
        status_code = (
            status.HTTP_404_NOT_FOUND
            if isinstance(error, NotFoundError)
            else status.HTTP_401_UNAUTHORIZED
        )
        raise HTTPException(
            status_code=status_code,
            detail={"error": {"code": error.code.value, "message": error.message}},
            headers={"WWW-Authenticate": "Bearer"}
            if isinstance(error, UnauthorizedError)
            else None,
        ) from error
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
