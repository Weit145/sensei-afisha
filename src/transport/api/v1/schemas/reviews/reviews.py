import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from typing import Annotated


ReviewText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class CreateReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rating: int = Field(ge=1, le=5)
    text: ReviewText


class UpdateReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rating: int | None = Field(default=None, ge=1, le=5)
    text: ReviewText | None = None

    @model_validator(mode="after")
    def require_change(self) -> "UpdateReviewRequest":
        if self.rating is None and self.text is None:
            raise ValueError("Укажите оценку или текст")
        return self


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    afisha_id: uuid.UUID
    author_id: uuid.UUID | None
    rating: int
    text: str
    created_at: datetime
    updated_at: datetime


class ReviewStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    afisha_id: uuid.UUID
    rating_sum: int
    reviews_count: int
    avg_rating: float


class ReviewsPageResponse(BaseModel):
    stats: ReviewStatsResponse
    items: list[ReviewResponse]
    limit: int
    offset: int


class ReviewStatsBatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    afisha_ids: list[uuid.UUID] = Field(min_length=1, max_length=100)


class ReviewStatsBatchResponse(BaseModel):
    items: list[ReviewStatsResponse]
