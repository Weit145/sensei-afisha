from dataclasses import dataclass

from src.domain.base import Entity


@dataclass(slots=True, kw_only=True)
class Venue(Entity):
    name: str
    city: str
    address: str

    latitude: float | None = None
    longitude: float | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Название площадки не может быть пустым")

        if not self.city.strip():
            raise ValueError("Город не может быть пустым")

        if not self.address.strip():
            raise ValueError("Адрес не может быть пустым")

        if self.latitude is not None and (not -90 <= self.latitude <= 90):
                raise ValueError("Некорректная широта")

        if self.longitude is not None and (not -180 <= self.longitude <= 180):
                raise ValueError("Некорректная долгота")

@dataclass(slots=True, kw_only=True)
class VenueUpdate(Entity):
    name: str | None = None
    city: str | None = None
    address: str | None = None

    latitude: float | None = None
    longitude: float | None = None

    def __post_init__(self) -> None:
        if self.latitude is not None and (not -90 <= self.latitude <= 90):
                raise ValueError("Некорректная широта")

        if self.longitude is not None and (not -180 <= self.longitude <= 180):
                raise ValueError("Некорректная долгота")
