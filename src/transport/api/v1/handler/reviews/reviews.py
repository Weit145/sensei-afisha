
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.err import DomainError
from src.repositories.storage.postgres.afisha_review_reader import (
    SqlAlchemyAfishaReviewReader,
)
from src.repositories.storage.postgres.db_helper import db_helper
from src.repositories.storage.postgres.reviews_repository import (
    AfishaReviewsRepository,
)
from src.transport.api.v1.map.err import map_error_to_http_status_code
from src.transport.api.v1.middleware.user_check import CurrentUserDep
from src.transport.api.v1.schemas.reviews.reviews import (
    CreateReviewRequest,
    ReviewResponse,
    ReviewsPageResponse,
    ReviewStatsBatchRequest,
    ReviewStatsBatchResponse,
    ReviewStatsResponse,
    UpdateReviewRequest,
)
from src.usecase.reviews.reviews_service import ReviewsService


router = APIRouter(tags=["Reviews"])
SessionDep = Annotated[AsyncSession, Depends(db_helper.get_session)]


def get_reviews_service(session: SessionDep) -> ReviewsService:
    return ReviewsService(
        repo=AfishaReviewsRepository(session),
        afisha_reader=SqlAlchemyAfishaReviewReader(session),
    )


ServiceDep = Annotated[ReviewsService, Depends(get_reviews_service)]


def _handle_integrity_error(exc: IntegrityError) -> None:
    original = getattr(exc.orig, "__cause__", None)
    constraint = getattr(original, "constraint_name", None) or getattr(
        exc.orig, "constraint_name", None
    )
    if constraint == "uq_reviews_author_afisha_reviews":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {
                "code": "review_already_exists",
                "message": "Вы уже оставили отзыв на эту афишу",
            }},
        ) from exc
    if constraint == "reviews_author_id_fkey":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {
                "code": "unauthorized",
                "message": "Пользователь из токена больше не существует",
            }},
        ) from exc
    raise exc


@router.post("/reviews/stats/batch", response_model=ReviewStatsBatchResponse)
async def get_stats_batch(
    data: ReviewStatsBatchRequest,
    service: ServiceDep,
) -> ReviewStatsBatchResponse:
    items = await service.get_stats_by_afisha_ids(data.afisha_ids)
    return ReviewStatsBatchResponse(
        items=[ReviewStatsResponse.model_validate(item) for item in items]
    )


@router.get(
    "/afisha/{afisha_id}/reviews",
    response_model=ReviewsPageResponse,
)
async def list_reviews(
    afisha_id: uuid.UUID,
    service: ServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ReviewsPageResponse:
    try:
        stats, reviews = await service.get_reviews_by_afisha_id(
            afisha_id, limit=limit, offset=offset
        )
    except DomainError as error:
        map_error_to_http_status_code(error)
    return ReviewsPageResponse(
        stats=ReviewStatsResponse.model_validate(stats),
        items=[ReviewResponse.model_validate(review) for review in reviews],
        limit=limit,
        offset=offset,
    )


@router.post(
    "/afisha/{afisha_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    afisha_id: uuid.UUID,
    data: CreateReviewRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
    service: ServiceDep,
) -> ReviewResponse:
    try:
        review = await service.create_review(
            afisha_id=afisha_id,
            author_id=current_user.user_id,
            rating=data.rating,
            text=data.text,
        )
        await session.commit()
    except DomainError as error:
        await session.rollback()
        map_error_to_http_status_code(error)
    except IntegrityError as exc:
        await session.rollback()
        _handle_integrity_error(exc)
    return ReviewResponse.model_validate(review)


@router.patch(
    "/afisha/{afisha_id}/reviews/{review_id}",
    response_model=ReviewResponse,
)
async def update_review(
    afisha_id: uuid.UUID,
    review_id: uuid.UUID,
    data: UpdateReviewRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
    service: ServiceDep,
) -> ReviewResponse:
    try:
        review = await service.update_review(
            afisha_id=afisha_id,
            review_id=review_id,
            author_id=current_user.user_id,
            rating=data.rating,
            text=data.text,
        )
        await session.commit()
    except DomainError as error:
        await session.rollback()
        map_error_to_http_status_code(error)
    return ReviewResponse.model_validate(review)


@router.delete(
    "/afisha/{afisha_id}/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_review(
    afisha_id: uuid.UUID,
    review_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
    service: ServiceDep,
) -> None:
    try:
        await service.delete_review(
            afisha_id=afisha_id,
            review_id=review_id,
            author_id=current_user.user_id,
        )
        await session.commit()
    except DomainError as error:
        await session.rollback()
        map_error_to_http_status_code(error)
