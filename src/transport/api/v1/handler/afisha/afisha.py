import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Path,
    Query,
    UploadFile,
    status,
)
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.err import DomainError
from src.repositories.storage.postgres.db_helper import db_helper
from src.transport.api.v1.map.afisha import (
    map_afisha_to_domain as map_to_domain,
)
from src.transport.api.v1.map.afisha import (
    map_afisha_to_list_response as map_to_list_response,
)
from src.transport.api.v1.map.afisha import (
    map_afisha_to_response as map_to_response,
)
from src.transport.api.v1.map.afisha import (
    map_afisha_to_update_domain as map_to_update_domain,
)
from src.transport.api.v1.map.err import map_error_to_http_status_code
from src.transport.api.v1.middleware.user_check import CurrentUser, require_admin
from src.transport.api.v1.schemas.afisha import (
    AfishaListResponse,
    CreateAfisha,
    ResponseAfisha,
    UpdateAfisha,
)
from src.usecase.afisha.afisha_service import afisha_service

router = APIRouter(prefix="/afisha", tags=["Afisha"])

@router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    description="Создаёт афишу. Данные передаются JSON-строкой в поле afisha, изображения — файлами в поле images.",
)
async def create_afisha(
    images: Annotated[
        list[UploadFile],
        File(
            default_factory=list,
            json_schema_extra={"items": {"type": "string", "format": "binary"}},
        ),
    ],
    afisha: Annotated[
        str,
        Form(description="JSON с данными афиши (поля CreateAfisha)"),
    ],
    # _:Annotated[CurrentUser, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->ResponseAfisha:
    try:
        create_data = CreateAfisha.model_validate_json(afisha)
    except ValidationError as error:
        errors = error.errors(include_context=False)
        for item in errors:
            item["loc"] = ("body", "afisha", *item["loc"])
        raise RequestValidationError(errors) from error
    try:
        domain_afisha = map_to_domain(create_data)
        result = await afisha_service.create_afisha(domain_afisha, session, images)
    except DomainError as error:
        map_error_to_http_status_code(error)
    return map_to_response(result)

@router.put(
    path="/{afisha_id}",
    status_code=status.HTTP_200_OK,
    response_model=ResponseAfisha,
    description="Полностью обновляет данные афиши, не изменяя её изображения.",
)
async def update_afisha(
    afisha:CreateAfisha,
    # _:Annotated[CurrentUser, Depends(require_admin)],
    afisha_id: Annotated[uuid.UUID, Path(title="The ID afisha")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->ResponseAfisha:
    try:
        domain_afisha = map_to_domain(afisha)
        result = await afisha_service.update_afisha(domain_afisha, afisha_id, session)
    except DomainError as error:
        map_error_to_http_status_code(error)
    return map_to_response(result)

@router.patch(
    path="/{afisha_id}",
    status_code=status.HTTP_200_OK,
    response_model=ResponseAfisha,
    description="Частично обновляет указанные поля афиши.",
)
async def patch_afisha(
    afisha:UpdateAfisha,
    # _:Annotated[CurrentUser, Depends(require_admin)],
    afisha_id: Annotated[uuid.UUID, Path(title="The ID afisha")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->ResponseAfisha:
    try:
        domain_update_afisha = map_to_update_domain(afisha)
        result = await afisha_service.patch_afisha(domain_update_afisha, afisha_id, session)
    except DomainError as error:
        map_error_to_http_status_code(error)
    return map_to_response(result)

@router.delete(
    path="/{afisha_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Удаляет афишу и связанные с ней изображения.",
)
async def delete_afisha(
    # _:Annotated[CurrentUser, Depends(require_admin)],
    afisha_id: Annotated[uuid.UUID, Path(title="The ID afisha")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->None:
    try:
        await afisha_service.delete_afisha(afisha_id, session)
    except DomainError as error:
        map_error_to_http_status_code(error)


@router.get(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=AfishaListResponse,
    description="Возвращает список афиш с поиском и постраничной навигацией.",
)
async def list_afisha(
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: str | None = None,
)->AfishaListResponse:
    try:
        result = await afisha_service.list_afisha(session, page, page_size, search)
    except DomainError as error:
        map_error_to_http_status_code(error)
    return map_to_list_response(result)

@router.get(
    path="/{afisha_id}",
    status_code=status.HTTP_200_OK,
    response_model=ResponseAfisha,
    description="Возвращает подробные данные афиши и её изображения.",
)
async def read_afisha(
    afisha_id: Annotated[uuid.UUID, Path(title="The ID afisha")],
    session: Annotated[AsyncSession, Depends(db_helper.get_session)],
)->ResponseAfisha:
    try:
        result = await afisha_service.read_afisha(afisha_id, session)
    except DomainError as error:
        map_error_to_http_status_code(error)
    return map_to_response(result)
