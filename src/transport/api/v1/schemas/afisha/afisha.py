import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AfishaStatus(StrEnum):
    PUBLISHED = "published"
    CANCELLED = "cancelled"


class AfishaImageResponse(BaseModel):
    id: uuid.UUID
    image_url: str
    is_cover: bool
    position: int


class UploadedImageResponse(BaseModel):
    id: uuid.UUID
    image_url: str


class Afisha(BaseModel):
    title: str = Field( ...,description="Название афиши")
    short_description: str | None = Field(None,description="Короткое описание")
    description: str|None = Field(None,description="Полное описание")
    starts_at: datetime = Field(...,description="Начало мероприятия")
    ends_at: datetime = Field(...,description="Конец мероприятия")
    venue_ids: list[uuid.UUID] = Field(...,min_length=1,description="ID мест проведения")
    age_limit: int | None = Field(None,ge=0,le=18)
    status: AfishaStatus = Field(AfishaStatus.PUBLISHED,description="Статус мероприятия")

    @model_validator(mode="after")
    def validate_dates(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("Дата окончания должна быть позже даты начала")
        return self


class CreateAfisha(Afisha):
    pass


class UpdateAfisha(BaseModel):
    title: str | None = Field( None, description="Название афиши")
    short_description: str | None = Field(None,description="Короткое описание")
    description: str | None = Field(None,description="Полное описание")
    starts_at: datetime | None =  Field(None,description="Начало мероприятия")
    ends_at: datetime | None = Field(None,description="Конец мероприятия")
    venue_ids: list[uuid.UUID] | None = Field(None,min_length=1,description="ID мест проведения")
    age_limit: int | None =  Field(None,ge=0,le=18)
    status: AfishaStatus | None = Field(None,description="Статус мероприятия")


class ResponseAfisha(Afisha):
    id: uuid.UUID = Field( ..., description="Id афиши")
    images: list[AfishaImageResponse] = Field(default_factory=list, description="Изображения")
    rating_sum: int = Field( ..., description="Сумма рейтинга")
    reviews_count: int = Field( ..., description="Колличество рейтинга")
    followers_count: int = Field(..., description="Количество подписчиков")
    created_at: datetime = Field( ..., description="Дата начала")
    updated_at: datetime = Field( ..., description="Дата обновления")
    model_config = ConfigDict(from_attributes=True)


class ResponseShortAfisha(BaseModel):
    id: uuid.UUID = Field( ..., description="Id афиши")
    title: str = Field( ...,description="Название афиши")
    short_description: str | None = Field(None,description="Короткое описание")
    starts_at: datetime = Field(...,description="Начало мероприятия")
    ends_at: datetime = Field(...,description="Конец мероприятия")
    rating_sum: int = Field( ..., description="Сумма рейтинга")
    reviews_count: int = Field( ..., description="Колличество рейтинга")
    followers_count: int = Field(..., description="Количество подписчиков")
    venue_names: list[str] = Field(...,description="Адресса мероприятия")
    cover_url: str | None = Field(None,description="Ссылка на изображение")
    age_limit: int | None = Field(None,ge=0,le=18)
    status: AfishaStatus


class AfishaListResponse(BaseModel):
    items: list[ResponseShortAfisha] = Field(...,description="Мероприятия")
    page: int = Field(...,description="Номер страницы")
    page_size: int = Field(...,description="Размер страницы")
    total: int = Field(...,description="Количество записей")
