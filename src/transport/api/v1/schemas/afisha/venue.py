import uuid

from pydantic import BaseModel, ConfigDict, Field


class Venue(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Название места проведения"
    )

    city: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Город"
    )

    address: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Адрес места проведения"
    )

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
        description="Географическая широта"
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
        description="Географическая долгота"
    )


class CreateVenue(Venue):
    pass


class UpdateVenue(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Название места проведения"
    )

    city: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Город"
    )

    address: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="Адрес места проведения"
    )

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
        description="Географическая широта"
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
        description="Географическая долгота"
    )


class ResponseVenue(Venue):
    id: uuid.UUID = Field(
        ...,
        description="Идентификатор площадки"
    )

    model_config = ConfigDict(from_attributes=True)

class VenueListResponse(BaseModel):
    items: list[ResponseVenue] = Field(
        ...,
        description="Список площадок"
    )

    page: int = Field(
        ...,
        ge=1,
        description="Номер страницы"
    )

    page_size: int = Field(
        ...,
        ge=1,
        le=100,
        description="Размер страницы"
    )

    total: int = Field(
        ...,
        ge=0,
        description="Общее количество площадок"
    )
