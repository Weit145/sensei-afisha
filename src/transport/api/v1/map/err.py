from fastapi import HTTPException, status

from src.domain.err import InternalError, InvalidDataError


def map_error_to_http_status_code(error: Exception) -> None:
    if isinstance(error, InvalidDataError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    elif isinstance(error, InternalError):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
