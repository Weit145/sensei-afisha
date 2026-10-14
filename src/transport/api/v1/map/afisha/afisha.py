from urllib.parse import quote

from src.domain.afisha import Afisha, AfishaStatus, AfishaUpdate
from src.transport.api.v1.schemas.afisha import (
    AfishaImageResponse,
    AfishaListResponse,
    AfishaStatus as ResponseAfishaStatus,
    CreateAfisha,
    ResponseAfisha,
    ResponseShortAfisha,
    UpdateAfisha,
    UploadedImageResponse,
)
from src.usecase.afisha.dto import (
    AfishaDetailResult,
    AfishaImageItem,
    AfishaListResult,
)


def map_to_domain(afisha: CreateAfisha) -> Afisha:
    return Afisha(
        title=afisha.title,
        description=afisha.description,
        short_description=afisha.short_description,
        starts_at=afisha.starts_at,
        ends_at=afisha.ends_at,
        venue_ids=list(afisha.venue_ids),
        age_limit=afisha.age_limit,
        status=AfishaStatus(afisha.status.value),
    )


def map_to_response(
    result: AfishaDetailResult,
) -> ResponseAfisha:
    afisha = result.afisha
    return ResponseAfisha(
        id=afisha.id,
        title=afisha.title,
        description=afisha.description,
        short_description=afisha.short_description,
        starts_at=afisha.starts_at,
        ends_at=afisha.ends_at,
        venue_ids=list(afisha.venue_ids),
        age_limit=afisha.age_limit,
        status=ResponseAfishaStatus(afisha.status.value),
        images=map_list_dto_to_response_img(result),
        reviews_id=result.reviews_id,
        average_id=result.average_id,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )

def map_list_dto_to_response_img(
    result: AfishaDetailResult,
) -> list[AfishaImageResponse]:
    images: list[AfishaImageResponse] = []
    for image in result.images:
        images.append(
            AfishaImageResponse(
                id=image.id,
                image_url=_image_url(image.file_name),
                is_cover=image.is_cover,
                position=image.position,
            )
        )
    return images


def map_to_update_domain(afisha: UpdateAfisha) -> AfishaUpdate:
    return AfishaUpdate(
        title=afisha.title,
        description=afisha.description,
        short_description=afisha.short_description,
        starts_at=afisha.starts_at,
        ends_at=afisha.ends_at,
        venue_ids=list(afisha.venue_ids) if afisha.venue_ids is not None else None,
        age_limit=afisha.age_limit,
        status=AfishaStatus(afisha.status.value) if afisha.status is not None else None,
    )


def map_to_list_response(
    result: AfishaListResult,
) -> AfishaListResponse:
    return AfishaListResponse(
        items=map_list_to_short_afish(result),
        page=result.page,
        page_size=result.page_size,
        total=result.total,
    )

def map_list_to_short_afish(
    result: AfishaListResult,
) -> list[ResponseShortAfisha]:
    items: list[ResponseShortAfisha] = []
    for item in result.items:
        items.append(
            ResponseShortAfisha(
                id=item.afisha.id,
                title=item.afisha.title,
                short_description=item.afisha.short_description,
                starts_at=item.afisha.starts_at,
                ends_at=item.afisha.ends_at,
                venue_names=list(item.venue_names),
                cover_url=(
                    _image_url(item.cover_file_name)
                    if item.cover_file_name is not None
                    else None
                ),
                age_limit=item.afisha.age_limit,
                status=ResponseAfishaStatus(item.afisha.status.value),
            )
        )
    return items


def _image_url(file_name: str) -> str:
    return f"/uploads/{quote(file_name, safe='')}"


def map_to_uploaded_image_response(image: AfishaImageItem) -> UploadedImageResponse:
    return UploadedImageResponse(
        id=image.id,
        image_url=_image_url(image.file_name),
    )
